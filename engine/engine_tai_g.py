# 鯛の刺身エンジン(足を選べる版)。big=縄1(9上)・縄4改(21上)・縄8(角度)の足/mid=縄2(21上)の足/small=入る足/exit=9割れで降りる足
# 4h/1h/5min/1h が完成形(engine_tai2 と同じ)。日足は NY の17時(EST)で区切る=業者の日足と同じ区切り【置き換え】
import sys,numpy as np,pandas as pd
sys.path.insert(0,__file__.rsplit('/',1)[0]); from engine_ichi import ema,angle21
from engine_tai import load
from engine_tai2 import stat
AGG=dict(o='first',h='max',l='min',c='last')
def bars(m1,tf):
    if tf=='1D': b=m1.resample('24h',offset='17h').agg(AGG).dropna(); b['k']=b.index+pd.Timedelta('1D')
    else: b=m1.resample(tf).agg(AGG).dropna(); b['k']=b.index+pd.Timedelta(tf)
    return b
def attach(x,b,cols,pre):
    a=b[['k']+cols].rename(columns={c:pre+c for c in cols}).rename(columns={'k':pre+'k'}).sort_values(pre+'k')
    y=pd.merge_asof(x.reset_index().rename(columns={'index':'t'}).sort_values('kakutei'),a,left_on='kakutei',right_on=pre+'k',direction='backward').set_index('t'); y.index.name=None; return y
def prep(m1,big,mid,small,LAG=21):
    m=bars(m1,small); m['kakutei']=m.k
    m['e9']=ema(m.c,9); m['e21']=ema(m.c,21); m['md']=m.c.rolling(20).mean(); m['sd']=m.c.rolling(20).std(ddof=0)
    m['hL']=m.h.shift(LAG); m['lL']=m.l.shift(LAG)
    B=bars(m1,big); B['e9']=ema(B.c,9); B['e21']=ema(B.c,21); B['ang']=angle21(B)
    M=bars(m1,mid); M['e21']=ema(M.c,21)
    M=attach(M.assign(kakutei=M.k),B,['c','e9'],'f_')
    M['pb']=(M.f_c>M.f_e9)&(M.c>M.e21); M['ps']=(M.f_c<M.f_e9)&(M.c<M.e21)
    x=attach(m,M,['pb','ps'],'g_'); x=attach(x,B,['c','e21','ang'],'q_')
    return x.drop(columns=['k'])
def add_exit(x,m1,tf):
    b=bars(m1,tf); b['e9']=ema(b.c,9); mid=(b.o+b.c)/2
    b['wb']=(mid<b.e9)&(b.c<b.e9); b['ws']=(mid>b.e9)&(b.c>b.e9)
    x=x.drop(columns=[c for c in x.columns if c.startswith('w_')]); return attach(x,b,['wb','ws'],'w_')
def signals(x,d,sao=2.0,n8=False):
    up=x.e9>x.e21; up1=x.e9.shift()>x.e21.shift()
    if d>0: perm=x.g_pb.fillna(False).astype(bool); cross=up&~up1; side=up; kawa=x.c>x.md+x.sd; chi=x.c>x.hL; q=x.q_c>x.q_e21; ns=x.c<=x.md+sao*x.sd; ang=x.q_ang
    else:   perm=x.g_ps.fillna(False).astype(bool); cross=~up&up1; side=~up; kawa=x.c<x.md-x.sd; chi=x.c<x.lL; q=x.q_c<x.q_e21; ns=x.c>=x.md-sao*x.sd; ang=-x.q_ang
    e921=cross&perm; kai=perm&~perm.shift(1,fill_value=False)&side&~cross
    ent=((e921&kawa&chi)|(kai&q))&ns
    if n8: ent=ent&~(ang>55)
    return ent
def run(x,d,ent,spr=0.003):
    E=ent.values; W=(x.w_wb if d>0 else x.w_ws).fillna(False).astype(bool).values; K=x.w_k.values; O=x.o.values; T=x.index.values; tr=[]; pos=None
    for i in range(len(x)-1):
        if pos is None:
            if E[i]: pos=(i+1,O[i+1]+(spr if d>0 else 0))
        elif W[i] and K[i]>T[pos[0]]:
            j,px=pos; ex=O[i+1]-(0 if d>0 else spr); tr.append((T[j],px,T[i+1],ex,(ex-px)*100*d)); pos=None
    return pd.DataFrame(tr,columns=['ent','e','ext','x','pips'])
