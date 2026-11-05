# 照らし: 「4h 5>9>21>200 かつ 1h 5>9>21 が同じ向き」と、5分足の 5>9>21 を別の道で計算し直して全部の5分足で比べる
import os, glob, numpy as np, pandas as pd
from sim3 import *
m5,h1=load(); m=prep3(m5,h1,H1='ord')
dfs=[pd.read_csv(f,header=None,names=['d','t','o','h','l','c','v']) for f in sorted(glob.glob(os.environ.get('M1DIR','../dl/m1')+'/*.csv'))]
d=pd.concat(dfs); d.index=pd.to_datetime(d.d+' '+d.t,format='%Y.%m.%d %H:%M'); d=d[~d.index.duplicated()].sort_index()
def ema_loop(x,p):
    a=2/(p+1); o=np.empty(len(x)); o[0]=x[0]
    for i in range(1,len(x)): o[i]=a*x[i]+(1-a)*o[i-1]
    return o
def sigs(c, po):
    x=c.values; e={p:ema_loop(x,p) for p in (5,9,21,200)}; s=np.zeros(len(x),int)
    for i in range(len(x)):
        if po and i<200: continue
        u=e[5][i]>e[9][i]>e[21][i] and (not po or e[21][i]>e[200][i]); w=e[5][i]<e[9][i]<e[21][i] and (not po or e[21][i]<e[200][i])
        s[i]=1 if u else (-1 if w else 0)
    return s
def at(c, s, hours, idx):
    closed=(c.index+pd.Timedelta(hours=hours)).values; p=np.searchsorted(closed, idx.values, side='right')-1
    return np.where(p>=0, s[np.clip(p,0,None)], 0)
c4=d.c.resample('4h').last().dropna(); c1=d.c.resample('1h').last().dropna(); c5=d.c.resample('5min').last().dropna()
s4=at(c4,sigs(c4,True),4,m.index); s1=at(c1,sigs(c1,False),1,m.index)
ent=np.where(s1==s4, s4, 0)
s5=pd.Series(sigs(c5,False),index=c5.index).shift(1).reindex(m.index).values
print('5分足の数',len(m))
print('主(4h)の食い違い', int((s4!=m.trend.values).sum()))
print('入りの向き(4h×1h)の食い違い', int((ent!=m.ent.values).sum()))
print('5分足の並び(1本前)の食い違い', int((s5!=m['loc'].values).sum()))
print('入りの向きがある5分足の割合 上',round((ent==1).mean()*100,1),'% 下',round((ent==-1).mean()*100,1),'%')
