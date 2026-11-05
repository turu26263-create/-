# わがまま版:200でドテンし続ける(つねに買いか売りを持つ)+部品
from sim3 import *
def prep4(m5, h1, TF='4h', BUF=0.0, LOC='same', NET=None, CHB=22):
    m=m5.copy(); idx=m.index; b=bigbars(h1,TF); e=ema(b.c,200)
    side=pd.Series(np.where(b.c>e+BUF*PIP,1,np.where(b.c<e-BUF*PIP,-1,np.nan)),index=b.index).ffill().fillna(0)
    side[: b.index[200]]=0
    tr=to_m5(side,TF,idx); m['trend']=tr; m['ent']=tr
    if LOC=='same': m['loc']=tr                         # すぐ入る・すぐ足す
    else:           m['loc']=pd.Series(order(m.c),index=idx).shift(1)   # 5分 5>9>21 がそろった時だけ
    if NET is None: m['chL']=-1e9; m['chS']=1e9         # 網なし(ドテンだけで降りる)
    else:
        tf,k=NET; a=to_m5(atr14(bigbars(h1,tf)),tf,idx)
        hh=m.h.rolling(CHB).max().shift(1); ll=m.l.rolling(CHB).min().shift(1)
        m['chL']=hh-k*a; m['chS']=ll+k*a
    return m.dropna()
def row(tag,m,spr=0.3,**kw):
    a=sim3(m,spr,start='2022',end='2024',**kw); b=sim3(m,spr,start='2015',end='2021',**kw); c=sim3(m,spr,start='2025',**kw); f=sim3(m,spr,**kw)
    print(f"{tag:34s} 決 {a['pips']:+7d} PF{a['PF']:.2f} | 確15-21 {b['pips']:+7d} PF{b['PF']:.2f} | 確25 {c['pips']:+6d} | 全 {f['pips']:+7d} PF{f['PF']:.2f} DD{f['DD']:6d} 戦{f['ikusa']:4d} 買{f['buy']:+d} 売{f['sell']:+d}",flush=True)
    return f
