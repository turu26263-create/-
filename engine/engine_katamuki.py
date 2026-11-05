# 傾き押し目エンジン(たくちん 11-05「傾き決めてどの時間軸かで9上エントリからの押し目でないともうからんな」)
# 1) 向き = その足(TF)の21の角度(だまし回避スキルの測り方)が向き側に ANG 度以上。55度を超えたら竿先で新しく入らない
# 2) 入り = TF の終値が9の上で確定(9上)→ 次の5分足の始値(売りは9の下)
# 3) 押し目 = 確定5分足のひげが21に触れ・終値が9の向き側・9と21が向き側 → 前の玉から20p で1発(最大20)
# 4) 降り = TF の9割れ(実体の真ん中と終値が9の向こう)で全部利確。傾きが残っていれば次の9上でまた入る
# 5) 網 = 5分22本の高安 − 4hATR14×3(守り)
import os, sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from engine_ichi import load, ema, atr14, bigbars, PIP, angle21
from engine_nekko2 import tfbars, at_close, TFLEN
import numpy as np, pandas as pd
def prep(m5,h1,TF='1h',ANG=30.0,SAO=55.0):
    m=m5.copy(); idx=m.index; c=m.c
    b=tfbars(m5,h1,TF); bc=b.c; e9=ema(bc,9); ang=angle21(b)
    trend=pd.Series(np.where((ang>=ANG),1,np.where(ang<=-ANG,-1,0)),index=b.index)
    sao=pd.Series(np.where(ang>SAO,1,np.where(ang<-SAO,-1,0)),index=b.index)
    side9=pd.Series(np.sign(bc-e9).values,index=b.index)                                   # 9上(+1)/9下(−1)
    bm=(b.o+bc)/2; nine=pd.Series(np.where((bm>e9)&(bc>e9),1,np.where((bm<e9)&(bc<e9),-1,0)),index=b.index)
    for k,v in (('trend',trend),('sao',sao),('side9',side9),('nine',nine)): m[k]=at_close(v.astype(float),TF,idx)
    m['newb']=pd.Series(1.0,index=b.index+TFLEN[TF]).reindex(idx).notna().values
    e95,e215=ema(c,9),ema(c,21); mid=c.rolling(20).mean(); sd=c.rolling(20).std(ddof=0)
    pb=(m.l<=e215)&(c>e95)&(e95>e215)&(c<=mid+2*sd); ps=(m.h>=e215)&(c<e95)&(e95<e215)&(c>=mid-2*sd)
    m['pull']=pd.Series(np.where(pb,1,np.where(ps,-1,0)),index=idx).shift(1)
    b4=bigbars(h1,'4h'); a=at_close(atr14(b4),'4h',idx)
    m['chL']=m.h.rolling(22).max().shift(1)-3*a; m['chS']=m.l.rolling(22).min().shift(1)+3*a
    return m.dropna()
def run(m,spr=0.3*PIP,MAXPOS=20,ADD=20.0):
    O,H,L=m.o.values,m.h.values,m.l.values; TR=m.trend.values; SA=m.sao.values; S9=m.side9.values; NN=m.nine.values; NB=m.newb.values; P=m.pull.values
    CL,CS=m.chL.values,m.chS.values; T=m.index
    pos=[]; log=[]; camp=0; prev_pull=0
    def cls(i,p,ex,why): log.append(dict(camp=p['camp'],n=p['n'],dir='買' if p['d']>0 else '売',kind=p['k'],open=p['ot'],entry=p['e'],close=T[i],exit=ex,why=why,pips=(ex-p['e'])/PIP*p['d'],i0=p['i0'],i1=i))
    def opn(i,d,k):
        nonlocal camp
        px=O[i]+spr if d>0 else O[i]; sl=CL[i] if d>0 else CS[i]
        if d>0 and sl>px: sl=px-10*PIP
        if d<0 and sl<px: sl=px+10*PIP
        if not pos: camp+=1
        pos.append(dict(d=d,e=px,sl=sl,ot=T[i],camp=camp,n=len(pos)+1,k=k,i0=i))
    for i in range(len(m)):
        tr=int(TR[i])
        if NB[i]:
            if pos and int(NN[i])==-pos[0]['d']:                  # 9割れ → 利確
                for p in pos: cls(i,p,O[i] if p['d']>0 else O[i]+spr,'9割れ')
                pos=[]
            if not pos and tr!=0 and int(S9[i])==tr and int(SA[i])!=tr: opn(i,tr,'9上')   # 傾きあり・9上・竿先でない
        pl=int(P[i])
        if pos and len(pos)<MAXPOS:
            d=pos[0]['d']
            if pl==d and prev_pull!=d and int(SA[i])!=d:
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
