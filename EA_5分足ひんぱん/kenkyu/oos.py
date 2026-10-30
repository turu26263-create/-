import sys; sys.path.insert(0,"/home/user/-/EA_5分足ひんぱん")
import numpy as np,pandas as pd
from kenkyu_kousoku import sim,summary
d=pd.read_csv(sys.argv[1] if len(sys.argv)>1 else "USDJPY_M5.csv",sep="\t",parse_dates=["Time"])
df=d[["Open","High","Low","Close"]].astype(float);df.columns=list("ohlc");df.index=d.Time
o,h,l,c=df.o,df.h,df.l,df.c
tr=pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1);atr=tr.rolling(14).mean().shift().values
uh=df.index.hour
for N in (24,36,48,72):
  hi=h.rolling(N).max().shift();lo=l.rolling(N).min().shift()
  s=np.where((c>hi).shift().fillna(False).values,1,np.where((c<lo).shift().fillna(False).values,-1,0))
  s=np.where((uh>=7)&(uh<17),s,0)
  for slm,tpm,mb in ((2,4,48),(3,4,48),(3,3,48),(3,5,48),(3,4,24),(3,4,96)):
    for sp in (0.5,1.0):
      t=sim(df,s,slm*atr,tpm*atr,mb,sp)
      print(summary(t,f"N{N} sl{slm} tp{tpm} mb{mb} spr{sp}"))
