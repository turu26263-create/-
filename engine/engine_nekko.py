# 根っこエンジン(たくちん 11-05「根っこ無限リーチだけで9割れ利確」「バンドブレイクで押し目買い 竿根っこだけでいい」「まだ竿先で入っとる」)
# 1) 根っこ = 1時間足の帯が直前6本のどこかでしぼみ(幅<ふだん100本の0.7倍【置き換え】)、終値が ±2σ の外へ出た最初の1本(★)。2本目以降は竿先側なので根っこにしない
# 2) 根っこの後、5分足の押し目で入る:確定5分足のひげが21に触れ・終値が9の向き側・9と21が向き側
# 3) 竿先で入らない・足さない:1時間足の終値が ±2σ の外にある間、5分足の終値が ±2σ の外の時
# 4) 無限リーチ:押し目ごとに1発(帯21に触れて離れてまた触れたら次)、前の玉から20pips、最大20発
# 5) 降り:9割れ(1時間足の実体の真ん中と終値が9の向こう)で全部利確。網(5分22本の高安−4hATR×3)は損切りの守りだけ
# 6) 根っこの向きは 逆の根っこ か 1hの219(921) が来るまで生きる(9割れでは消さない=押し目)。ドテンはしない
#    11-05 直したミス:玉が無い時の9割れで根っこを消していた(押し目で入れずに終わっていた)
import os, sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from engine_ichi import load, ema, atr14, bigbars, to_m5, PIP
import numpy as np, pandas as pd
def prep(m5,h1):
    m=m5.copy(); idx=m.index; c=m.c
    e9,e21=ema(c,9),ema(c,21); mid=c.rolling(20).mean(); sd=c.rolling(20).std(ddof=0)
    hc=h1.c; mid1=hc.rolling(20).mean(); sd1=hc.rolling(20).std(ddof=0); w=4*sd1; sq=w<0.7*w.rolling(100).mean()
    recent_sq=sq.shift(1).rolling(6).max().fillna(0).astype(bool)
    up=hc>mid1+2*sd1; dn=hc<mid1-2*sd1
    first_up=up&~up.shift(1).fillna(False); first_dn=dn&~dn.shift(1).fillna(False)   # 帯の外へ出た最初の1本だけ(2本目以降は竿先側)
    root=pd.Series(np.where(first_up&recent_sq,1,np.where(first_dn&recent_sq,-1,0)),index=h1.index)   # ★=根っこ
    e91=ema(hc,9); bm=(h1.o+hc)/2
    nine=pd.Series(np.where((bm>e91)&(hc>e91),1,np.where((bm<e91)&(hc<e91),-1,0)),index=h1.index)                  # 9の渡り切り
    sao1=pd.Series(np.where(hc>mid1+2*sd1,1,np.where(hc<mid1-2*sd1,-1,0)),index=h1.index)                           # 1hの竿先
    o1=pd.Series(np.sign(e91-ema(hc,21)).values,index=h1.index)                     # 1h の 921(+1)/219(-1)
    m['o1']=to_m5(o1,'1h',idx)
    m['root']=to_m5(root.astype(float),'1h',idx); m['nine']=to_m5(nine.astype(float),'1h',idx); m['sao1']=to_m5(sao1.astype(float),'1h',idx)
    pb=(m.l<=e21)&(c>e9)&(e9>e21)&(c<=mid+2*sd); ps=(m.h>=e21)&(c<e9)&(e9<e21)&(c>=mid-2*sd)
    m['pull']=pd.Series(np.where(pb,1,np.where(ps,-1,0)),index=idx).shift(1)            # 確定5分足の押し目(戻り)
    m['t21']=pd.Series(np.where(m.l<=e21,1,0)-np.where(m.h>=e21,1,0),index=idx).shift(1)  # 21に触れた(押しの区切り用)
    b4=bigbars(h1,'4h'); a=to_m5(atr14(b4),'4h',idx)
    m['chL']=m.h.rolling(22).max().shift(1)-3*a; m['chS']=m.l.rolling(22).min().shift(1)+3*a
    m['newh']=(idx.minute==0)
    return m.dropna()
def run(m,spr=0.3*PIP,MAXPOS=20,ADD=20.0):
    O,H,L,C=m.o.values,m.h.values,m.l.values,m.c.values; O1=m.o1.values; R=m.root.values; N=m.nine.values; S=m.sao1.values; P=m.pull.values; NH=m.newh.values
    CL,CS=m.chL.values,m.chS.values; T=m.index
    pos=[]; log=[]; camp=0; rootd=0; used=False
    def cls(i,p,ex,why): log.append(dict(camp=p['camp'],n=p['n'],dir='買' if p['d']>0 else '売',kind=p['k'],open=p['ot'],entry=p['e'],close=T[i],exit=ex,why=why,pips=(ex-p['e'])/PIP*p['d'],i0=p['i0'],i1=i))
    def opn(i,d,k):
        nonlocal camp
        px=O[i]+spr if d>0 else O[i]; sl=CL[i] if d>0 else CS[i]
        if d>0 and sl>px: sl=px-10*PIP
        if d<0 and sl<px: sl=px+10*PIP
        if not pos: camp+=1
        pos.append(dict(d=d,e=px,sl=sl,ot=T[i],camp=camp,n=len(pos)+1,k=k,i0=i))
    last_pull=-1
    for i in range(len(m)):
        if NH[i]:                                          # 1時間足が確定した直後の5分足で、根っこ・9割れを見る
            r=int(R[i]); nn=int(N[i])
            if pos and nn==-pos[0]['d']:                   # 9割れ → 玉は全部利確。根っこは生かしたまま(次の押し目でまた入る)
                for p in pos: cls(i,p,O[i] if p['d']>0 else O[i]+spr,'9割れ')
                pos=[]
            if rootd and int(O1[i])==-rootd:               # 根っこが終わるのは 1h の219(買い根っこ)/921(売り根っこ)が確定した時
                for p in pos: cls(i,p,O[i] if p['d']>0 else O[i]+spr,'219')
                pos=[]; rootd=0
            if r!=0 and r!=rootd:
                if pos and pos[0]['d']!=r:
                    for p in pos: cls(i,p,O[i] if p['d']>0 else O[i]+spr,'逆の根っこ')
                    pos=[]
                rootd=r
        d=rootd; pl=int(P[i])
        if d!=0 and pl==d and int(S[i])!=d:               # 押し目・竿先でない
            if not pos: opn(i,d,'根っこ押し目'); last_pull=i
            elif len(pos)<MAXPOS and i-last_pull>1:
                pxc=O[i] if d>0 else O[i]+spr
                if d*(pxc-pos[-1]['e'])>=ADD*PIP: opn(i,d,'無限リーチ'); last_pull=i
        if pl==d: last_pull=max(last_pull,i) if pos else last_pull
        if pos:
            dd=pos[0]['d']
            for p in pos:
                sl=CL[i] if dd>0 else CS[i]
                if dd>0 and sl>p['sl']+0.001 and sl<O[i]: p['sl']=sl
                if dd<0 and sl<p['sl']-0.001 and sl>O[i]+spr: p['sl']=sl
        keep=[]
        for p in pos:
            dd=p['d']
            if dd>0 and L[i]<=p['sl']: cls(i,p,O[i] if O[i]<=p['sl'] else p['sl'],'網')
            elif dd<0 and H[i]+spr>=p['sl']: cls(i,p,O[i]+spr if O[i]+spr>=p['sl'] else p['sl'],'網')
            else: keep.append(p)
        pos=keep
    out=pd.DataFrame(log); out.attrs['open_left']=len(pos); return out
