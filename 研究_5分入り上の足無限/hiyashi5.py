"""向き=日足。押し=日足21 / 1時間21 / 両方。入り=5分921。冷やし4番の骨に1時間の浅い押しを足すと上乗せか。数字は全部【置き換え】。"""
import itertools, numpy as np, pandas as pd
from numba import njit
from go_mugen import load5, htf, score
def build(d):
    e9=d.c.ewm(span=9,adjust=False).mean(); e21=d.c.ewm(span=21,adjust=False).mean()
    z=d.assign(e9=e9,e21=e21); ct=d.index+pd.Timedelta(minutes=5)
    for nm,rule,hh in (('h1','1h',1),('dd','1D',24)):
        f=htf(d,rule,hh)
        lv=f.drop(columns='X').reindex(ct,method='ffill'); lv.index=d.index
        ev=f.X.reindex(ct).fillna(0); ev.index=d.index
        for col in lv.columns: z[f'{nm}{col}']=lv[col].values
        z[f'{nm}X']=ev.values; z[f'{nm}NB']=ct.isin(f.index)
    return z.dropna()
@njit(cache=True)
def run(o,h,l,c,e9,e21,E91,E211,H1,L1,NB1,MD,SD,E9D,E21D,HD,LD,CD,XD,NBD,useD,useH,stmode,stl,spr):
    n=len(o); MAXP=600; out=np.zeros((80000,6)); k=0
    pe=np.zeros(MAXP); pst=np.zeros(MAXP); pu_=np.zeros(MAXP); pi=np.zeros(MAXP,np.int64); pk=np.zeros(MAXP); np_=0
    d=0; tD=False; tH=False; armD=True; armH=True; trail=False
    h1h=np.zeros(8); l1h=np.zeros(8)
    for i in range(300,n-1):
        if NB1[i]:
            for q in range(7,0,-1): h1h[q]=h1h[q-1]; l1h[q]=l1h[q-1]
            h1h[0]=H1[i]; l1h[0]=L1[i]
        if np_>0:
            up=MD[i-1]+3.5*SD[i-1]; dn=MD[i-1]-3.5*SD[i-1]
            hit=(d>0 and h[i]>=up) or (d<0 and l[i]<=dn)
            j=0
            while j<np_:
                st=pst[j]; ex=np.nan
                if st!=0:
                    if d>0 and l[i]<=st: ex=min(st,o[i])
                    if d<0 and h[i]>=st: ex=max(st,o[i])
                if np.isnan(ex) and hit: ex=up if d>0 else dn
                if not np.isnan(ex):
                    out[k,0]=pi[j];out[k,1]=i;out[k,2]=d;out[k,3]=pu_[j];out[k,4]=pu_[j]*((ex-pe[j])*d/0.01-spr);out[k,5]=pk[j];k+=1
                    pe[j]=pe[np_-1];pst[j]=pst[np_-1];pu_[j]=pu_[np_-1];pi[j]=pi[np_-1];pk[j]=pk[np_-1];np_-=1
                else: j+=1
        # 日足の921/219:全部降りて逆の斥候
        if XD[i]!=0:
            nd=int(XD[i])
            if d!=0 and nd==-d:
                for j in range(np_):
                    out[k,0]=pi[j];out[k,1]=i+1;out[k,2]=d;out[k,3]=pu_[j];out[k,4]=pu_[j]*((o[i+1]-pe[j])*d/0.01-spr);out[k,5]=pk[j];k+=1
                np_=0
            if nd!=d or np_==0:
                d=nd; tD=False; tH=False; armD=True; armH=True; trail=False
                pe[np_]=o[i+1]; pst[np_]=0; pu_[np_]=4; pi[np_]=i+1; pk[np_]=0; np_+=1
            continue
        if d==0: continue
        # 網の元
        if stmode==0: tip=LD[i] if d>0 else HD[i]
        else:
            if d>0:
                tip=l1h[0]
                for q in range(1,stl): tip=min(tip,l1h[q])
            else:
                tip=h1h[0]
                for q in range(1,stl): tip=max(tip,h1h[q])
        if NBD[i] and d*(CD[i]-(MD[i]+d*2*SD[i]))>0: trail=True
        upd = NBD[i] if stmode==0 else NB1[i]
        if upd or (trail and NBD[i]):
            ttip = (LD[i] if d>0 else HD[i]) if (trail and NBD[i]) else tip
            for j in range(np_):
                if pk[j]==1 or trail:
                    t2 = ttip if trail else tip
                    if pst[j]==0: pst[j]=t2
                    elif d>0: pst[j]=max(pst[j],t2)
                    else: pst[j]=min(pst[j],t2)
        if useD and ((d>0 and l[i]<=E21D[i]) or (d<0 and h[i]>=E21D[i])): tD=True
        if useH and ((d>0 and l[i]<=E211[i]) or (d<0 and h[i]>=E211[i])): tH=True
        if not armD and ((d>0 and c[i]>E9D[i]) or (d<0 and c[i]<E9D[i])): armD=True
        if not armH and ((d>0 and l[i]>E91[i]) or (d<0 and h[i]<E91[i])): armH=True
        x5=(d>0 and e9[i]>e21[i] and e9[i-1]<=e21[i-1]) or (d<0 and e9[i]<e21[i] and e9[i-1]>=e21[i-1])
        if x5 and np_<MAXP and ((tD and armD) or (tH and armH)):
            kind=1 if (tD and armD) else 2
            pe[np_]=o[i+1]; pu_[np_]=8; pk[np_]=kind; pst[np_]=tip; pi[np_]=i+1; np_+=1
            if kind==1: tD=False; armD=False
            else: tH=False; armH=False
    return out[:k]
def arr(z):
    f=lambda ks:[z[k].values.astype(np.float64) for k in ks]
    return (f(('o','h','l','c','e9','e21','h1E9','h1E21','h1H','h1L'))+[z.h1NB.values.astype(np.bool_)]
            +f(('ddM','ddS','ddE9','ddE21','ddH','ddL','ddC','ddX'))+[z.ddNB.values.astype(np.bool_)])
if __name__=='__main__':
    z=build(load5()); yr=z.index.year.values; A=arr(z)
    NM={(1,0):'冷やし(日足21押し)',(1,1):'冷やし+1時間21押し',(0,1):'1時間21押しだけ'}
    print('向き=日足 入り=5分921 単位:斥候4・押し目8 / 1.0ピップ / ピップ×単位')
    for (uD,uH),nm in NM.items():
        for stm,stl in ((0,0),(1,3),(1,6)):
            t=run(*A,uD,uH,stm,stl,1.0); ey=yr[t[:,0].astype(int)]
            line=[]
            for Y in (2021,2022,2023):
                tt=t[ey==Y]; sc=score(tt)
                line.append(f"{Y} {sc[1]:+6d}(比{sc[2]} 斥{int((tt[:,5]==0).sum())} 日{int((tt[:,5]==1).sum())} 時{int((tt[:,5]==2).sum())})")
            o_=np.argsort(t[:,1]); eq=np.cumsum(t[o_,4]); dd=(np.maximum.accumulate(eq)-eq).max()
            print(f" {nm:12s} 網={'前の日のひげ先' if stm==0 else f'1時間{stl}本'}: "+'  '.join(line)+f"  3年の落ち込み{dd:.0f}")
