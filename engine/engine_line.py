# 延長線エンジン(たくちん 11-05「5分レンジの時 前の山とその前の山の頂点を結んで延長で傾き計算 上むき bb開き、延長線超えて損切りくったら、押し目買いにする、延長線と押し目買いの検証」)
# 山 = 5分足で両側K本より高い実体の頂点(谷は低い実体の底)。ひげ=魚のピチピチは無視(たくちん「川の向きと魚ピチピチと同じような感じ」)。右側K本が確定してから使う【置き換え K=3】
# 線は 川(帯の真ん中の3本の向き)と同じ向きの時だけ。同じ線での抜けは1回だけ
# 線 = 直近の5分レンジ(遅行21本前が12本中8本以上絡む)があった所で、前の山とその前の山を結んだ延長線(上向き)/ 谷と谷(下向き)
# 抜け = 線が向き側に傾き・帯(5分±2σの幅)が開いている・5分終値が延長線を越えて確定
# MODE 'A' 延長線で入る(損切り=直前の谷の下)/ 'B' 抜けた後の押し目で入る(無限リーチ)/ 'C' A で損切りを食ったら同じ抜けを B に切り替える
# 降り = 1時間9割れ。だまし回避 = 1h200の向き側(実体渡り切り)・1h21が逆向きなら入らない
import os, sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from engine_ichi import load, ema, atr14, bigbars, to_m5, PIP, angle21, karami
import numpy as np, pandas as pd
def prep(m5,h1,K=3,LAG=21):
    m=m5.copy(); idx=m.index; c=m.c; H=np.maximum(m.o.values,m.c.values); L=np.minimum(m.o.values,m.c.values); n=len(m)   # 山・谷は実体の頂点(ひげ=魚のピチピチは無視)
    e9,e21=ema(c,9),ema(c,21); mid=c.rolling(20).mean(); sd=c.rolling(20).std(ddof=0); w=(4*sd).values
    rng=(karami(m,LAG).rolling(12).sum()>=8).values
    rng_recent=pd.Series(rng).rolling(24).max().fillna(0).values>0             # 直近24本(2時間)の中にレンジがあった【置き換え】
    # 山・谷(右K本で確定)
    ph=np.zeros(n,bool); pl=np.zeros(n,bool)
    for i in range(K,n-K):
        if H[i]==H[i-K:i+K+1].max() and (H[i]>H[i-K:i]).all(): ph[i]=True
        if L[i]==L[i-K:i+K+1].min() and (L[i]<L[i-K:i]).all(): pl[i]=True
    brk=np.zeros(n); lineval=np.full(n,np.nan); stop=np.full(n,np.nan)
    peaks=[]; troughs=[]; used=set(); midv=mid.values
    C=c.values
    for i in range(n):
        j=i-K                                                                   # i の時点で確定している山・谷
        if j>=0 and ph[j]: peaks.append(j)
        if j>=0 and pl[j]: troughs.append(j)
        if not rng_recent[i] or i<1: continue
        opening=w[i]>w[i-1]; river=np.sign(midv[i]-midv[i-3])               # 川の向き=帯の真ん中の3本の向き
        if len(peaks)>=2 and (peaks[-2],peaks[-1]) not in used:
            a,b=peaks[-2],peaks[-1]; slope=(H[b]-H[a])/(b-a); v=H[b]+slope*(i-b); vp=H[b]+slope*(i-1-b)
            if slope>0 and river>0 and opening and C[i]>v and C[i-1]<=vp:
                brk[i]=1; lineval[i]=v; stop[i]=L[troughs[-1]] if troughs else np.nan; used.add((a,b))   # 同じ線は1回だけ
        if len(troughs)>=2 and (troughs[-2],troughs[-1]) not in used:
            a,b=troughs[-2],troughs[-1]; slope=(L[b]-L[a])/(b-a); v=L[b]+slope*(i-b); vp=L[b]+slope*(i-1-b)
            if slope<0 and river<0 and opening and C[i]<v and C[i-1]>=vp:
                brk[i]=-1; lineval[i]=v; stop[i]=H[peaks[-1]] if peaks else np.nan; used.add((a,b))
    m['brk']=pd.Series(brk,index=idx).shift(1); m['stop']=pd.Series(stop,index=idx).shift(1)   # 確定足で抜け → 次の足で動く
    pb=(m.l<=e21)&(c>e9)&(e9>e21)&(c<=mid+2*sd); ps=(m.h>=e21)&(c<e9)&(e9<e21)&(c>=mid-2*sd)
    m['pull']=pd.Series(np.where(pb,1,np.where(ps,-1,0)),index=idx).shift(1)
    hc=h1.c; e91=ema(hc,9); bm=(h1.o+hc)/2
    nine=pd.Series(np.where((bm>e91)&(hc>e91),1,np.where((bm<e91)&(hc<e91),-1,0)),index=h1.index)
    s200=ema(hc,200); ab=((hc>s200)&(bm>s200)).astype(int)-((hc<s200)&(bm<s200)).astype(int)
    for k,v in (('nine',nine),('s200',ab),('ang1',np.sign(angle21(h1)))): m[k]=to_m5(pd.Series(np.asarray(v,float),index=h1.index),'1h',idx)
    b4=bigbars(h1,'4h'); a=to_m5(atr14(b4),'4h',idx)
    m['chL']=m.h.rolling(22).max().shift(1)-3*a; m['chS']=m.l.rolling(22).min().shift(1)+3*a
    m['newh']=(idx.minute==0)
    return m.dropna(subset=['pull','nine','s200','ang1','chL','chS'])
def run(m,MODE='C',spr=0.3*PIP,MAXPOS=20,ADD=20.0):
    O,Hh,Ll=m.o.values,m.h.values,m.l.values; B=m.brk.fillna(0).values; ST=m.stop.values; P=m.pull.values; NN=m.nine.values; S2=m.s200.values; A1=m.ang1.values; NH=m.newh.values
    CL,CS=m.chL.values,m.chS.values; T=m.index
    pos=[]; log=[]; camp=0; mode=None; d0=0; prev_pull=0
    def cls(i,p,ex,why): log.append(dict(camp=p['camp'],n=p['n'],dir='買' if p['d']>0 else '売',kind=p['k'],open=p['ot'],entry=p['e'],close=T[i],exit=ex,why=why,pips=(ex-p['e'])/PIP*p['d'],i0=p['i0'],i1=i))
    def opn(i,d,k,sl=None):
        nonlocal camp
        px=O[i]+spr if d>0 else O[i]
        if sl is None or np.isnan(sl): sl=CL[i] if d>0 else CS[i]
        if d>0 and sl>=px: sl=px-10*PIP
        if d<0 and sl<=px: sl=px+10*PIP
        if not pos: camp+=1
        pos.append(dict(d=d,e=px,sl=sl,ot=T[i],camp=camp,n=len(pos)+1,k=k,i0=i,fixed=(k=='延長線')))
    for i in range(len(m)):
        if NH[i] and d0!=0 and int(NN[i])==-d0:                    # 1時間9割れ → 利確、その抜けは終わり
            for p in pos: cls(i,p,O[i] if p['d']>0 else O[i]+spr,'9割れ')
            pos=[]; d0=0; mode=None
        b=int(B[i]); ok=lambda d: int(S2[i])==d and int(A1[i])!=-d
        if b!=0 and ok(b) and (d0!=b):
            if pos:
                for p in pos: cls(i,p,O[i] if p['d']>0 else O[i]+spr,'逆の抜け')
                pos=[]
            d0=b
            if MODE in ('A','C'): opn(i,b,'延長線',ST[i]); mode='A'
            else: mode='B'
        pl=int(P[i])
        if d0!=0 and mode=='B' and pl==d0 and prev_pull!=d0 and ok(d0):
            if not pos: opn(i,d0,'押し目')
            elif len(pos)<MAXPOS:
                pxc=O[i] if d0>0 else O[i]+spr
                if d0*(pxc-pos[-1]['e'])>=ADD*PIP: opn(i,d0,'無限リーチ')
        prev_pull=pl
        for p in pos:
            if p['fixed']: continue
            d=p['d']; sl=CL[i] if d>0 else CS[i]
            if d>0 and sl>p['sl']+0.001 and sl<O[i]: p['sl']=sl
            if d<0 and sl<p['sl']-0.001 and sl>O[i]+spr: p['sl']=sl
        keep=[]; hit_a=False
        for p in pos:
            d=p['d']
            if d>0 and Ll[i]<=p['sl']: cls(i,p,O[i] if O[i]<=p['sl'] else p['sl'],'損切り' if p['fixed'] else '網'); hit_a|=p['fixed']
            elif d<0 and Hh[i]+spr>=p['sl']: cls(i,p,O[i]+spr if O[i]+spr>=p['sl'] else p['sl'],'損切り' if p['fixed'] else '網'); hit_a|=p['fixed']
            else: keep.append(p)
        pos=keep
        if hit_a:
            if MODE=='C': mode='B'                                  # 延長線で損切りを食ったら 押し目買いに切り替える
            else: d0=0; mode=None
    out=pd.DataFrame(log); out.attrs['open_left']=len(pos); return out
