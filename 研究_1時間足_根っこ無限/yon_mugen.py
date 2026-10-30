"""入りは1時間(根っこ+ポン)で斥候4、持つのは4時間(21押し→1時間921で8を無限に、4時間219・±3.5σで降りる)。数字は全部【置き換え】。"""
import itertools, time, numpy as np, pandas as pd
from numba import njit
from neko_mugen import load, prep, score
def four(raw):
    x=raw.resample('4h',label='left',closed='left').agg({'o':'first','h':'max','l':'min','c':'last'}).dropna()
    m=x.c.rolling(21).mean(); s=x.c.rolling(21).std(ddof=0)
    e9=x.c.ewm(span=9,adjust=False).mean(); e21=x.c.ewm(span=21,adjust=False).mean()
    f=pd.DataFrame(dict(M=m,S=s,E9=e9,E21=e21,H=x.h,L=x.l,C=x.c))
    f['X']=np.sign(e9-e21).diff().fillna(0)/2   # +1=921 / -1=219 が確定した4時間足
    f.index=f.index+pd.Timedelta(hours=4)       # 確定した時刻
    return f
def join(y,f):
    close_t=y.index+pd.Timedelta(hours=1)        # 1時間足の確定時刻
    lv=f.drop(columns='X').reindex(close_t,method='ffill'); lv.index=y.index
    ev=f.X.reindex(close_t).fillna(0); ev.index=y.index
    z=y.join(lv); z['X']=ev.values
    return z.dropna()
@njit(cache=True)
def tipf(L4,H4,E21,S,i,d,stm):
    # 押し目の網:0=前の4時間足のひげ先/1=4時間足3本のひげ先/2=4時間21の1σ向こう
    if stm==0: return L4[i] if d>0 else H4[i]
    if stm==1:
        if d>0: return min(L4[i],min(L4[i-4],L4[i-8]))
        return max(H4[i],max(H4[i-4],H4[i-8]))
    return E21[i]-d*S[i]
@njit(cache=True)
def run(o,h,l,c,m,s,e9,e21,wp,pu,pdn,M,S,E9,E21,H4,L4,C4,X,sq,spr,tmode,conf,stm=0):
    n=len(o); MAXP=300
    out=np.zeros((20000,6)); k=0
    pe=np.zeros(MAXP); pst=np.zeros(MAXP); pu_=np.zeros(MAXP); pi=np.zeros(MAXP,np.int64); pk=np.zeros(MAXP); np_=0
    d=0; touched=False; armed=True; trail=False; nadd=0
    for i in range(130,n-1):
        if d!=0:
            up35=M[i-1]+3.5*S[i-1]; dn35=M[i-1]-3.5*S[i-1]
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
        if d!=0:
            if X[i]==-d:      # 4時間の219(921)が確定 → 全部降りる
                for j in range(np_):
                    out[k,0]=pi[j];out[k,1]=i+1;out[k,2]=d;out[k,3]=pu_[j];out[k,4]=pu_[j]*((o[i+1]-pe[j])*d/0.01-spr);out[k,5]=pk[j];k+=1
                np_=0; d=0; continue
            if X[i]!=0 or True:
                pass
            newbar4 = (i>0 and C4[i]!=C4[i-1])        # 4時間足が確定した1時間足
            if newbar4 and d*(C4[i]-M[i])>2*S[i] and (tmode==0 or nadd>0): trail=True
            if newbar4:
                tip=tipf(L4,H4,E21,S,i,d,stm)
                for j in range(np_):
                    if pk[j]==1 or trail:
                        if pst[j]==0: pst[j]=tip
                        elif d>0: pst[j]=max(pst[j],tip)
                        else: pst[j]=min(pst[j],tip)
            if (d>0 and l[i]<=E21[i]) or (d<0 and h[i]>=E21[i]): touched=True
            if not armed:
                if (d>0 and l[i]>E9[i]) or (d<0 and h[i]<E9[i]): armed=True
            if conf==0: ok=(d>0 and e9[i]>e21[i] and e9[i-1]<=e21[i-1]) or (d<0 and e9[i]<e21[i] and e9[i-1]>=e21[i-1])
            else: ok=d*(c[i]-e9[i])>0 and d*(e9[i]-e21[i])>0
            if touched and armed and ok and np_<MAXP:
                pe[np_]=o[i+1]; pst[np_]=tipf(L4,H4,E21,S,i,d,stm); pu_[np_]=8; pi[np_]=i+1; pk[np_]=1; np_+=1
                touched=False; armed=False; nadd+=1
        else:
            for dd in (1,-1):
                pon=False
                for q in range(0,4):
                    if (dd>0 and pu[i-q]) or (dd<0 and pdn[i-q]): pon=True
                sqz=False
                for q in range(1,13):
                    if wp[i-q]<sq: sqz=True
                root=sqz and dd*(c[i]-m[i])>2*s[i] and dd*(c[i-1]-m[i-1])<=2*s[i-1]
                if root and pon:
                    d=dd; pe[0]=o[i+1]; pst[0]=0; pu_[0]=4; pi[0]=i+1; pk[0]=0; np_=1
                    touched=False; armed=True; trail=False; nadd=0
                    break
    return out[:k]
def arrays(z):
    a=[z[k].values.astype(np.float64) for k in ('o','h','l','c','m','s','e9','e21','wp')]
    b=[z.pu.values.astype(np.bool_), z.pd.values.astype(np.bool_)]
    c=[z[k].values.astype(np.float64) for k in ('M','S','E9','E21','H','L','C','X')]
    return a+b+c
if __name__=='__main__':
    raw=load(); f=four(raw); rows=[]; t0=time.time()
    for K in (5,6,7,8):
        z=join(prep(raw,K=K),f); yr=z.index.year.values; A=arrays(z)
        for sq,tm,cf,spr in itertools.product([0.2,0.3,0.4],[0,1],[0,1],[0.5,1.0]):
            t=run(*A,sq,spr,tm,cf); ey=yr[t[:,0].astype(int)] if len(t) else np.array([])
            r=dict(K=K,sq=sq,tm=tm,cf=cf,spr=spr)
            for Y in (2021,2022,2023): r[Y]=score(t[ey==Y]); r[f'押{Y}']=int(((t[:,5]==1)&(ey==Y)).sum()) if len(t) else 0
            rows.append(r)
    print(f'{len(rows)}通り {time.time()-t0:.1f}秒')
    pd.to_pickle(pd.DataFrame(rows),'/tmp/claude-0/-home-user--/7cce787f-40b8-5d7f-af9d-9068bd24ecc6/scratchpad/yon.pkl')
