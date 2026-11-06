# 鯛の刺身エンジン 2(買い・売り両方、降りの足・竿先の幅を変えられる)。縄の中身は engine_tai.py と同じ
# d=+1 買い / d=-1 売り(鏡うつし)。exit_tf=9割れを見る足。sao=竿先の幅(σ)。遅行は21本前で固定(たくちんの記憶)
import sys,glob,numpy as np,pandas as pd
sys.path.insert(0,__file__.rsplit('/',1)[0]); from engine_ichi import ema
from engine_tai import load,JST
from engine_ichi import angle21
AGG=dict(o='first',h='max',l='min',c='last')
def bars(m1,tf):
    b=m1.resample(tf).agg(AGG).dropna(); b['k']=b.index+pd.Timedelta(tf); return b
def attach(x,b,cols,pre):
    a=b[['k']+cols].rename(columns={c:pre+c for c in cols}).rename(columns={'k':pre+'k'}).sort_values(pre+'k')
    ix=x.index; y=pd.merge_asof(x.reset_index().rename(columns={'index':'t'}).sort_values('kakutei'),a,left_on='kakutei',right_on=pre+'k',direction='backward').set_index('t'); y.index.name=None; return y
def prep(m1,LAG=21):
    m=bars(m1,'5min'); m['kakutei']=m.k
    m['e9']=ema(m.c,9); m['e21']=ema(m.c,21); m['mid']=m.c.rolling(20).mean(); m['sd']=m.c.rolling(20).std(ddof=0)
    m['hL']=m.h.shift(LAG); m['lL']=m.l.shift(LAG)
    h4=bars(m1,'4h'); h4['e9']=ema(h4.c,9); h4['e21']=ema(h4.c,21)
    h1=bars(m1,'1h'); h1['e21']=ema(h1.c,21)
    # 1h の許しは「その1h足が閉じた時に確定している4h」で作る(engine_tai と同じ)
    h1=attach(h1.assign(kakutei=h1.k),h4,['c','e9','e21'],'f_')
    h1['pb']=(h1.f_c>h1.f_e9)&(h1.c>h1.e21); h1['ps']=(h1.f_c<h1.f_e9)&(h1.c<h1.e21)
    x=attach(m,h1,['pb','ps'],'g_'); h4['ang']=angle21(h4); x=attach(x,h4,['c','e21','ang'],'q_')
    return x.drop(columns=['k'])
def add_exit(x,m1,tf):
    b=bars(m1,tf); b['e9']=ema(b.c,9); mid=(b.o+b.c)/2
    b['wb']=(mid<b.e9)&(b.c<b.e9); b['ws']=(mid>b.e9)&(b.c>b.e9)
    return attach(x,b,['wb','ws'],'w_')
def signals(x,d,sao=2.0,n8=False):
    up=x.e9>x.e21; up1=x.e9.shift()>x.e21.shift()
    if d>0: perm=x.g_pb.fillna(False).astype(bool); cross=up&~up1; side=up; kawa=x.c>x['mid']+x.sd; chi=x.c>x.hL; q=x.q_c>x.q_e21; ns=x.c<=x['mid']+sao*x.sd
    else:   perm=x.g_ps.fillna(False).astype(bool); cross=~up&up1; side=~up; kawa=x.c<x['mid']-x.sd; chi=x.c<x.lL; q=x.q_c<x.q_e21; ns=x.c>=x['mid']-sao*x.sd
    e921=cross&perm; kai=perm&~perm.shift(1,fill_value=False)&side&~cross
    ent=((e921&kawa&chi)|(kai&q))&ns
    if n8:   # 縄8 4時間の竿先で入らない:入る時に確定している4h足の21の角度が向きに55度を超えていたら入らない【置き換え:だまし回避の角度の段階 55度超=竿先】(11-06 たくちん「うりもして 1と」)
        ang=x.q_ang if d>0 else -x.q_ang
        ent=ent&~(ang>55)
    return ent
def run(x,d,ent,spr=0.003):
    E=ent.values; W=(x.w_wb if d>0 else x.w_ws).fillna(False).astype(bool).values; K=x.w_k.values; O=x.o.values; H=x.h.values; L=x.l.values; T=x.index.values; tr=[]; pos=None
    for i in range(len(x)-1):
        if pos is None:
            if E[i]: pos=(i+1,O[i+1]+(spr if d>0 else 0))
        elif W[i] and K[i]>T[pos[0]]:
            j,px=pos; ex=O[i+1]+(0 if d>0 else spr); tr.append((T[j],px,T[i+1],ex,(ex-px)*100*d)); pos=None
    return pd.DataFrame(tr,columns=['ent','e','ext','x','pips'])
def stat(t):
    if len(t)==0: return dict(n=0,sum=0,pf=np.nan,dd=0)
    w=t.pips[t.pips>0].sum(); l=-t.pips[t.pips<0].sum(); eq=t.pips.cumsum()
    return dict(n=len(t),sum=round(t.pips.sum(),1),pf=round(w/l,2) if l else np.nan,dd=round((eq.cummax()-eq).max(),1))
