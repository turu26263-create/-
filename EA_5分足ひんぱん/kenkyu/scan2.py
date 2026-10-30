import sys,itertools; sys.path.insert(0,"/home/user/-/EA_5分足ひんぱん")
import numpy as np,pandas as pd
from kenkyu_kousoku import sim
d=pd.read_csv(sys.argv[1] if len(sys.argv)>1 else "USDJPY_M5.csv",sep="\t",parse_dates=["Time"])
df=d[["Open","High","Low","Close"]].astype(float);df.columns=list("ohlc");df.index=d.Time
o,h,l,c=df.o,df.h,df.l,df.c
tr=pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1);atr=tr.rolling(14).mean()
uh=df.index.hour
h1=c.resample("1h").last().dropna();e50=h1.ewm(span=50,adjust=False).mean()
h1d=pd.Series(np.where((h1>e50)&(e50>e50.shift()),1,np.where((h1<e50)&(e50<e50.shift()),-1,0)),index=h1.index+pd.Timedelta(hours=1)).reindex(df.index,method="ffill").fillna(0).values
IS=(df.index.year<=2022)
dfi=df[IS]
def ev(sig,slm,tpm,mb,name):
    s=np.where(IS,sig,0)
    t=sim(df,s,slm*atr.shift().values,tpm*atr.shift().values,mb,0.5)
    t=t[t.t.dt.year<=2022]
    if len(t)<300: return None
    p=t.pips;y=[t[t.t.dt.year==Y].pips.sum() for Y in (2021,2022)]
    return dict(name=name,n=len(t),pips=p.sum(),pf=p[p>0].sum()/-p[p<0].sum(),y21=y[0],y22=y[1],avg=p.mean())
res=[]
sh=lambda x:x.shift().values  # 確定足(1本前)の値を、今の足の始値で使う
for N in (12,24,48):
  hi=h.rolling(N).max().shift();lo=l.rolling(N).min().shift()
  up=(c>hi);dn=(c<lo)
  for filt in ("none","h1","sess","h1sess"):
    m=np.ones(len(df),bool)
    s=np.where(sh(up)==True,1,np.where(sh(dn)==True,-1,0))
    if "h1" in filt: s=np.where(s==h1d,s,0)
    if "sess" in filt: s=np.where((uh>=7)&(uh<17),s,0)
    for slm,tpm,mb in itertools.product((1,2,3),(1,2,4),(12,48)):
      r=ev(s,slm,tpm,mb,f"F1抜け N{N} {filt} sl{slm} tp{tpm} mb{mb}");r and res.append(r)
for z in (2.0,2.5,3.0):
  mid=c.rolling(20).mean();sd=c.rolling(20).std(ddof=0)
  for mode in ("close_out","reenter"):
    if mode=="close_out": up=c>mid+z*sd;dn=c<mid-z*sd
    else: up=(h>=mid+z*sd)&(c<mid+z*sd);dn=(l<=mid-z*sd)&(c>mid-z*sd)
    for filt in ("all","quiet","sess","contra_h1no"):
      s=np.where(sh(up)==True,-1,np.where(sh(dn)==True,1,0))
      if filt=="quiet": s=np.where((uh>=21)|(uh<6),s,0)
      if filt=="sess": s=np.where((uh>=7)&(uh<17),s,0)
      if filt=="contra_h1no": s=np.where(s!=-h1d,s,0)
      for slm,tpm,mb in itertools.product((1,2,3),(0.5,1,2),(6,24)):
        r=ev(s,slm,tpm,mb,f"F2戻し z{z} {mode} {filt} sl{slm} tp{tpm} mb{mb}");r and res.append(r)
R=pd.DataFrame(res);R.to_csv("scan2.csv",index=False)
ok=R[(R.y21>0)&(R.y22>0)].sort_values("pf",ascending=False)
print(len(R),"通り / 両年プラス",len(ok));print(ok.head(25).round(2).to_string())
