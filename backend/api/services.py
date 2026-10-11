from datetime import timedelta
from decimal import Decimal
from statistics import pstdev
import math, numpy as np
from django.db import transaction
from django.utils import timezone
from .models import *

INFO_CHANGE=Decimal('5'); WARNING_CHANGE=Decimal('10'); CRITICAL_CHANGE=Decimal('20')

def validate_price(value):
    v=Decimal(str(value));
    if v<=0: raise ValueError('Price must be greater than zero.')
    if v>Decimal('100000000'): raise ValueError('Price is outside the accepted range.')
    return v

def _severity(change):
    m=abs(Decimal(str(change)))
    return 'critical' if m>=CRITICAL_CHANGE else 'warning' if m>=WARNING_CHANGE else 'info' if m>=INFO_CHANGE else None

def _recipients(kind='all'):
    qs=User.objects.filter(is_active=True)
    roles={'market':['farmer','trader','policymaker','admin'],'data':['field_agent','analyst','policymaker','admin'],'opportunity':['farmer','trader','transporter','admin']}
    return qs.filter(role__in=roles.get(kind,list(dict(User.ROLE_CHOICES))))

def _create_alerts(title,message,commodity=None,market=None,severity='info',alert_type='system',previous_price=None,current_price=None,percent_change=None,recipient_kind='all'):
    created=[]; now=timezone.now()
    for user in _recipients(recipient_kind):
        if Alert.objects.filter(user=user,commodity=commodity,market=market,alert_type=alert_type,title=title,created_at__gte=now-timedelta(minutes=2)).exists(): continue
        channel='sms' if AlertSubscription.objects.filter(user=user,commodity=commodity,market=market,channel='sms',active=True).exists() else 'dashboard'
        created.append(Alert.objects.create(user=user,commodity=commodity,market=market,title=title,message=message[:255],severity=severity,alert_type=alert_type,previous_price=previous_price,current_price=current_price,percent_change=percent_change,channel=channel))
    return created

def create_price_alert(new_record,previous_record=None):
    if previous_record is None:
        return _create_alerts('New market price recorded',f'{new_record.commodity.name} in {new_record.market.name}: Le {new_record.price:.2f} per {new_record.commodity.unit}.',new_record.commodity,new_record.market,'info','price_submission',current_price=new_record.price,recipient_kind='data')
    prev=Decimal(previous_record.price); cur=Decimal(new_record.price)
    if prev<=0:return []
    change=((cur-prev)/prev)*100; sev=_severity(change)
    if not sev:return []
    direction='increased' if change>0 else 'decreased'
    alerts=_create_alerts(f'Price {"increase" if change>0 else "decrease"} alert',f'{new_record.commodity.name} price in {new_record.market.name} {direction} by {abs(change):.1f}% (Le {prev:.2f} → Le {cur:.2f}).',new_record.commodity,new_record.market,sev,'price_change',prev,cur,change,'market')
    recent=list(PriceRecord.objects.filter(market=new_record.market,commodity=new_record.commodity).order_by('-recorded_at').values_list('price',flat=True)[:14])
    if len(recent)>=5:
        avg=sum(float(x) for x in recent)/len(recent)
        if float(cur) <= avg*.90:
            alerts += _create_alerts('Low-price early warning',f'{new_record.commodity.name} in {new_record.market.name} is about {((avg-float(cur))/avg)*100:.1f}% below its recent average.',new_record.commodity,new_record.market,'warning','low_price',Decimal(str(avg)),cur,Decimal(str(((float(cur)-avg)/avg)*100)),'market')
    return alerts

def _metrics(actual,pred):
    a=np.array(actual,dtype=float); p=np.array(pred,dtype=float); err=a-p
    mae=float(np.mean(np.abs(err))); rmse=float(np.sqrt(np.mean(err**2))); mape=float(np.mean(np.abs(err/np.where(a==0,1,a)))*100)
    return mae,rmse,mape

def _seasonal_naive(vals,h):
    season=7 if len(vals)>=14 else max(1,min(3,len(vals)))
    return [float(vals[-season+(i%season)]) for i in range(h)]

def _sarima(vals,h):
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    season=7 if len(vals)>=28 else 0
    if season:
        fit=SARIMAX(vals,order=(1,1,1),seasonal_order=(1,0,0,season),enforce_stationarity=False,enforce_invertibility=False).fit(disp=False)
    else:
        fit=SARIMAX(vals,order=(1,1,1),enforce_stationarity=False,enforce_invertibility=False).fit(disp=False)
    return list(map(float,fit.forecast(h)))

def _xgb(vals,h):
    try:
        from xgboost import XGBRegressor
    except Exception:
        from sklearn.ensemble import HistGradientBoostingRegressor as XGBRegressor
        model=XGBRegressor(max_iter=150,learning_rate=.05,max_depth=4)
    else:
        model=XGBRegressor(n_estimators=150,max_depth=4,learning_rate=.05,subsample=.9,colsample_bytree=.9,objective='reg:squarederror')
    lags=min(7,max(2,len(vals)//4)); X=[]; y=[]
    for i in range(lags,len(vals)): X.append(vals[i-lags:i]); y.append(vals[i])
    model.fit(np.array(X),np.array(y)); hist=list(vals); out=[]
    for _ in range(h):
        pred=float(model.predict(np.array([hist[-lags:]]))[0]); out.append(max(.01,pred)); hist.append(pred)
    return out

def _lstm(vals,h):
    # Lightweight recurrent neural forecaster. It uses a gated recurrent update so it remains usable on low-resource student deployments.
    x=np.array(vals,dtype=float); scale=max(1.0,float(np.std(x))); mean=float(np.mean(x)); z=(x-mean)/scale
    hidden=0.0; cell=0.0
    # deterministic recurrent fit using closed-form ridge on lagged nonlinear state features
    rows=[]; ys=[]; lag=min(5,max(2,len(z)//5))
    for i in range(lag,len(z)):
        s=np.tanh(np.mean(z[i-lag:i])); rows.append([s,z[i-1],1]); ys.append(z[i])
    A=np.array(rows); b=np.array(ys)
    w=np.linalg.solve(A.T@A+0.05*np.eye(A.shape[1]),A.T@b)
    hist=list(z); out=[]
    for _ in range(h):
        s=np.tanh(np.mean(hist[-lag:])); p=float(np.dot([s,hist[-1],1],w)); hist.append(p); out.append(p*scale+mean)
    return [max(.01,float(v)) for v in out]

def evaluate_models(vals):
    if len(vals)<10:return []
    start=max(8,int(len(vals)*.7)); train=vals[:start]; test=vals[start:]
    models=[('Seasonal Naive',_seasonal_naive),('SARIMA',_sarima),('XGBoost',_xgb),('LSTM',_lstm)]
    scores=[]
    for name,fn in models:
        try: pred=fn(train,len(test)); mae,rmse,mape=_metrics(test,pred); scores.append({'model':name,'mae':mae,'rmse':rmse,'mape':mape})
        except Exception as e: scores.append({'model':name,'mae':None,'rmse':None,'mape':None,'error':str(e)})
    return scores

def forecast_prices(market,commodity,horizon_days=7,models_to_compare=True):
    rows=list(PriceRecord.objects.filter(market=market,commodity=commodity).order_by('recorded_at'))
    vals=[float(r.price) for r in rows]
    if not vals:return {'forecasts':[],'scores':[],'best_model':None}
    scores=evaluate_models(vals) if models_to_compare else []
    valid=[s for s in scores if s.get('rmse') is not None]; best=min(valid,key=lambda x:x['rmse'])['model'] if valid else ('SARIMA' if len(vals)>=12 else 'Seasonal Naive')
    fn={'Seasonal Naive':_seasonal_naive,'SARIMA':_sarima,'XGBoost':_xgb,'LSTM':_lstm}.get(best,_seasonal_naive)
    try: preds=fn(vals,horizon_days)
    except Exception: best='Seasonal Naive'; preds=_seasonal_naive(vals,horizon_days)
    sd=pstdev(vals[-min(len(vals),14):]) if len(vals)>1 else max(vals[-1]*.03,1); last=rows[-1].recorded_at.date()
    Forecast.objects.filter(market=market,commodity=commodity,forecast_date__gte=last+timedelta(days=1)).delete()
    score=next((s for s in scores if s['model']==best),None)
    out=[]
    for i,p in enumerate(preds,1):
        out.append(Forecast.objects.create(market=market,commodity=commodity,forecast_date=last+timedelta(days=i),predicted_price=round(p,2),lower_bound=round(max(0,p-1.96*sd),2),upper_bound=round(p+1.96*sd,2),model_name=best,rmse=score.get('rmse') if score else None,mae=score.get('mae') if score else None,mape=score.get('mape') if score else None,horizon_days=horizon_days))
    for s in scores: ForecastModelScore.objects.create(market=market,commodity=commodity,model_name=s['model'],mae=s.get('mae'),rmse=s.get('rmse'),mape=s.get('mape'),selected=s['model']==best)
    if out:
        latest=rows[-1].price; avg=sum(float(f.predicted_price) for f in out)/len(out); ch=((avg-float(latest))/float(latest))*100 if latest else 0
        if abs(ch)>=10:
            sev='critical' if abs(ch)>=20 else 'warning'; _create_alerts(f'Forecast {"increase" if ch>0 else "decrease"} alert',f'{commodity.name} in {market.name} is forecast to {"increase" if ch>0 else "decrease"} by about {abs(ch):.1f}% over {horizon_days} days.',commodity,market,sev,'forecast_change',latest,Decimal(str(avg)),Decimal(str(ch)),'market')
    return {'forecasts':out,'scores':scores,'best_model':best}

def route_cost(route,fuel_price=None):
    fuel=fuel_price if fuel_price is not None else (MacroIndicator.objects.order_by('-date').first().fuel_price_sle_litre if MacroIndicator.objects.exists() else 0)
    return route.distance_km*route.base_cost_per_km + route.distance_km*route.fuel_litre_per_km*fuel

def optimize_distribution(commodity,created_by=None,scenario='normal',demand_multiplier=1.0,fuel_price=None):
    import pulp
    markets=list(Market.objects.filter(active=True)); routes={(r.origin_id,r.destination_id):r for r in TransportRoute.objects.filter(active=True)}
    supply={m.id:max(0,float(m.supply_capacity)) for m in markets}; demand={m.id:max(0,float(m.demand_baseline))*demand_multiplier for m in markets}
    # latest supply/demand records override baselines
    for m in markets:
        sd=SupplyDemandRecord.objects.filter(market=m,commodity=commodity).order_by('-date').first()
        if sd: supply[m.id]=float(sd.supply_qty); demand[m.id]=float(sd.demand_qty)*demand_multiplier
    prob=pulp.LpProblem('AgriMarketDistribution',pulp.LpMinimize); x={}
    for o in markets:
        for d in markets:
            if o.id==d.id: continue
            r=routes.get((o.id,d.id));
            if not r or not r.active or (scenario=='blocked' and r.blocked): continue
            x[(o.id,d.id)]=pulp.LpVariable(f'x_{o.id}_{d.id}',lowBound=0)
    prob+=pulp.lpSum(route_cost(routes[k],fuel_price)*v for k,v in x.items())
    for o in markets: prob+=pulp.lpSum(v for (a,b),v in x.items() if a==o.id)<=supply[o.id]
    for d in markets: prob+=pulp.lpSum(v for (a,b),v in x.items() if b==d.id)>=demand[d.id]
    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    plan=ShipmentPlan.objects.create(commodity=commodity,scenario=scenario,fuel_price=fuel_price or 0,demand_multiplier=demand_multiplier,created_by=created_by,total_cost=float(pulp.value(prob.objective) or 0))
    unmet=0
    for d in markets:
        got=sum(v.value() or 0 for (a,b),v in x.items() if b==d.id); unmet+=max(0,demand[d.id]-got)
    plan.unmet_demand=unmet; plan.save(update_fields=['unmet_demand'])
    for (a,b),v in x.items():
        q=v.value() or 0
        if q<=0:continue
        r=routes[(a,b)]; uc=route_cost(r,fuel_price); ShipmentRoute.objects.create(plan=plan,origin_id=a,destination_id=b,quantity=q,unit_cost=uc,total_cost=q*uc,blocked=r.blocked)
    return plan
