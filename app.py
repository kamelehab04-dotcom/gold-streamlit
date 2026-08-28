import json, os
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="BLACK PYRAMID FX PRO", page_icon="â–²", layout="wide")

PAIRS = {
    "EUR/USD":"EURUSD=X", "GBP/USD":"GBPUSD=X", "USD/JPY":"USDJPY=X",
    "AUD/USD":"AUDUSD=X", "USD/CAD":"USDCAD=X", "USD/CHF":"USDCHF=X",
    "EUR/JPY":"EURJPY=X", "GBP/JPY":"GBPJPY=X", "EUR/GBP":"EURGBP=X",
    "NZD/USD":"NZDUSD=X",
}
DXY = "DX-Y.NYB"
STATE_FILE = Path("black_pyramid_fx_state.json")

def load_state():
    try: return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception: return {"active_trade":None,"closed_trades":[]}

def save_state(s): STATE_FILE.write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding="utf-8")
if "state" not in st.session_state: st.session_state.state=load_state()

@st.cache_data(ttl=45,show_spinner=False)
def data(symbol,period,interval):
    try:
        x=yf.download(symbol,period=period,interval=interval,auto_adjust=False,progress=False,threads=False)
        if x is None or x.empty:return None
        if isinstance(x.columns,pd.MultiIndex): x.columns=[c[0] for c in x.columns]
        x.columns=[str(c).lower() for c in x.columns]
        if not all(c in x for c in ["open","high","low","close"]):return None
        if "volume" not in x:x["volume"]=0
        x=x[["open","high","low","close","volume"]].apply(pd.to_numeric,errors="coerce").dropna(subset=["open","high","low","close"])
        return x[~x.index.duplicated(keep="last")].sort_index()
    except Exception:return None

@st.cache_data(ttl=20,show_spinner=False)
def price(symbol):
    x=data(symbol,"5d","5m")
    if x is None:return None,None
    p=float(x.close.iloc[-1]); q=float(x.close.iloc[-2])
    return p,((p-q)/q*100 if q else 0)

def rsi(c,n=14):
    d=c.diff(); g=d.clip(lower=0); l=-d.clip(upper=0)
    ag=g.ewm(alpha=1/n,adjust=False,min_periods=n).mean()
    al=l.ewm(alpha=1/n,adjust=False,min_periods=n).mean()
    return 100-100/(1+ag/al.replace(0,np.nan))

def atr(x,n=14):
    pc=x.close.shift(1)
    tr=pd.concat([x.high-x.low,(x.high-pc).abs(),(x.low-pc).abs()],axis=1).max(axis=1)
    return tr.ewm(alpha=1/n,adjust=False,min_periods=n).mean()

def adx(x,n=14):
    up=x.high.diff(); dn=-x.low.diff()
    plus=pd.Series(np.where((up>dn)&(up>0),up,0),index=x.index)
    minus=pd.Series(np.where((dn>up)&(dn>0),dn,0),index=x.index)
    a=atr(x,n)
    p=100*plus.ewm(alpha=1/n,adjust=False).mean()/a.replace(0,np.nan)
    m=100*minus.ewm(alpha=1/n,adjust=False).mean()/a.replace(0,np.nan)
    dx=100*(p-m).abs()/(p+m).replace(0,np.nan)
    return dx.ewm(alpha=1/n,adjust=False,min_periods=n).mean(),p,m

def enrich(x):
    x=x.copy()
    x["ema20"]=x.close.ewm(span=20,adjust=False).mean()
    x["ema50"]=x.close.ewm(span=50,adjust=False).mean()
    x["ema200"]=x.close.ewm(span=200,adjust=False).mean()
    x["rsi"]=rsi(x.close); x["atr"]=atr(x); x["adx"],x["pdi"],x["mdi"]=adx(x)
    e12=x.close.ewm(span=12,adjust=False).mean(); e26=x.close.ewm(span=26,adjust=False).mean()
    x["macd"]=e12-e26; x["macds"]=x.macd.ewm(span=9,adjust=False).mean()
    x["hist"]=x.macd-x.macds
    ph=x.high.rolling(5).max().shift(1); pl=x.low.rolling(5).min().shift(1)
    x["bos_bull"]=x.close>ph; x["bos_bear"]=x.close<pl
    hi=x.high.rolling(20).max().shift(1); lo=x.low.rolling(20).min().shift(1)
    x["sweep_bull"]=(x.low<lo)&(x.close>lo); x["sweep_bear"]=(x.high>hi)&(x.close<hi)
    x["fvg_bull"]=x.low>x.high.shift(2); x["fvg_bear"]=x.high<x.low.shift(2)
    x["ob_bull"]=(x.close>x.open)&((x.close-x.open).abs()>x.atr*1.15)&(x.close.shift(1)<x.open.shift(1))
    x["ob_bear"]=(x.close<x.open)&((x.close-x.open).abs()>x.atr*1.15)&(x.close.shift(1)>x.open.shift(1))
    rh=x.high.rolling(50).max(); rl=x.low.rolling(50).min(); mid=(rh+rl)/2
    x["premium"]=x.close>mid; x["discount"]=x.close<mid
    return x

def tf4(x):
    return x.resample("4h",label="right",closed="right").agg({"open":"first","high":"max","low":"min","close":"last","volume":"sum"}).dropna()

def bias(x):
    if x is None or len(x)<220:return "WAIT"
    z=enrich(x).iloc[-1]; b=s=0
    if z.close>z.ema200:b+=3
    else:s+=3
    if z.ema20>z.ema50:b+=2
    else:s+=2
    if z.bos_bull:b+=2
    if z.bos_bear:s+=2
    if z.adx>=18:
        if z.pdi>z.mdi:b+=1
        elif z.mdi>z.pdi:s+=1
    if b>=s+2:return "BULLISH"
    if s>=b+2:return "BEARISH"
    return "NEUTRAL"

@st.cache_data(ttl=60,show_spinner=False)
def mtf(symbol):
    h=data(symbol,"180d","1h"); m=data(symbol,"30d","15m")
    if h is None or m is None:return None
    h4=tf4(h)
    return {"4H":bias(h4),"1H":bias(h),"15M":bias(m),"h4":enrich(h4),"h1":enrich(h),"m15":enrich(m)}

@st.cache_data(ttl=60,show_spinner=False)
def dxy_data(): 
    x=data(DXY,"180d","1h")
    return enrich(x) if x is not None else None

def dxy_bias(symbol,h):
    d=dxy_data()
    if d is None:return "UNKNOWN",0
    common=h.index.intersection(d.index)
    if len(common)<40:return "UNKNOWN",0
    corr=float(h.loc[common,"close"].pct_change().tail(60).corr(d.loc[common,"close"].pct_change().tail(60)))
    return bias(d),corr

def trade(z,direction,entry):
    a=float(z.atr.iloc[-1])
    if not np.isfinite(a) or a<=0:return None
    lo=float(z.low.tail(40).min()); hi=float(z.high.tail(40).max())
    if direction=="BUY":
        sl=min(lo,entry-a*.9); risk=entry-sl
        if risk<a*.65:risk=a*.8; sl=entry-risk
        t1=entry+risk*1.25; t2=entry+risk*2; t3=entry+risk*2.75
    else:
        sl=max(hi,entry+a*.9); risk=sl-entry
        if risk<a*.65:risk=a*.8; sl=entry+risk
        t1=entry-risk*1.25; t2=entry-risk*2; t3=entry-risk*2.75
    rr=abs(t2-entry)/abs(entry-sl)
    if rr<1.8:return None
    return dict(direction=direction,entry=round(entry,6),stop_loss=round(sl,6),
                target1=round(t1,6),target2=round(t2,6),target3=round(t3,6),rr=round(rr,2))

def analyze(name,symbol):
    p,ch=price(symbol); m=mtf(symbol)
    if p is None or m is None:return None
    z=m["m15"]; q=z.iloc[-1]; b4,b1,b15=m["4H"],m["1H"],m["15M"]
    buy=sell=0; br=[]; sr=[]
    if b4=="BULLISH":buy+=22;br.append("4H Bullish")
    elif b4=="BEARISH":sell+=22;sr.append("4H Bearish")
    if b1=="BULLISH":buy+=18;br.append("1H Bullish")
    elif b1=="BEARISH":sell+=18;sr.append("1H Bearish")
    if b15=="BULLISH":buy+=8;br.append("15M Bullish")
    elif b15=="BEARISH":sell+=8;sr.append("15M Bearish")
    if q.sweep_bull:buy+=18;br.append("Liquidity Sweep +")
    if q.sweep_bear:sell+=18;sr.append("Liquidity Sweep -")
    if q.bos_bull:buy+=12;br.append("BOS/MSS +")
    if q.bos_bear:sell+=12;sr.append("BOS/MSS -")
    if q.ob_bull:buy+=10;br.append("Order Block +")
    if q.ob_bear:sell+=10;sr.append("Order Block -")
    if q.fvg_bull:buy+=7;br.append("FVG +")
    if q.fvg_bear:sell+=7;sr.append("FVG -")
    if q.discount:buy+=5;br.append("Discount")
    if q.premium:sell+=5;sr.append("Premium")
    if 50<=q.rsi<=68:buy+=5;br.append(f"RSI {q.rsi:.1f}")
    if 32<=q.rsi<=50:sell+=5;sr.append(f"RSI {q.rsi:.1f}")
    if q.hist>0:buy+=4;br.append("MACD +")
    elif q.hist<0:sell+=4;sr.append("MACD -")
    if q.adx>=18:
        if q.pdi>q.mdi:buy+=4;br.append("ADX +DI")
        elif q.mdi>q.pdi:sell+=4;sr.append("ADX -DI")
    db,corr=dxy_bias(symbol,m["h1"])
    if abs(corr)>=.25:
        if db=="BEARISH":buy+=6;br.append(f"DXY Bearish {corr:.2f}")
        elif db=="BULLISH":sell+=6;sr.append(f"DXY Bullish {corr:.2f}")
    direction="BUY" if buy>sell else "SELL" if sell>buy else "WAIT"
    edge=abs(buy-sell)
    bull_trigger=bool(q.sweep_bull or q.bos_bull or q.ob_bull or q.fvg_bull)
    bear_trigger=bool(q.sweep_bear or q.bos_bear or q.ob_bear or q.fvg_bear)
    bull_zone=bool(q.ob_bull or q.fvg_bull or q.discount)
    bear_zone=bool(q.ob_bear or q.fvg_bear or q.premium)
    if direction=="BUY":
        aplus=b4=="BULLISH" and b1=="BULLISH" and bull_trigger and bull_zone and q.rsi<70
        aset=(b4=="BULLISH" or b1=="BULLISH") and bull_trigger and bull_zone and q.rsi<72 and edge>=8
    elif direction=="SELL":
        aplus=b4=="BEARISH" and b1=="BEARISH" and bear_trigger and bear_zone and q.rsi>30
        aset=(b4=="BEARISH" or b1=="BEARISH") and bear_trigger and bear_zone and q.rsi>28 and edge>=8
    else:aplus=aset=False
    gate=aplus or aset
    if not gate:
        signal="WAIT"; conf=min(68,50+edge*.35); tr=None; grade="WAIT"
    else:
        grade="A+" if aplus else "A"
        conf=min(95,72+edge*.20+min(max(buy,sell),100)*.10) if aplus else min(79,67+edge*.18+min(max(buy,sell),100)*.08)
        tr=trade(z,direction,float(p)); signal=direction if tr else "WAIT"
        if signal=="WAIT":grade="WAIT"
    return dict(name=name,symbol=symbol,price=p,change=ch,signal=signal,grade=grade,confidence=round(conf,1),
                buy=round(buy,1),sell=round(sell,1),edge=round(edge,1),**{"4H":b4,"1H":b1,"15M":b15},
                rsi=round(float(q.rsi),1),adx=round(float(q.adx),1),dxy=db,corr=round(corr,3),
                reasons=(br if direction=="BUY" else sr),trade=tr,chart=z)

@st.cache_data(ttl=60,show_spinner=False)
def scan():
    out=[]
    for n,s in PAIRS.items():
        r=analyze(n,s)
        if r:out.append(r)
    rank={"A+":3,"A":2,"WAIT":1}
    return sorted(out,key=lambda x:(rank[x["grade"]],x["confidence"],x["edge"]),reverse=True)

# ---------------- UI ----------------
st.markdown("<style>.stApp{background:#050505}.card{border:1px solid #b8941f;border-radius:16px;padding:20px;background:#0b0b0b}.gold{color:#c7a52d}</style>",unsafe_allow_html=True)
st.markdown('<div class="card"><h1>â–² BLACK PYRAMID FX PRO</h1><div class="gold">Forex Scanner â€¢ MTF â€¢ SMC/ICT â€¢ Liquidity â€¢ DXY â€¢ Risk/Reward</div></div>',unsafe_allow_html=True)

state=st.session_state.state; active=state.get("active_trade")
with st.sidebar:
    pair=st.selectbox("ط§ظ„ط²ظˆط¬",list(PAIRS))
    if st.button("ًں”„ طھط­ط¯ظٹط« ط§ظ„ط¨ظٹط§ظ†ط§طھ"):st.cache_data.clear();st.rerun()

if active:
    st.warning(f"ًں”’ ط§ظ„طµظپظ‚ط© ط§ظ„ظ…ط«ط¨طھط©: {active['name']} {active['direction']} | Entry {active['entry']} | SL {active['stop_loss']} | TP2 {active['target2']}")
    if st.button("â‌Œ ط¥ط؛ظ„ط§ظ‚ ظˆطھط³ط¬ظٹظ„ ط§ظ„طµظپظ‚ط©"):
        active["status"]="closed_manual";active["closed_at"]=datetime.now(timezone.utc).isoformat()
        state["closed_trades"].append(active);state["active_trade"]=None;save_state(state);st.session_state.state=state;st.rerun()

cur=analyze(pair,PAIRS[pair])
if cur is None:st.error("ظ„ط§ طھظˆط¬ط¯ ط¨ظٹط§ظ†ط§طھ ظƒط§ظپظٹط©.");st.stop()

a,b,c,d,e=st.columns(5)
a.metric("Price",f"{cur['price']:.5f}");b.metric("4H",cur["4H"]);c.metric("1H",cur["1H"]);d.metric("15M",cur["15M"]);e.metric("DXY",cur["dxy"])

if cur["signal"]=="BUY":st.success(f"ًںں¢ BUY {cur['grade']} â€” {cur['confidence']}%")
elif cur["signal"]=="SELL":st.error(f"ًں”´ SELL {cur['grade']} â€” {cur['confidence']}%")
else:st.info(f"âڑھ WAIT â€” {cur['confidence']}%")

if cur["trade"]:
    t=cur["trade"]; st.markdown("### ًںژ¯ ط§ظ„طµظپظ‚ط©")
    a,b,c,d,e=st.columns(5)
    a.metric("Entry",f"{t['entry']:.5f}");b.metric("SL",f"{t['stop_loss']:.5f}");c.metric("TP1",f"{t['target1']:.5f}");d.metric("TP2",f"{t['target2']:.5f}");e.metric("R/R",f"1:{t['rr']:.2f}")
    if not active and st.button("ًں”’ طھط«ط¨ظٹطھ AI Trade",use_container_width=True):
        state["active_trade"]={"id":"BPFX-"+datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),"name":cur["name"],"symbol":cur["symbol"],
            "direction":t["direction"],"grade":cur["grade"],"confidence":cur["confidence"],**t,"opened_at":datetime.now(timezone.utc).isoformat(),"status":"open"}
        save_state(state);st.session_state.state=state;st.rerun()

st.markdown("### ًں”ژ ط£ط³ط¨ط§ط¨ ط§ظ„ظ‚ط±ط§ط±")
for r in cur["reasons"]:st.write("â€¢",r)

z=cur["chart"].tail(250)
fig=go.Figure(go.Candlestick(x=z.index,open=z.open,high=z.high,low=z.low,close=z.close,name="Price"))
for col in ["ema20","ema50","ema200"]:fig.add_trace(go.Scatter(x=z.index,y=z[col],name=col.upper()))
if cur["trade"]:
    for y,label in [(cur["trade"]["entry"],"ENTRY"),(cur["trade"]["stop_loss"],"SL"),(cur["trade"]["target2"],"TP2")]:
        fig.add_hline(y=y,line_dash="dash",annotation_text=label)
fig.update_layout(height=600,template="plotly_dark",xaxis_rangeslider_visible=False)
st.plotly_chart(fig,use_container_width=True)

st.markdown("---");st.markdown("## ًںڑ¨ ظ…ط§ط³ط­ ط£ط²ظˆط§ط¬ ط§ظ„ط¹ظ…ظ„ط§طھ")
with st.spinner("ظپط­طµ ط§ظ„ط£ط²ظˆط§ط¬..."):results=scan()
if results:
    table=pd.DataFrame([{"Pair":r["name"],"Signal":r["signal"],"Grade":r["grade"],"Confidence":r["confidence"],"4H":r["4H"],"1H":r["1H"],"15M":r["15M"],"RSI":r["rsi"],"ADX":r["adx"],"DXY":r["dxy"],"R/R":r["trade"]["rr"] if r["trade"] else None} for r in results])
    st.dataframe(table,use_container_width=True,hide_index=True)
    confirmed=[r for r in results if r["trade"]]
    if confirmed:
        st.markdown("### ًںڈ† ط£ظپط¶ظ„ ط§ظ„ظپط±طµ")
        for r in confirmed[:3]:
            st.write(f"{'ًںں¢' if r['signal']=='BUY' else 'ًں”´'} **{r['name']}** â€” {r['signal']} {r['grade']} â€” {r['confidence']}% â€” R/R 1:{r['trade']['rr']}")
            st.caption(" | ".join(r["reasons"][:8]))
    else:st.info("ظ„ط§ طھظˆط¬ط¯ طµظپظ‚ط© ظ…ظƒطھظ…ظ„ط© ط§ظ„ط¢ظ†ط› ط§ظ„ظ†ط¸ط§ظ… ظ„ط§ ظٹط¬ط¨ط± ط§ظ„ط³ظˆظ‚ ط¹ظ„ظ‰ طµظپظ‚ط©.")

st.markdown("---");st.markdown("## ًں“ڑ ط³ط¬ظ„ ط§ظ„طµظپظ‚ط§طھ")
closed=state.get("closed_trades",[])
if closed:
    st.dataframe(pd.DataFrame([{"ID":x.get("id"),"Pair":x.get("name"),"Direction":x.get("direction"),"Grade":x.get("grade"),"Confidence":x.get("confidence"),"Entry":x.get("entry"),"SL":x.get("stop_loss"),"TP2":x.get("target2"),"Status":x.get("status")} for x in closed[-50:]]),use_container_width=True,hide_index=True)
else:st.info("ظ„ط§ طھظˆط¬ط¯ طµظپظ‚ط§طھ ظ…ط³ط¬ظ„ط©.")
st.caption("ط§ظ„ط«ظ‚ط© ظ„ظٹط³طھ ط§ط­طھظ…ط§ظ„ ط±ط¨ط­ ط­ظ‚ظٹظ‚ظٹظ‹ط§. ط§ط®طھط¨ط± ط§ظ„ظ†ط¸ط§ظ… Backtest ظˆForward Test ظ‚ط¨ظ„ ط§ظ„طھط¯ط§ظˆظ„ ط¨ط£ظ…ظˆط§ظ„ ط­ظ‚ظٹظ‚ظٹط©.")
