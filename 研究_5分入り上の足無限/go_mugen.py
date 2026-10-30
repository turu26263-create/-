"""5分で入り、1時間・4時間を見て無限リーチ(たくちん「ごぶんではいって一時間よ時間みたら無限リーチつかえる」)。数字は全部【置き換え】。"""
import os, itertools, time, numpy as np, pandas as pd
from numba import njit
M5=os.environ.get('M5','/tmp/claude-0/-home-user--/7cce787f-40b8-5d7f-af9d-9068bd24ecc6/scratchpad/data/r/forex/usdjpy/USDJPY_M5.csv')
def load5():
    d=pd.read_csv(M5,sep='\t',parse_dates=['Time']).set_index('Time'); d=d[~d.index.duplicated()]
    d=d.rename(columns={'Open':'o','High':'h','Low':'l','Close':'c'})[['o','h','l','c']]; return d
def htf(d,rule,hours):
    x=d.resample(rule,label='left',closed='left').agg({'o':'first','h':'max','l':'min','c':'last'}).dropna()
    m=x.c.rolling(21).mean(); s=x.c.rolling(21).std(ddof=0)
    e9=x.c.ewm(span=9,adjust=False).mean(); e21=x.c.ewm(span=21,adjust=False).mean()
    f=pd.DataFrame(dict(M=m,S=s,E9=e9,E21=e21,H=x.h,L=x.l,C=x.c))
    f['X']=np.sign(e9-e21).diff().fillna(0)/2
    f.index=f.index+pd.Timedelta(hours=hours)          # 確定した時刻
    return f
def build(d):
    e9=d.c.ewm(span=9,adjust=False).mean(); e21=d.c.ewm(span=21,adjust=False).mean()
    z=d.assign(e9=e9,e21=e21)
    ct=d.index+pd.Timedelta(minutes=5)                  # 5分足の確定時刻
    for nm,rule,hh in (('h1','1h',1),('h4','4h',4)):
        f=htf(d,rule,hh)
        lv=f.drop(columns='X').reindex(ct,method='ffill'); lv.index=d.index
        ev=f.X.reindex(ct).fillna(0); ev.index=d.index
        nb=pd.Series(ct.isin(f.index),index=d.index)     # その5分足で上の足が確定した
        for col in lv.columns: z[f'{nm}{col}']=lv[col].values
        z[f'{nm}X']=ev.values; z[f'{nm}NB']=nb.values
    return z.dropna()
@njit(cache=True)
def run(o,h,l,c,e9,e21, M1,S1,E91,E211,H1,L1,NB1, M4,S4,E94,E214,X4, lvl,stl,scout,tr,spr,neru=0.0):
    n=len(o); MAXP=400; out=np.zeros((60000,6)); k=0
    pe=np.zeros(MAXP); pst=np.zeros(MAXP); pu_=np.zeros(MAXP); pi=np.zeros(MAXP,np.int64); pk=np.zeros(MAXP); np_=0
    d=0; touched=False; armed=True; trail=False
    h1hist=np.zeros(8); l1hist=np.zeros(8)   # 直近の1時間足のひげ先
    for i in range(300,n-1):
        if NB1[i]:
            for q in range(7,0,-1): h1hist[q]=h1hist[q-1]; l1hist[q]=l1hist[q-1]
            h1hist[0]=H1[i]; l1hist[0]=L1[i]
        # 足の中:網と4時間3.5σ
        if np_>0:
            up=M4[i-1]+3.5*S4[i-1]; dn=M4[i-1]-3.5*S4[i-1]
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
        al=0
        sl4=(E214[i]-E214[i-48])/S4[i] if S4[i]>0 else 0.0   # 4時間21の傾き(4時間足1本ぶん、σ単位)
        if E94[i]>E214[i] and E91[i]>E211[i] and sl4>=neru: al=1
        if E94[i]<E214[i] and E91[i]<E211[i] and -sl4>=neru: al=-1
        if d!=0 and X4[i]==-d:     # 4時間の219(921)→全部降りて流れ終わり
            for j in range(np_):
                out[k,0]=pi[j];out[k,1]=i+1;out[k,2]=d;out[k,3]=pu_[j];out[k,4]=pu_[j]*((o[i+1]-pe[j])*d/0.01-spr);out[k,5]=pk[j];k+=1
            np_=0; d=0
        if d==0 and al!=0:
            d=al; touched=False; armed=True; trail=False
            if scout==1: touched=True   # 流れの始めの5分921を斥候に
        if d==0: continue
        # ひげ先(1時間足 stl 本)
        tip=0.0
        if d>0:
            tip=l1hist[0]
            for q in range(1,stl): tip=min(tip,l1hist[q])
        else:
            tip=h1hist[0]
            for q in range(1,stl): tip=max(tip,h1hist[q])
        if NB1[i]:
            if tr==1 and d*(c[i]-(M1[i]+d*2*S1[i]))>0: trail=True
            for j in range(np_):
                if pk[j]==1 or trail:
                    if pst[j]==0: pst[j]=tip
                    elif d>0: pst[j]=max(pst[j],tip)
                    else: pst[j]=min(pst[j],tip)
        lv21=E211[i] if lvl==1 else E214[i]
        if (d>0 and l[i]<=lv21) or (d<0 and h[i]>=lv21): touched=True
        if not armed and ((d>0 and l[i]>E91[i]) or (d<0 and h[i]<E91[i])): armed=True
        x5=(d>0 and e9[i]>e21[i] and e9[i-1]<=e21[i-1]) or (d<0 and e9[i]<e21[i] and e9[i-1]>=e21[i-1])
        if touched and armed and x5 and al==d and np_<MAXP:
            first=(np_==0 and scout==1)
            pe[np_]=o[i+1]; pu_[np_]=4 if first else 8; pk[np_]=0 if first else 1
            pst[np_]=0 if first else tip; pi[np_]=i+1; np_+=1
            touched=False; armed=False
    return out[:k]
def arr(z):
    return ([z[k].values.astype(np.float64) for k in ('o','h','l','c','e9','e21','h1M','h1S','h1E9','h1E21','h1H','h1L')]+[z.h1NB.values.astype(np.bool_)]
            +[z[k].values.astype(np.float64) for k in ('h4M','h4S','h4E9','h4E21','h4X')])
def score(t):
    if len(t)==0: return (0,0,0.0,0)
    g=t[:,4][t[:,4]>0].sum(); b=-t[:,4][t[:,4]<0].sum()
    return (len(t), int(t[:,4].sum()), round(g/b,2) if b>0 else 9.0, int(t[:,3].sum()))
if __name__=='__main__':
    z=build(load5()); yr=z.index.year.values; A=arr(z); rows=[]; t0=time.time()
    for lvl,stl,scout,tr,spr in itertools.product([1,4],[1,2,3,4],[0,1],[0,1],[0.5,1.0]):
        t=run(*A,lvl,stl,scout,tr,spr); ey=yr[t[:,0].astype(int)] if len(t) else np.array([])
        r=dict(lvl=lvl,stl=stl,scout=scout,tr=tr,spr=spr)
        for Y in (2021,2022,2023):
            tt=t[ey==Y]; r[Y]=score(tt); r[f'押{Y}']=int((tt[:,5]==1).sum()); r[f'押益{Y}']=int(tt[tt[:,5]==1,4].sum())
        rows.append(r)
    print(f'{len(rows)}通り {time.time()-t0:.1f}秒')
    pd.to_pickle(pd.DataFrame(rows),'/tmp/claude-0/-home-user--/7cce787f-40b8-5d7f-af9d-9068bd24ecc6/scratchpad/go.pkl')
