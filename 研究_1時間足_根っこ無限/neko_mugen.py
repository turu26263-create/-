"""1時間足だけ:921/219・ポン(遅行21)・竿の根っこ → 斥候4、押し目買い8 無限リーチ。数字は全部【置き換え】。"""
import os, sys, itertools, time, numpy as np, pandas as pd
from numba import njit
M5=os.environ.get('M5','/tmp/claude-0/-home-user--/7cce787f-40b8-5d7f-af9d-9068bd24ecc6/scratchpad/data/r/forex/usdjpy/USDJPY_M5.csv')
def load():
    d=pd.read_csv(M5,sep='\t',parse_dates=['Time']).set_index('Time')
    d=d[~d.index.duplicated()]
    x=d.resample('1h',label='left',closed='left').agg({'Open':'first','High':'max','Low':'min','Close':'last'}).dropna()
    x.columns=list('ohlc'); return x
def prep(x, lag=21, K=8):
    m=x.c.rolling(21).mean(); s=x.c.rolling(21).std(ddof=0)
    e9=x.c.ewm(span=9,adjust=False).mean(); e21=x.c.ewm(span=21,adjust=False).mean()
    wp=(s/m).rolling(100).rank(pct=True)
    hl=x.h.shift(lag); ll=x.l.shift(lag)
    karami=((x.c<=hl)&(x.c>=ll)).astype(float)
    tame=karami.shift(1).rolling(12).sum()>=K
    pon_u=(x.c>hl)&(x.c.shift(1)<=hl.shift(1))&tame
    pon_d=(x.c<ll)&(x.c.shift(1)>=ll.shift(1))&tame
    y=pd.DataFrame(dict(o=x.o,h=x.h,l=x.l,c=x.c,m=m,s=s,e9=e9,e21=e21,wp=wp,pu=pon_u,pd=pon_d)).dropna()
    return y
@njit(cache=True)
def run(o,h,l,c,m,s,e9,e21,wp,pu,pdn,variant,sq,trailL,spr,sakite,tmode):
    n=len(o); MAXP=200
    out=np.zeros((20000,6)); k=0          # 入り足,出足,向き,単位,ピップ×単位,種類(0斥候/1押し目)
    pe=np.zeros(MAXP); pst=np.zeros(MAXP); pu_=np.zeros(MAXP); pi=np.zeros(MAXP,np.int64); pk=np.zeros(MAXP); np_=0
    d=0; touched=False; armed=True; trail=False; nadd=0
    for i in range(130,n-1):
        # ---- 足 i の中:網と3.5σ(前の足の帯で測る)
        if d!=0:
            up35=m[i-1]+3.5*s[i-1]; dn35=m[i-1]-3.5*s[i-1]
            hit35=(d>0 and h[i]>=up35) or (d<0 and l[i]<=dn35)
            j=0
            while j<np_:
                st=pst[j]; ex=np.nan
                if st!=0:
                    if d>0 and l[i]<=st: ex=min(st,o[i])
                    if d<0 and h[i]>=st: ex=max(st,o[i])
                if np.isnan(ex) and hit35: ex=up35 if d>0 else dn35
                if not np.isnan(ex):
                    out[k,0]=pi[j];out[k,1]=i;out[k,2]=d;out[k,3]=pu_[j];out[k,4]=pu_[j]*((ex-pe[j])*d/0.01-spr);out[k,5]=pk[j];k+=1
                    pe[j]=pe[np_-1];pst[j]=pst[np_-1];pu_[j]=pu_[np_-1];pi[j]=pi[np_-1];pk[j]=pk[np_-1];np_-=1
                else: j+=1
            if np_==0: d=0
        # ---- 足 i の終わりで判断 → i+1 の始値で動く
        if d!=0:
            x219=(d>0 and e9[i]<e21[i] and e9[i-1]>=e21[i-1]) or (d<0 and e9[i]>e21[i] and e9[i-1]<=e21[i-1])
            if x219:
                for j in range(np_):
                    ex=o[i+1]
                    out[k,0]=pi[j];out[k,1]=i+1;out[k,2]=d;out[k,3]=pu_[j];out[k,4]=pu_[j]*((ex-pe[j])*d/0.01-spr);out[k,5]=pk[j];k+=1
                np_=0; d=0; continue
            if d*(c[i]-m[i])>2*s[i] and (tmode==0 or nadd>0): trail=True
            # ひげ先(直近 trailL 本)
            if d>0:
                tip=l[i]
                for q in range(1,trailL): tip=min(tip,l[i-q])
            else:
                tip=h[i]
                for q in range(1,trailL): tip=max(tip,h[i-q])
            for j in range(np_):
                if pk[j]==1 or trail:
                    if pst[j]==0: pst[j]=tip
                    elif d>0: pst[j]=max(pst[j],tip)
                    else: pst[j]=min(pst[j],tip)
            # 竿先(帯の外で幅が2本続けて縮む)なら足さない
            sk = sakite and d*(c[i]-m[i])>2*s[i] and s[i]<s[i-1] and s[i-1]<s[i-2]
            # 押し目:21(指数)に触れたら構え、9の向こうで確定したら足す
            if (d>0 and l[i]<=e21[i]) or (d<0 and h[i]>=e21[i]): touched=True
            if not armed:
                if (d>0 and l[i]>e9[i]) or (d<0 and h[i]<e9[i]): armed=True
            if touched and armed and (not sk) and d*(c[i]-e9[i])>0 and np_<MAXP:
                pe[np_]=o[i+1]; pst[np_]=0; pu_[np_]=8; pi[np_]=i+1; pk[np_]=1; np_+=1
                touched=False; armed=False; nadd+=1
        else:
            # 斥候の入り
            for dd in (1,-1):
                cross=(dd>0 and e9[i]>e21[i] and e9[i-1]<=e21[i-1]) or (dd<0 and e9[i]<e21[i] and e9[i-1]>=e21[i-1])
                align=dd*(e9[i]-e21[i])>0
                pon=False
                for q in range(0,4):
                    if (dd>0 and pu[i-q]) or (dd<0 and pdn[i-q]): pon=True
                sqz=False
                for q in range(1,13):
                    if wp[i-q]<sq: sqz=True
                root=sqz and dd*(c[i]-m[i])>2*s[i] and dd*(c[i-1]-m[i-1])<=2*s[i-1]
                ok=False
                if variant==1: ok=root and align
                elif variant==2: ok=root and pon
                elif variant==3: ok=root and pon and align
                elif variant==4: ok=cross and pon
                elif variant==5: ok=((dd>0 and pu[i]) or (dd<0 and pdn[i])) and align
                if ok:
                    d=dd; pe[0]=o[i+1]; pst[0]=0; pu_[0]=4; pi[0]=i+1; pk[0]=0; np_=1
                    touched=False; armed=True; trail=False; nadd=0
                    break
    return out[:k]
NAMES={1:'根っこ+921',2:'根っこ+ポン',3:'根っこ+ポン+921',4:'921交差+ポン',5:'ポン+921向き'}
def score(t):
    if len(t)==0: return (0,0,0.0,0)
    g=t[:,4][t[:,4]>0].sum(); b=-t[:,4][t[:,4]<0].sum()
    return (int((t[:,5]==0).sum()), int(t[:,4].sum()), round(g/b,2) if b>0 else 9.0, int(t[:,3].sum()))
if __name__=='__main__':
    y=prep(load()); yr=y.index.year.values
    A=[y[k].values.astype(np.float64) for k in ('o','h','l','c','m','s','e9','e21','wp')]
    P=[y.pu.values.astype(np.bool_), y.pd.values.astype(np.bool_)]
    t0=time.time(); rows=[]
    for v,sq,L,sk,tm,spr in itertools.product([1,2,3,4,5],[0.2,0.3,0.4],[1,2,3],[False,True],[0,1],[0.5,1.0]):
        t=run(*A,*P,v,sq,L,spr,sk,tm)
        ey=yr[t[:,0].astype(int)] if len(t) else np.array([])
        r=dict(v=v,sq=sq,L=L,sk=sk,tm=tm,spr=spr)
        for Y in (2021,2022,2023): r[Y]=score(t[ey==Y])
        rows.append(r)
    print(f'{len(rows)}通り {time.time()-t0:.1f}秒')
    pd.to_pickle(pd.DataFrame(rows),'/tmp/claude-0/-home-user--/7cce787f-40b8-5d7f-af9d-9068bd24ecc6/scratchpad/neko.pkl')
