import csv, io, json
from datetime import datetime
from django.contrib.auth import authenticate, get_user_model
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import *
from .serializers import *
from .services import *
User=get_user_model()

def _obj(model,pk): return model.objects.filter(id=pk).first()

@api_view(['POST'])
def register(request):
    phone=str(request.data.get('phone_number','')).strip(); username=request.data.get('username') or phone; password=request.data.get('password','')
    if not phone or not password:return Response({'error':'phone_number and password are required'},status=400)
    if User.objects.filter(phone_number=phone).exists():return Response({'error':'Phone number is already registered'},status=400)
    role=request.data.get('role','farmer'); role=role if role in dict(User.ROLE_CHOICES) else 'farmer'; lang=request.data.get('language','en')
    u=User.objects.create_user(username=username,password=password,phone_number=phone,role=role,language=lang); return Response(UserSerializer(u).data,status=201)

@api_view(['POST'])
def login(request):
    identifier=request.data.get('username') or request.data.get('phone_number'); password=request.data.get('password',''); u=User.objects.filter(phone_number=identifier).first() if identifier else None
    u=authenticate(username=u.username,password=password) if u else authenticate(username=identifier,password=password)
    if not u:return Response({'error':'Invalid login details'},status=401)
    return Response({'message':'Login successful','user':UserSerializer(u).data})

@api_view(['GET'])
def overview(request):
    uid=request.GET.get('user'); aq=Alert.objects.filter(is_read=False); aq=aq.filter(user_id=uid) if uid else aq
    return Response({'users':User.objects.count(),'markets':Market.objects.filter(active=True).count(),'commodities':Commodity.objects.filter(active=True).count(),'price_records':PriceRecord.objects.count(),'forecasts':Forecast.objects.count(),'recommendations':Recommendation.objects.count(),'alerts':aq.count(),'routes':TransportRoute.objects.filter(active=True).count(),'climate_records':ClimateRecord.objects.count(),'macro_records':MacroIndicator.objects.count()})

@api_view(['GET'])
def markets(request): return Response(MarketSerializer(Market.objects.filter(active=True),many=True).data)
@api_view(['GET'])
def commodities(request): return Response(CommoditySerializer(Commodity.objects.filter(active=True),many=True).data)
@api_view(['GET'])
def prices(request):
    qs=PriceRecord.objects.select_related('market','commodity').all()
    if request.GET.get('market'):qs=qs.filter(market_id=request.GET['market'])
    if request.GET.get('commodity'):qs=qs.filter(commodity_id=request.GET['commodity'])
    return Response(PriceRecordSerializer(qs[:500],many=True).data)

@api_view(['POST'])
def submit_price(request):
    try:
        market=Market.objects.get(id=request.data['market']); commodity=Commodity.objects.get(id=request.data['commodity']); price=validate_price(request.data.get('price'))
        previous=PriceRecord.objects.filter(market=market,commodity=commodity).order_by('-recorded_at').first(); user=User.objects.filter(id=request.data.get('submitted_by')).first()
        recorded_at=datetime.fromisoformat(request.data.get('recorded_at')) if request.data.get('recorded_at') else timezone.now(); recorded_at=timezone.make_aware(recorded_at) if timezone.is_naive(recorded_at) else recorded_at
        obj=PriceRecord.objects.create(market=market,commodity=commodity,price=price,volume=request.data.get('volume',0),recorded_at=recorded_at,source=request.data.get('source','manual'),source_reference=request.data.get('source_reference',''),submitted_by=user,validated=False)
        alerts=create_price_alert(obj,previous); return Response({'price':PriceRecordSerializer(obj).data,'alerts_created':len(alerts),'message':'Price submitted. It is awaiting validation.'},status=201)
    except Exception as e:return Response({'error':str(e)},status=400)

@api_view(['POST'])
def validate_prices(request):
    ids=request.data.get('ids',[]); ok=request.data.get('validated',True); note=request.data.get('note','Validated by administrator')
    count=PriceRecord.objects.filter(id__in=ids).update(validated=ok,validation_note=note); return Response({'updated':count})

@api_view(['POST'])
def import_prices(request):
    text=request.data.get('csv_text','')
    if not text:return Response({'error':'csv_text is required'},status=400)
    created=[]; errors=[]
    for i,row in enumerate(csv.DictReader(io.StringIO(text)),start=2):
        try:
            m=Market.objects.get(name__iexact=row['market'].strip()); c=Commodity.objects.get(name__iexact=row['commodity'].strip()); p=validate_price(row['price']); dt=datetime.fromisoformat(row['date']); dt=timezone.make_aware(dt) if timezone.is_naive(dt) else dt
            created.append(PriceRecord.objects.create(market=m,commodity=c,price=p,recorded_at=dt,volume=row.get('volume') or 0,source=row.get('source') or 'csv_import',validated=False))
        except Exception as e:errors.append({'row':i,'error':str(e)})
    return Response({'imported':len(created),'errors':errors})

@api_view(['GET','POST'])
def forecasts(request):
    if request.method=='POST':
        try:
            m=Market.objects.get(id=request.data['market']); c=Commodity.objects.get(id=request.data['commodity']); weeks=max(1,min(12,int(request.data.get('weeks',request.data.get('horizon_weeks',1))))); result=forecast_prices(m,c,weeks*7,True)
            return Response({'best_model':result['best_model'],'forecasts':ForecastSerializer(result['forecasts'],many=True).data,'scores':result['scores']})
        except Exception as e:return Response({'error':str(e)},status=400)
    qs=Forecast.objects.select_related('market','commodity').order_by('-forecast_date')
    if request.GET.get('market'):qs=qs.filter(market_id=request.GET['market'])
    if request.GET.get('commodity'):qs=qs.filter(commodity_id=request.GET['commodity'])
    return Response(ForecastSerializer(qs[:500],many=True).data)

@api_view(['GET'])
def model_scores(request):
    qs=ForecastModelScore.objects.all();
    if request.GET.get('market'):qs=qs.filter(market_id=request.GET['market'])
    if request.GET.get('commodity'):qs=qs.filter(commodity_id=request.GET['commodity'])
    return Response(ScoreSerializer(qs[:100],many=True).data)

@api_view(['POST'])
def recommendations(request):
    try:
        c=Commodity.objects.get(id=request.data.get('commodity')); qty=float(request.data.get('quantity',100)); recs=[]
        markets=list(Market.objects.filter(active=True)); latest={}
        for m in markets:
            p=PriceRecord.objects.filter(market=m,commodity=c).order_by('-recorded_at').first(); f=Forecast.objects.filter(market=m,commodity=c).order_by('-forecast_date').first(); latest[m.id]=float(f.predicted_price if f else p.price) if (f or p) else None
        for o in markets:
            for d in markets:
                if o.id==d.id or latest.get(o.id) is None or latest.get(d.id) is None:continue
                route=TransportRoute.objects.filter(origin=o,destination=d,active=True).first(); cost=route_cost(route) if route else 15; margin=latest[d.id]-latest[o.id]-cost
                if margin>0:recs.append(Recommendation.objects.create(commodity=c,origin=o,destination=d,quantity=qty,expected_margin=round(margin,2),confidence=round(min(.95,max(.5,.5+abs(margin)/(latest[d.id]+1)*.5)),2),rationale=f'Expected price spread is Le {latest[d.id]-latest[o.id]:.2f}; estimated movement cost is Le {cost:.2f}.'))
        return Response(RecommendationSerializer(recs, many=True).data)
    except Exception as e:return Response({'error':str(e)},status=400)

@api_view(['POST'])
def optimize(request):
    try:
        c=Commodity.objects.get(id=request.data['commodity']); plan=optimize_distribution(c,User.objects.filter(id=request.data.get('user')).first(),request.data.get('scenario','normal'),float(request.data.get('demand_multiplier',1)),float(request.data.get('fuel_price')) if request.data.get('fuel_price') else None)
        return Response({'plan':{'id':plan.id,'scenario':plan.scenario,'total_cost':plan.total_cost,'unmet_demand':plan.unmet_demand},'routes':[{'origin':x.origin.name,'destination':x.destination.name,'quantity':x.quantity,'unit_cost':x.unit_cost,'total_cost':x.total_cost,'blocked':x.blocked} for x in plan.routes.select_related('origin','destination')]})
    except Exception as e:return Response({'error':str(e)},status=400)

@api_view(['GET'])
def route_list(request):return Response(RouteSerializer(TransportRoute.objects.select_related('origin','destination'),many=True).data)
@api_view(['GET'])
def climate(request):return Response(ClimateSerializer(ClimateRecord.objects.select_related('market')[:200],many=True).data)
@api_view(['GET'])
def macro(request):return Response(MacroSerializer(MacroIndicator.objects.all()[:200],many=True).data)
@api_view(['GET'])
def supply_demand(request):return Response(SupplyDemandSerializer(SupplyDemandRecord.objects.select_related('market','commodity')[:200],many=True).data)

@api_view(['GET'])
def alerts(request):
    qs=Alert.objects.select_related('commodity','market','user').order_by('-created_at'); uid=request.GET.get('user')
    if uid:qs=qs.filter(user_id=uid)
    if request.GET.get('unread')=='1':qs=qs.filter(is_read=False)
    if request.GET.get('severity'):qs=qs.filter(severity=request.GET['severity'])
    return Response(AlertSerializer(qs[:200],many=True).data)
@api_view(['POST'])
def mark_alert_read(request,alert_id):
    a=Alert.objects.filter(id=alert_id).first();
    if not a:return Response({'error':'Alert not found'},status=404)
    a.is_read=True;a.sent=True;a.save(update_fields=['is_read','sent']);return Response(AlertSerializer(a).data)
@api_view(['POST'])
def mark_all_alerts_read(request):
    qs=Alert.objects.filter(user_id=request.data.get('user')) if request.data.get('user') else Alert.objects.all(); return Response({'marked_read':qs.filter(is_read=False).update(is_read=True,sent=True)})

@api_view(['GET','POST'])
def subscriptions(request):
    if request.method=='POST':
        s=AlertSubscription.objects.update_or_create(user_id=request.data['user'],commodity_id=request.data.get('commodity') or None,market_id=request.data.get('market') or None,channel=request.data.get('channel','dashboard'),defaults={'active':request.data.get('active',True)})[0]; return Response(SubscriptionSerializer(s).data,status=201)
    qs=AlertSubscription.objects.all();
    if request.GET.get('user'):qs=qs.filter(user_id=request.GET['user'])
    return Response(SubscriptionSerializer(qs,many=True).data)

@api_view(['GET'])
def report(request):
    commodity=_obj(Commodity,request.GET.get('commodity')); market=_obj(Market,request.GET.get('market')); fmt=request.GET.get('format','csv'); rows=list(PriceRecord.objects.select_related('market','commodity').order_by('recorded_at')[:1000]); rows=[r for r in rows if (not commodity or r.commodity_id==commodity.id) and (not market or r.market_id==market.id)]
    if fmt=='pdf':
        from reportlab.platypus import SimpleDocTemplate,Paragraph,Table,TableStyle,Spacer
        from reportlab.lib.pagesizes import A4; from reportlab.lib import colors; from reportlab.lib.styles import getSampleStyleSheet
        buf=io.BytesIO(); doc=SimpleDocTemplate(buf,pagesize=A4); st=getSampleStyleSheet(); elems=[Paragraph('Sierra Leone AgriMarket Intelligence Report',st['Title']),Paragraph(f'Generated: {timezone.now():%Y-%m-%d %H:%M}',st['Normal']),Spacer(1,12)]
        data=[['Date','Market','Commodity','Price','Validated']]+[[str(r.recorded_at.date()),r.market.name,r.commodity.name,f'Le {r.price:.2f}',str(r.validated)] for r in rows[:60]]; t=Table(data,repeatRows=1); t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.lightgrey),('GRID',(0,0),(-1,-1),.25,colors.grey),('FONTSIZE',(0,0),(-1,-1),7)])); elems.append(t); doc.build(elems); resp=HttpResponse(buf.getvalue(),content_type='application/pdf'); resp['Content-Disposition']='attachment; filename="agrimarket_report.pdf"'; return resp
    lines=['Date,Market,Commodity,Price,Unit,Validated']+[f'{r.recorded_at.date()},{r.market.name},{r.commodity.name},{r.price},{r.commodity.unit},{r.validated}' for r in rows]; return HttpResponse('\n'.join(lines),content_type='text/csv',headers={'Content-Disposition':'attachment; filename="agrimarket_report.csv"'})

@api_view(['POST'])
def ussd(request):
    text=(request.data.get('text') or '').strip(); parts=text.split('*') if text else []
    if not parts:return Response({'response':'CON AgriMarket\n1. Check Price\n2. Forecast\n3. Report Price\n4. Subscribe SMS\n5. Help'})
    menus={'1':('price','Select commodity\n1. Rice\n2. Cassava\n3. Maize\n4. Groundnuts\n5. Palm Oil'),'2':('forecast','Select commodity\n1. Rice\n2. Cassava\n3. Maize\n4. Groundnuts\n5. Palm Oil')}
    if parts[0] in menus and len(parts)==1:return Response({'response':'CON '+menus[parts[0]][1]})
    if parts[0] in menus and len(parts)==2:return Response({'response':'CON Select market\n1. Freetown\n2. Bo\n3. Makeni\n4. Kenema\n5. Port Loko'})
    if parts[0] in menus and len(parts)>=3:
        cn={1:'Rice',2:'Cassava',3:'Maize',4:'Groundnuts',5:'Palm Oil'}.get(int(parts[1]),''); mn={1:'Freetown',2:'Bo',3:'Makeni',4:'Kenema',5:'Port Loko'}.get(int(parts[2]),''); c=Commodity.objects.filter(name=cn).first(); m=Market.objects.filter(name=mn).first()
        if parts[0]=='1':p=PriceRecord.objects.filter(commodity=c,market=m).order_by('-recorded_at').first(); return Response({'response':f'END {cn} in {mn}: '+(f'Le {p.price:.2f}/{c.unit}' if p else 'No data')})
        f=Forecast.objects.filter(commodity=c,market=m).order_by('forecast_date').first(); return Response({'response':f'END Forecast: '+(f'Le {f.predicted_price:.2f}/{c.unit}' if f else 'No forecast available')})
    if parts[0]=='3':return Response({'response':'END Price reporting is available on the web data-entry form.'})
    if parts[0]=='4':return Response({'response':'END SMS subscription is managed from the dashboard. Send your phone number through the web profile.'})
    return Response({'response':'END Use 1 price, 2 forecast, 3 report, 4 SMS subscription.'})
