import React,{useEffect,useMemo,useState} from 'react';
import {createRoot} from 'react-dom/client';
import {LineChart,Line,BarChart,Bar,XAxis,YAxis,Tooltip,CartesianGrid,ResponsiveContainer,Legend} from 'recharts';
import './style.css';
const API=import.meta.env.VITE_API_URL||(import.meta.env.PROD?'/api':'http://127.0.0.1:8000/api');
async function api(path,options={}){const r=await fetch(API+path,options);const d=await r.json().catch(()=>({}));if(!r.ok)throw new Error(d.error||'Request failed');return d}
const fmt=v=>v==null||v===''?'—':`Le ${Number(v).toLocaleString('en-SL',{minimumFractionDigits:2,maximumFractionDigits:2})}`;
const ROLES={farmer:'Farmer',trader:'Trader',transporter:'Transporter',field_agent:'Field Agent',policymaker:'Policy Maker',analyst:'Analyst',admin:'Administrator'};
const NAV={farmer:['Dashboard','Prices','Forecasting','Supply Chain','Alerts','USSD/SMS'],trader:['Dashboard','Prices','Forecasting','Supply Chain','Alerts','USSD/SMS'],transporter:['Dashboard','Supply Chain','Prices','Alerts','USSD/SMS'],field_agent:['Dashboard','Prices','Data Validation','Alerts','USSD/SMS'],policymaker:['Dashboard','Prices','Forecasting','Supply Chain','Reports','Climate & Economy','Alerts','USSD/SMS'],analyst:['Dashboard','Prices','Forecasting','Supply Chain','Reports','Climate & Economy','Data Validation','Alerts','USSD/SMS'],admin:['Dashboard','Prices','Forecasting','Supply Chain','Reports','Climate & Economy','Data Validation','Alerts','USSD/SMS','Administration']};
  const [identifier, setIdentifier] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState('farmer');
  const [err, setErr] = useState('');
  const [msg, setMsg] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async e => {
    e.preventDefault();
    setErr('');
    setMsg('');

    if (mode === 'register' && password !== confirmPassword) {
      setErr('Passwords do not match.');
      return;
    }

    setBusy(true);

    try {
      if (mode === 'login') {
        const d = await api('/auth/login/', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
          username: identifier,
          password,
          role
        })

        });

        onLogin(d.user);
      } else {
        const d = await api('/auth/register/', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
          username: identifier,
          phone_number: phone,
          password,
          role
        })
        });

        setMsg(d.message || 'Account created successfully. You can now sign in.');
        setMode('login');
        setPassword('');
        setConfirmPassword('');
      }
    } catch (e) {
      setErr(e.message || 'Something went wrong. Please try again.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-brand">
        <div className="logo-mark">🌾</div>
        <div>
          <div className="brand-name">AgriMarket</div>
          <div>Sierra Leone Intelligence Platform</div>
        </div>
      </div>

      <div className="login-card">
        <div className="eyebrow">SECURE ACCESS</div>

        <h1>{mode === 'login' ? 'Welcome back' : 'Create your account'}</h1>

        <p>
          Access market prices, forecasts, supply-chain information and alerts.
        </p>

        <form onSubmit={submit}>
          <label>
            Username
            <input
              value={identifier}
              onChange={e => setIdentifier(e.target.value)}
              autoComplete="username"
              required
            />
          </label>

          {mode === 'register' && (
            <>
              <label>
                Phone number
                <input
                  type="tel"
                  value={phone}
                  onChange={e => setPhone(e.target.value)}
                  placeholder="Enter your phone number"
                  autoComplete="tel"
                  required
                />
              </label>

              <label>
                Account type
                <select value={role} onChange={e => setRole(e.target.value)}>
                  <option value="farmer">Farmer</option>
                  <option value="trader">Trader</option>
                  <option value="transporter">Transporter</option>
                </select>
              </label>
            </>
          )}

          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              required
            />
          </label>

          {mode === 'register' && (
            <label>
              Confirm password
              <input
                type="password"
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                autoComplete="new-password"
                required
              />
            </label>
          )}

          {err && <div className="error">{err}</div>}
          {msg && <div className="success">{msg}</div>}

          <button className="primary wide" type="submit" disabled={busy}>
            {busy
              ? 'Please wait…'
              : mode === 'login'
                ? 'Sign in'
                : 'Create account'}
          </button>
        </form>

        <div style={{textAlign: 'center', marginTop: 18, fontSize: 12}}>
          {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}

          <button
            type="button"
            className="text-btn"
            onClick={() => {
              setMode(mode === 'login' ? 'register' : 'login');
              setErr('');
              setMsg('');
            }}
          >
            {mode === 'login' ? 'Create an account' : 'Sign in'}
          </button>
        </div>

        {mode === 'login' && (
          <div className="demo-box">
            <b>Demo administrator</b>
            <br />
            admin / admin123
          </div>
        )}
      </div>
    </div>
  );

function App(){const [user,setUser]=useState(null);if(!user)return <Login onLogin={setUser}/>;return <Main user={user} logout={()=>setUser(null)}/>}
function Main({user,logout}){const nav=NAV[user.role]||NAV.farmer;const [tab,setTab]=useState('Dashboard'),[markets,setMarkets]=useState([]),[commodities,setCommodities]=useState([]),[prices,setPrices]=useState([]),[forecasts,setForecasts]=useState([]),[alerts,setAlerts]=useState([]),[overview,setOverview]=useState({}),[selected,setSelected]=useState({market:'',commodity:''});const [busy,setBusy]=useState(false);const refresh=async()=>{const [m,c,o,p,a,f]=await Promise.all([api('/markets/'),api('/commodities/'),api(`/overview/?user=${user.id}`),api('/prices/'),api(`/alerts/?user=${user.id}`),api('/forecasts/')]);setMarkets(m);setCommodities(c);setOverview(o);setPrices(p);setAlerts(a);setForecasts(f)};useEffect(()=>{refresh().catch(console.error)},[]);useEffect(()=>{if(!selected.market&&markets[0])setSelected(s=>({...s,market:markets[0].id}));if(!selected.commodity&&commodities[0])setSelected(s=>({...s,commodity:commodities[0].id}))},[markets,commodities]);const generate=async weeks=>{if(!selected.market||!selected.commodity)return;setBusy(true);try{const d=await api('/forecasts/',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({market:selected.market,commodity:selected.commodity,weeks:weeks||1})});setForecasts(d.forecasts);alert(`Best model: ${d.best_model}. Models compared: ${d.scores.length}.`);refresh()}catch(e){alert(e.message)}finally{setBusy(false)}};const current=prices.find(p=>String(p.market)===String(selected.market)&&String(p.commodity)===String(selected.commodity));const prev=prices.filter(p=>String(p.market)===String(selected.market)&&String(p.commodity)===String(selected.commodity)&&p.id!==current?.id)[1]||prices.find(p=>String(p.market)===String(selected.market)&&String(p.commodity)===String(selected.commodity));const navClick=x=>setTab(x);return <div className="shell"><aside className="sidebar"><div className="sidebar-brand"><span>🌾</span><div><b>AGRI-MARKET</b><small>INTELLIGENCE</small></div></div><div className="role-badge">{ROLES[user.role]}</div><nav>{nav.map(x=><button className={tab===x?'nav-item active':'nav-item'} key={x} onClick={()=>navClick(x)}>{x}</button>)}</nav><button className="logout" onClick={logout}>Log out</button></aside><main className="content"><header className="topbar"><div><div className="breadcrumb">SIERRA LEONE · MARKET INTELLIGENCE</div><h1>{tab}</h1></div><div className="top-actions"><span className="live-pill">● LIVE DATA</span><div className="profile"><div><b>{user.username}</b><small>{ROLES[user.role]}</small></div><div className="avatar">{user.username?.[0]?.toUpperCase()}</div></div></div></header>{tab==='Dashboard'&&<Dashboard {...{markets,commodities,selected,setSelected,overview,prices,forecasts,alerts,current,prev,generate,busy,setTab}}/>}{tab==='Prices'&&<Prices {...{markets,commodities,selected,setSelected,prices,user,refresh}}/>}{tab==='Forecasting'&&<Forecasting {...{markets,commodities,selected,setSelected,forecasts,prices,generate,busy}}/>}{tab==='Supply Chain'&&<SupplyChain {...{markets,commodities,user}}/>}{tab==='Data Validation'&&<Validation {...{prices,refresh}}/>}{tab==='Reports'&&<Reports {...{markets,commodities,selected,setSelected}}/>}{tab==='Climate & Economy'&&<ClimateEconomy/>}{tab==='Alerts'&&<Alerts {...{alerts,user,refresh}}/>}{tab==='USSD/SMS'&&<USSD user={user}/>} {tab==='Administration'&&<Administration/>}</main></div>}
function Filters({markets,commodities,selected,setSelected,children}){return <div className="toolbar"><label>Commodity<select value={selected.commodity} onChange={e=>setSelected({...selected,commodity:e.target.value})}>{commodities.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></label><label>Market<select value={selected.market} onChange={e=>setSelected({...selected,market:e.target.value})}>{markets.map(m=><option key={m.id} value={m.id}>{m.name}</option>)}</select></label>{children}</div>}
function Dashboard(p){const trend=[...p.prices.filter(x=>String(x.market)===String(p.selected.market)&&String(x.commodity)===String(p.selected.commodity)).slice(0,30).reverse().map(x=>({date:x.recorded_at?.slice(5,10),actual:+x.price})),...p.forecasts.filter(x=>String(x.market)===String(p.selected.market)&&String(x.commodity)===String(p.selected.commodity)).slice(0,14).map(x=>({date:x.forecast_date?.slice(5,10),forecast:+x.predicted_price}))];return <div className="page"><div className="welcome"><div><div className="eyebrow">AGRIC-MARKET INTELLIGENCE</div><h2>WELLCOME</h2><p>Price intelligence, AI forecasting, route optimization and early-warning alerts for Sierra Leone.</p></div><button className="primary" onClick={()=>p.setTab('Prices')}>+ Submit market price</button></div><Filters {...p}><button className="primary" onClick={()=>p.generate(1)} disabled={p.busy}>Generate 1-week forecast</button></Filters><div className="stat-grid">{[['Markets',p.overview.markets,'Active markets'],['Commodities',p.overview.commodities,'Staple goods'],['Price records',p.overview.price_records,'Observations'],['Forecasts',p.overview.forecasts,'Predictions'],['Alerts',p.overview.alerts,'Unread signals']].map((x,i)=><div className="stat-card" key={x[0]}><span>{x[0]}</span><strong>{x[1]??'—'}</strong><small>{x[2]}</small></div>)}</div><div className="two-col"><section className="panel"><div className="panel-head"><div><h3>Price trend & forecast</h3><p>Actual market observations and predicted values</p></div></div><ResponsiveContainer width="100%" height={320}><LineChart data={trend}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="date"/><YAxis/><Tooltip/><Legend/><Line dataKey="actual" name="Actual" strokeWidth={2.5} dot={false}/><Line dataKey="forecast" name="Forecast" strokeWidth={2.5} strokeDasharray="6 5" dot={false}/></LineChart></ResponsiveContainer></section><section className="panel current-card"><h3>Current price</h3><p>{p.current?.commodity_name} · {p.current?.market_name}</p><div className="big-price">{fmt(p.current?.price)} <span>/ {p.current?.unit||'kg'}</span></div><div className="price-compare"><span>Previous</span><b>{fmt(p.prev?.price)}</b></div><div className="mini-note">Prices use Sierra Leone Leone (Le). Alerts are generated automatically when configured thresholds are reached.</div></section></div><div className="two-col"><section className="panel"><div className="panel-head"><h3>Latest forecasts</h3><button className="text-btn" onClick={()=>p.setTab('Forecasting')}>Model comparison →</button></div>{p.forecasts.slice(0,6).map(f=><div className="forecast-row" key={f.id}><span>{f.forecast_date}</span><b>{fmt(f.predicted_price)}</b><small>{f.model_name}</small></div>)}</section><section className="panel"><h3>Early-warning alerts</h3>{p.alerts.slice(0,4).map(a=><AlertRow key={a.id} alert={a}/>)}{!p.alerts.length&&<div className="empty small">No important notices yet.</div>}</section></div></div>}
function Prices({markets,commodities,selected,setSelected,prices,user,refresh}){const [price,setPrice]=useState(''),[market,setMarket]=useState(selected.market),[commodity,setCommodity]=useState(selected.commodity),[msg,setMsg]=useState('');useEffect(()=>{setMarket(selected.market);setCommodity(selected.commodity)},[selected]);const submit=async e=>{e.preventDefault();try{const d=await api('/prices/submit/',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({market,commodity,price,submitted_by:user.id})});setMsg(d.message);setPrice('');refresh()}catch(e){setMsg(e.message)}};const rows=prices.filter(p=>!selected.market||String(p.market)===String(selected.market)).slice(0,80);return <div className="page"><Filters {...{markets,commodities,selected,setSelected}}/><section className="panel"><h3>Submit / collect price</h3><form className="report-form" onSubmit={submit}><label>Market<select value={market} onChange={e=>setMarket(e.target.value)}>{markets.map(m=><option key={m.id} value={m.id}>{m.name}</option>)}</select></label><label>Commodity<select value={commodity} onChange={e=>setCommodity(e.target.value)}>{commodities.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></label><label>Price<input type="number" step="0.01" value={price} onChange={e=>setPrice(e.target.value)} required/></label><button className="primary">Submit for validation</button></form>{msg&&<div className="success">{msg}</div>}</section><section className="panel"><div className="panel-head"><div><h3>Historical market prices</h3><p>Data can be imported, validated and analysed.</p></div></div><div className="data-table"><div className="thead"><span>Date</span><span>Commodity</span><span>Market</span><span>Price</span></div>{rows.map(r=><div className="tr" key={r.id}><span>{r.recorded_at?.slice(0,10)}</span><span>{r.commodity_name}</span><span>{r.market_name}</span><b>{fmt(r.price)}</b></div>)}</div></section></div>}
function Forecasting({markets,commodities,selected,setSelected,forecasts,prices,generate,busy}){const [weeks,setWeeks]=useState(4),[scores,setScores]=useState([]);const compare=async()=>{await generate(weeks);try{const d=await api(`/forecast-scores/?market=${selected.market}&commodity=${selected.commodity}`);setScores(d)}catch{}};const chart=[...prices.filter(x=>String(x.market)===String(selected.market)&&String(x.commodity)===String(selected.commodity)).slice(0,30).reverse().map(x=>({date:x.recorded_at?.slice(5,10),actual:+x.price})),...forecasts.filter(x=>String(x.market)===String(selected.market)&&String(x.commodity)===String(selected.commodity)).slice(0,84).map(x=>({date:x.forecast_date?.slice(5,10),forecast:+x.predicted_price}))];return <div className="page"><section className="hero-panel"><div><div className="eyebrow">AI FORECASTING</div><h2>1–12 week price forecasting</h2><p>Compare Seasonal Naive, SARIMA, XGBoost and a lightweight LSTM-style recurrent model using walk-forward evaluation.</p></div></section><Filters {...{markets,commodities,selected,setSelected}}><select className="week-select" value={weeks} onChange={e=>setWeeks(+e.target.value)}>{[1,2,4,8,12].map(w=><option key={w} value={w}>{w} week{w>1?'s':''}</option>)}</select><button className="primary" onClick={compare} disabled={busy}>{busy?'Training…':'Compare & Forecast'}</button></Filters><section className="panel"><ResponsiveContainer width="100%" height={360}><LineChart data={chart}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="date"/><YAxis/><Tooltip/><Legend/><Line dataKey="actual" name="Actual" strokeWidth={2.5} dot={false}/><Line dataKey="forecast" name="Best forecast" strokeWidth={2.5} strokeDasharray="6 5" dot={false}/></LineChart></ResponsiveContainer></section><section className="panel"><h3>Model comparison</h3><div className="model-grid">{scores.length?scores.map(s=><div className="model-card" key={s.id||s.model_name}><b>{s.model_name}</b><span>MAE: {s.mae?.toFixed?.(2)||'—'}</span><span>RMSE: {s.rmse?.toFixed?.(2)||'—'}</span><span>MAPE: {s.mape?.toFixed?.(2)||'—'}%</span>{s.selected&&<em>BEST MODEL</em>}</div>):<div className="empty small">Run a comparison to evaluate the models.</div>}</div></section><section className="panel"><h3>Forecast results</h3>{forecasts.filter(x=>String(x.market)===String(selected.market)&&String(x.commodity)===String(selected.commodity)).slice(0,84).map(f=><div className="forecast-row" key={f.id}><span>{f.forecast_date}</span><b>{fmt(f.predicted_price)}</b><small>{f.model_name} · {fmt(f.lower_bound)}–{fmt(f.upper_bound)}</small></div>)}</section></div>}
function SupplyChain({markets,commodities,user}){const [commodity,setCommodity]=useState(commodities[0]?.id||''),[scenario,setScenario]=useState('normal'),[result,setResult]=useState(null),[busy,setBusy]=useState(false);useEffect(()=>{if(!commodity&&commodities[0])setCommodity(commodities[0].id)},[commodities]);const run=async()=>{setBusy(true);try{setResult(await api('/optimize/',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({commodity,scenario,user:user.id,demand_multiplier:scenario==='demand_shock'?1.25:1})}))}catch(e){alert(e.message)}finally{setBusy(false)}};return <div className="page"><section className="hero-panel"><div><div className="eyebrow">SUPPLY CHAIN OPTIMIZATION</div><h2>Find lower-cost distribution plans</h2><p>The transportation model uses supply, demand, distance, fuel cost and route availability. Try a blocked-road or demand-shock scenario.</p></div></section><section className="panel"><div className="toolbar"><label>Commodity<select value={commodity} onChange={e=>setCommodity(e.target.value)}>{commodities.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></label><label>Scenario<select value={scenario} onChange={e=>setScenario(e.target.value)}><option value="normal">Normal</option><option value="blocked">Blocked road</option><option value="demand_shock">Demand shock +25%</option></select></label><button className="primary" onClick={run}>{busy?'Optimizing…':'Run optimization'}</button></div>{result&&<><div className="stat-grid"><div className="stat-card"><span>Total transport cost</span><strong>{fmt(result.plan.total_cost)}</strong></div><div className="stat-card"><span>Unmet demand</span><strong>{result.plan.unmet_demand.toFixed(1)}</strong></div><div className="stat-card"><span>Scenario</span><strong>{result.plan.scenario}</strong></div></div><div className="data-table"><div className="thead"><span>Origin</span><span>Destination</span><span>Quantity</span><span>Total cost</span></div>{result.routes.map((r,i)=><div className="tr" key={i}><span>{r.origin}</span><span>{r.destination}</span><span>{r.quantity.toFixed(1)}</span><b>{fmt(r.total_cost)}</b></div>)}</div></>}</section></div>}
function Validation({prices,refresh}){const [ids,setIds]=useState([]),[msg,setMsg]=useState('');const toggle=id=>setIds(x=>x.includes(id)?x.filter(v=>v!==id):[...x,id]);const validate=async()=>{const d=await api('/prices/validate/',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ids,validated:true,note:'Validated by field agent/analyst'})});setMsg(`${d.updated} record(s) validated.`);setIds([]);refresh()};return <div className="page"><section className="hero-panel"><div><div className="eyebrow">DATA QUALITY</div><h2>Validate submitted market prices</h2><p>Review incoming observations before they are trusted by forecasting and reporting.</p></div><button className="primary" onClick={validate} disabled={!ids.length}>Validate selected</button></section><section className="panel">{msg&&<div className="success">{msg}</div>}<div className="data-table"><div className="thead"><span>Select</span><span>Commodity</span><span>Market</span><span>Status</span></div>{prices.filter(p=>!p.validated).slice(0,80).map(r=><div className="tr" key={r.id}><span><input type="checkbox" checked={ids.includes(r.id)} onChange={()=>toggle(r.id)}/></span><span>{r.commodity_name}</span><span>{r.market_name}</span><b>{r.validated?'Validated':'Pending'}</b></div>)}</div></section></div>}
function Reports({markets,commodities,selected,setSelected}){const download=fmt=>window.open(`${API}/reports/?format=${fmt}${selected.market?`&market=${selected.market}`:''}${selected.commodity?`&commodity=${selected.commodity}`:''}`,'_blank');return <div className="page"><section className="hero-panel"><div><div className="eyebrow">REPORTING</div><h2>Market, forecast and distribution reports</h2><p>Export evidence for policymakers, analysts and project evaluation.</p></div></section><Filters {...{markets,commodities,selected,setSelected}}/><section className="panel"><div className="report-buttons"><button className="primary" onClick={()=>download('csv')}>Export CSV</button><button className="secondary" onClick={()=>download('pdf')}>Export PDF</button></div><div className="info-box"><b>Report coverage</b><p>Price history, validation status, selected market/commodity filters and forecast/optimization outputs can be included in project reporting.</p></div></section></div>}
function ClimateEconomy(){const [climate,setClimate]=useState([]),[macro,setMacro]=useState([]);useEffect(()=>{Promise.all([api('/climate/'),api('/macro/')]).then(([c,m])=>{setClimate(c);setMacro(m)})},[]);return <div className="page"><div className="two-col"><section className="panel"><h3>Climate indicators</h3>{climate.slice(0,15).map(x=><div className="forecast-row" key={x.id}><span>{x.date}</span><b>{x.rainfall_mm.toFixed(1)} mm</b><small>{x.temperature_c.toFixed(1)}°C · {x.market_name}</small></div>)}</section><section className="panel"><h3>Macroeconomic indicators</h3>{macro.slice(0,15).map(x=><div className="forecast-row" key={x.id}><span>{x.date}</span><b>Fuel Le {x.fuel_price_sle_litre.toFixed(2)}</b><small>FX {x.exchange_rate_sle_usd.toFixed(0)} · Inflation {x.inflation_pct.toFixed(2)}%</small></div>)}</section></div></div>}
function Alerts({alerts,user,refresh}){const [filter,setFilter]=useState('all');const rows=alerts.filter(a=>filter==='all'||a.severity===filter);const read=async id=>{await api(`/alerts/${id}/read/`,{method:'POST'});refresh()};const all=async()=>{await api('/alerts/read-all/',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user:user.id})});refresh()};return <div className="page"><section className="hero-panel"><div><div className="eyebrow">EARLY WARNING</div><h2>Market alerts</h2><p>Price spikes, forecast movements, opportunities and low-price signals.</p></div><div className="alert-actions"><select value={filter} onChange={e=>setFilter(e.target.value)}><option value="all">All</option><option value="warning">Warning</option><option value="critical">Critical</option><option value="info">Information</option></select><button className="secondary" onClick={all}>Mark all read</button></div></section><section className="panel">{rows.length?rows.map(a=><AlertRow key={a.id} alert={a} onRead={read}/>):<div className="empty"><b>No alerts</b><p>The system will generate alerts when configured thresholds are reached.</p></div>}</section></div>}
function AlertRow({alert,onRead}){return <div className={`alert-item ${alert.severity} ${alert.is_read?'read':''}`}><div className="alert-symbol">{alert.severity==='critical'?'!':alert.severity==='warning'?'△':'i'}</div><div className="alert-main"><div className="alert-title"><b>{alert.title}</b><span>{alert.severity}</span></div><p>{alert.message}</p><small>{alert.created_at?new Date(alert.created_at).toLocaleString():''} · {alert.channel||'dashboard'}</small></div>{onRead&&!alert.is_read&&<button className="small-btn" onClick={()=>onRead(alert.id)}>Read</button>}</div>}
function USSD({user}){const [text,setText]=useState(''),[screen,setScreen]=useState('Welcome to AgriMarket\n1. Check Price\n2. Forecast\n3. Report Price\n4. Subscribe SMS\n5. Help'),[history,setHistory]=useState([]);const send=async(v=text)=>{try{const d=await api('/ussd/',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sessionId:'WEB-DEMO',text:v})});setScreen(d.response);setHistory(h=>[...h,{input:v||'START',output:d.response}]);setText('')}catch(e){setScreen('ERROR: '+e.message)}};return <div className="page"><div className="two-col"><section className="panel"><div className="eyebrow">LOW-BANDWIDTH ACCESS</div><h2>USSD / SMS service</h2><p>The simulator demonstrates the menu that can be connected to a telecom aggregator. SMS alert subscriptions are also supported in the backend.</p><div className="phone"><div className="phone-head">AGRI MARKET · USSD</div><div className="phone-screen">{screen.split('\n').map((x,i)=><div key={i}>{x}</div>)}</div><input value={text} onChange={e=>setText(e.target.value)} onKeyDown={e=>e.key==='Enter'&&send()} placeholder="e.g. 1*1*1"/><button className="primary wide" onClick={()=>send()}>SEND</button></div><div className="quick"><b>Quick tests</b>{['1','1*1','1*1*1','2','2*1','2*1*1','3','4'].map(x=><button className="secondary" key={x} onClick={()=>send(x)}>{x}</button>)}</div></section><section className="panel"><h3>Session history</h3>{history.map((h,i)=><div className="history" key={i}><b>{h.input}</b><pre>{h.output}</pre></div>)}<SMSSubscription user={user}/></section></div></div>}

function SMSSubscription({user}){const [on,setOn]=useState(false),[msg,setMsg]=useState('');const save=async()=>{try{const d=await api('/subscriptions/',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user:user.id,channel:'sms',active:on})});setMsg(on?'SMS alerts enabled for this account.':'SMS alerts disabled.')}catch(e){setMsg(e.message)}};return <div className="info-box"><b>SMS alert subscription</b><p>Enable SMS channel preference. A telecom aggregator credential is required before real messages can be delivered.</p><label className="check-line"><input type="checkbox" checked={on} onChange={e=>setOn(e.target.checked)}/> Receive price-spike and forecast alerts by SMS</label><button className="secondary" onClick={save}>Save SMS preference</button>{msg&&<div className="success">{msg}</div>}</div>}

function Administration(){return <div className="page"><section className="hero-panel"><div><div className="eyebrow">SYSTEM CONTROL</div><h2>Administration</h2><p>Users, markets, commodities, data quality, routes, forecasts and subscriptions are managed through Django Admin.</p></div><a className="primary link-button" href="/admin/" target="_blank">Open Admin →</a></section><div className="admin-cards"><div><span>01</span><h3>Users & roles</h3><p>Farmer, Trader, Transporter, Field Agent, Policy Maker, Analyst and Administrator.</p></div><div><span>02</span><h3>Intelligence data</h3><p>Prices, climate, macro indicators, supply/demand and routes.</p></div><div><span>03</span><h3>Models & plans</h3><p>Forecast scores, selected model, shipment plans, alerts and subscriptions.</p></div></div></div>}
createRoot(document.getElementById('root')).render(<App/>);
