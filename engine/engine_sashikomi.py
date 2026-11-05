# 200差し込みエンジン(たくちん 11-05「200の差し込みとれんかな」+ だまし回避スキルの差し込み型)
# 1) 差し込み(買い)= 1h足の安値が 200(LINE: '1h' か '4h' のEMA200)の 5pips 以内まで下りる。実体は200の上に残る(割り込まない)。売りは逆
# 2) 離れ = 差し込みから6本以内に 1h終値が9の上で確定 かつ 1h21の傾きが上向き → 次の5分足の始値で入る【置き換え:スキルの「5ピップ内・6本以内」】
# 3) 足し = 5分の押し目(21に触れ9の上で確定)ごとに +20p で1発、最大20
# 4) 降り = 1h の9割れ(実体の真ん中と終値が9の向こう)で全部利確。網=5分22本の高安−4hATR×3
import os, sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from engine_ichi import load, ema, atr14, bigbars, to_m5, PIP, angle21
import numpy as np, pandas as pd
def prep(m5,h1,LINE='1h',NEAR=5.0,WIN=6):
    m=m5.copy(); idx=m.index; c=m.c
    hc=h1.c; e9=ema(hc,9); ang=angle21(h1)
    if LINE=='1h': s2=ema(hc,200)
    else:
        b4=bigbars(h1,'4h'); s2=ema(b4.c,200); s2.index=s2.index+pd.Timedelta(hours=4); s2=s2.reindex(h1.index,method='ffill')   # 確定した4h200を1h足に
    bt=np.minimum(h1.o,hc); btop=np.maximum(h1.o,hc)
    sb=(h1.l<=s2+NEAR*PIP)&(bt>s2)            # 買いの差し込み:安値が200の5p以内・実体は200の上
    ss=(h1.h>=s2-NEAR*PIP)&(btop<s2)          # 売りの差し込み
    recent_b=sb.rolling(WIN).max().fillna(0).astype(bool); recent_s=ss.rolling(WIN).max().fillna(0).astype(bool)
    go=pd.Series(np.where(recent_b&(hc>e9)&(ang>0)&(hc>s2),1,np.where(recent_s&(hc<e9)&(ang<0)&(hc<s2),-1,0)),index=h1.index)
    bm=(h1.o+hc)/2; nine=pd.Series(np.where((bm>e9)&(hc>e9),1,np.where((bm<e9)&(hc<e9),-1,0)),index=h1.index)
    for k,v in (('go',go),('nine',nine)): m[k]=to_m5(v.astype(float),'1h',idx)
    m['newh']=(idx.minute==0)
    e95,e215=ema(c,9),ema(c,21); mid=c.rolling(20).mean(); sd=c.rolling(20).std(ddof=0)
    pb=(m.l<=e215)&(c>e95)&(e95>e215)&(c<=mid+2*sd); ps=(m.h>=e215)&(c<e95)&(e95<e215)&(c>=mid-2*sd)
    m['pull']=pd.Series(np.where(pb,1,np.where(ps,-1,0)),index=idx).shift(1)
    b4=bigbars(h1,'4h'); a=to_m5(atr14(b4),'4h',idx)
    m['chL']=m.h.rolling(22).max().shift(1)-3*a; m['chS']=m.l.rolling(22).min().shift(1)+3*a
    return m.dropna()
def run(m,spr=0.3*PIP,MAXPOS=20,ADD=20.0):
    O,H,L=m.o.values,m.h.values,m.l.values; G=m.go.values; NN=m.nine.values; NH=m.newh.values; P=m.pull.values
    CL,CS=m.chL.values,m.chS.values; T=m.index
    pos=[]; log=[]; camp=0; prev_pull=0; prevg=0
    def cls(i,p,ex,why): log.append(dict(camp=p['camp'],n=p['n'],dir='買' if p['d']>0 else '売',kind=p['k'],open=p['ot'],entry=p['e'],close=T[i],exit=ex,why=why,pips=(ex-p['e'])/PIP*p['d'],i0=p['i0'],i1=i))
    def opn(i,d,k):
        nonlocal camp
        px=O[i]+spr if d>0 else O[i]; sl=CL[i] if d>0 else CS[i]
        if d>0 and sl>px: sl=px-10*PIP
        if d<0 and sl<px: sl=px+10*PIP
        if not pos: camp+=1
        pos.append(dict(d=d,e=px,sl=sl,ot=T[i],camp=camp,n=len(pos)+1,k=k,i0=i))
    for i in range(len(m)):
        if NH[i]:
            if pos and int(NN[i])==-pos[0]['d']:
                for p in pos: cls(i,p,O[i] if p['d']>0 else O[i]+spr,'9割れ')
                pos=[]
            g=int(G[i])
            if not pos and g!=0 and g!=prevg: opn(i,g,'差し込み')      # 差し込みからの離れ(同じ差し込みでは1回)
            prevg=g
        pl=int(P[i])
        if pos and len(pos)<MAXPOS:
            d=pos[0]['d']
            if pl==d and prev_pull!=d:
                pxc=O[i] if d>0 else O[i]+spr
                if d*(pxc-pos[-1]['e'])>=ADD*PIP: opn(i,d,'押し目')
        prev_pull=pl
        if pos:
            d=pos[0]['d']
            for p in pos:
                sl=CL[i] if d>0 else CS[i]
                if d>0 and sl>p['sl']+0.001 and sl<O[i]: p['sl']=sl
                if d<0 and sl<p['sl']-0.001 and sl>O[i]+spr: p['sl']=sl
        keep=[]
        for p in pos:
            d=p['d']
            if d>0 and L[i]<=p['sl']: cls(i,p,O[i] if O[i]<=p['sl'] else p['sl'],'網')
            elif d<0 and H[i]+spr>=p['sl']: cls(i,p,O[i]+spr if O[i]+spr>=p['sl'] else p['sl'],'網')
            else: keep.append(p)
        pos=keep
    out=pd.DataFrame(log); out.attrs['open_left']=len(pos); return out
