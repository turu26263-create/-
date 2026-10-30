import sys
import sys; sys.path.insert(0,"/home/user/-/EA_5分足ひんぱん")
import numpy as np,pandas as pd
from kenkyu_kousoku import sim,summary
d=pd.read_csv(sys.argv[1] if len(sys.argv)>1 else "USDJPY_M5.csv",sep="\t",parse_dates=["Time"])
df=d[["Open","High","Low","Close"]].astype(float);df.columns=list("ohlc");df.index=d.Time  # UTC
jst=df.index+pd.Timedelta(hours=9)
IS=df.index.year<=2022
# 時間ごとのくせ:JSTの30分ごとに、その後60分の値動き(ピップ)
ret=(df.o.shift(-12)-df.o)/0.01
key=jst.hour*100+(jst.minute//30)*30
t=pd.DataFrame({"k":key,"r":ret,"y":df.index.year,"wd":jst.dayofweek})
t=t[t.k%100==t.k%100]  # all
g=t[(jst.minute%30==0)].groupby(["k","y"]).r.mean().unstack()
g["t21_22"]=t[(jst.minute%30==0)&(t.y<=2022)].groupby("k").r.apply(lambda x:x.mean()/x.std()*np.sqrt(len(x)))
print(g.round(2).sort_values("t21_22").to_string())
