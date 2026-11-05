# 根っこエンジン 第2版(たくちん 11-05「無限リーチ 竿根っこバンドブレイクのあとすぐだけで良い」)
# 1) 根っこ(★)= 1hの帯が直前6本のどこかでしぼみ(幅<ふだん100本の0.7倍【置き換え】)、終値が±2σの外へ出た最初の1本
# 2) 入り = 根っこの1h足が確定した次の5分足の始値ですぐ
# 3) 無限リーチ = 根っこの後、1h足が帯の外(±2σ)で確定し続けている間だけ、前の玉から20pips進むごとに1発(最大20)。1h足が帯の中で確定したら もう足さない【置き換え】
# 4) 降り = 9割れ(1h実体の真ん中と終値が9の向こう)で全部利確。その根っこは終わり
# 5) 網 = 5分22本の高安 − 4hATR14×3(損切りの守り)
# 7) 根っこは1h200の向き側だけ(買い=1h終値が1hEMA200の上、売り=下)— たくちん「200/4/1差し込みの所5で合わせれるやろ」
# 6) だまし回避(スキルの決まり):根っこの足で 1h遅行(26本前)が絡んでいたら入らない(爆弾岩)/ 1h21の角度が根っこと逆向きなら入らない(21が逆向きならついて起きたのは12%)
import os, sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from engine_ichi import load, ema, atr14, bigbars, to_m5, PIP, angle21, karami
import numpy as np, pandas as pd
TFLEN={'15min':pd.Timedelta(minutes=15),'30min':pd.Timedelta(minutes=30),'1h':pd.Timedelta(hours=1),'2h':pd.Timedelta(hours=2),'4h':pd.Timedelta(hours=4)}
def tfbars(m5,h1,tf):
    agg=dict(o='first',h='max',l='min',c='last')
    if tf in ('15min','30min'): return m5.resample(tf).agg(agg).dropna()
    return h1 if tf=='1h' else h1.resample(tf).agg(agg).dropna()
def at_close(s,tf,idx): s=s.copy(); s.index=s.index+TFLEN[tf]; return s.reindex(idx,method='ffill')   # その足が確定した時刻から使う
def prep(m5,h1,TF='1h',CONF=False):   # CONF: 確認の足(根っこの次の足も帯の外で確定)を待って入る
    m=m5.copy(); idx=m.index; h1_=h1; h1=tfbars(m5,h1_,TF); hc=h1.c
    mid1=hc.rolling(20).mean(); sd1=hc.rolling(20).std(ddof=0); w=4*sd1; sq=w<0.7*w.rolling(100).mean()
    recent_sq=sq.shift(1).rolling(6).max().fillna(0).astype(bool)
    up=hc>mid1+2*sd1; dn=hc<mid1-2*sd1
    first_up=up&~up.shift(1,fill_value=False); first_dn=dn&~dn.shift(1,fill_value=False)
    root=pd.Series(np.where(first_up&recent_sq,1,np.where(first_dn&recent_sq,-1,0)),index=h1.index)
    ang=angle21(h1); kar=karami(h1)
    root=root.where(~kar,0)                                   # だまし回避:遅行が絡む根っこ(爆弾岩)は捨てる
    root=root.where(~((root>0)&(ang<0))&~((root<0)&(ang>0)),0)   # だまし回避:1h21が逆向きの根っこは捨てる
    s200=ema(hc,200)
    bm1=(h1.o+hc)/2
    above=(hc>s200)&(bm1>s200); below=(hc<s200)&(bm1<s200)   # 実体が200の向こうへ渡り切っている(毛1本は水しぶき)
    root=root.where(~((root>0)&~above)&~((root<0)&~below),0)   # たくちん「200/4/1」:根っこは1h200の向き側だけ
    out=pd.Series(np.where(up,1,np.where(dn,-1,0)),index=h1.index)                    # 1h が帯の外(上+1/下−1)
    if CONF:   # bb開きのだまし回避:根っこの次の足も同じ向きに帯の外で確定したら、その足を根っこにする(=1本待つ)
        root=pd.Series(np.where((root.shift(1)==1)&(out==1),1,np.where((root.shift(1)==-1)&(out==-1),-1,0)),index=h1.index)
    e91=ema(hc,9); bm=(h1.o+hc)/2
    nine=pd.Series(np.where((bm>e91)&(hc>e91),1,np.where((bm<e91)&(hc<e91),-1,0)),index=h1.index)
    for k,v in (('root',root),('out1',out),('nine',nine)): m[k]=at_close(v.astype(float),TF,idx)
    b4=bigbars(h1_,'4h'); a=to_m5(atr14(b4),'4h',idx)
    m['chL']=m.h.rolling(22).max().shift(1)-3*a; m['chS']=m.l.rolling(22).min().shift(1)+3*a
    m['newh']=pd.Series(1.0,index=h1.index+TFLEN[TF]).reindex(idx).notna().values   # その足が確定した直後の5分足
    return m.dropna()
def run(m,spr=0.3*PIP,MAXPOS=20,ADD=20.0):
    O,H,L=m.o.values,m.h.values,m.l.values; R=m.root.values; OUT=m.out1.values; NN=m.nine.values; NH=m.newh.values
    CL,CS=m.chL.values,m.chS.values; T=m.index
    pos=[]; log=[]; camp=0; run_on=False
    def cls(i,p,ex,why): log.append(dict(camp=p['camp'],n=p['n'],dir='買' if p['d']>0 else '売',kind=p['k'],open=p['ot'],entry=p['e'],close=T[i],exit=ex,why=why,pips=(ex-p['e'])/PIP*p['d'],i0=i0s[id(p)],i1=i))
    i0s={}
    def opn(i,d,k):
        nonlocal camp
        px=O[i]+spr if d>0 else O[i]; sl=CL[i] if d>0 else CS[i]
        if d>0 and sl>px: sl=px-10*PIP
        if d<0 and sl<px: sl=px+10*PIP
        if not pos: camp+=1
        p=dict(d=d,e=px,sl=sl,ot=T[i],camp=camp,n=len(pos)+1,k=k); i0s[id(p)]=i; pos.append(p)
    for i in range(len(m)):
        if NH[i]:
            r=int(R[i]); nn=int(NN[i])
            if pos and nn==-pos[0]['d']:
                for p in pos: cls(i,p,O[i] if p['d']>0 else O[i]+spr,'9割れ')
                pos=[]; run_on=False
            if pos and int(OUT[i])!=pos[0]['d']: run_on=False        # 1h が帯の中へ戻った → もう足さない
            if r!=0:
                if pos and pos[0]['d']!=r:
                    for p in pos: cls(i,p,O[i] if p['d']>0 else O[i]+spr,'逆の根っこ')
                    pos=[]
                if not pos: opn(i,r,'根っこ'); run_on=True
        if pos and run_on and len(pos)<MAXPOS:
            d=pos[0]['d']; pxc=O[i] if d>0 else O[i]+spr
            if d*(pxc-pos[-1]['e'])>=ADD*PIP: opn(i,d,'無限リーチ')
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
        if not pos: run_on=False
    out=pd.DataFrame(log); out.attrs['open_left']=len(pos); return out
