# 4時間足のクジラ(11-06 たくちん「途中ほったらかし 450hあしでは?」→ 読み:4時間足でも 大山の無限リーチ・途中ほったらかし をやったら?)
# 入りの合図=4時間版の鯛(4hの9上・1hの21上・5分で入る・縄4〜5・買いは縄8)。合図のたびに玉を足す(最大20発)
#   kujira=どの玉も4hの9割れまで ほったらかし / mix=芯(1発目)は4hの9割れ・足した玉は1hの9割れ / tai=1玉だけ1hの9割れ(前の形)
import sys,warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,__file__.rsplit('/',1)[0])
from engine_tai_g import *
from engine_kujira import ware,attach2,run_k,dd_open
m1=load(sys.argv[1]); out=sys.argv[2]
x=prep(m1,'4h','1h','5min')
x=attach2(x,ware(m1,'1h','a_'),'a_'); x=attach2(x,ware(m1,'4h','b_'),'b_')   # a=小さい降り(1h) b=大きい降り(4h)
h=bars(m1,'1h'); C=h.c.values; idx=h.index.values
def fdd(t,d):
    eq=np.zeros(len(idx))
    for e,ent,ext,p in zip(t.e.values,t.ent.values,t.ext.values,t.pips.values):
        a=np.searchsorted(idx,ent); b=np.searchsorted(idx,ext); eq[a:b]+=(C[a:b]-e)*100*d; eq[b:]+=p
    return round((np.maximum.accumulate(eq)-eq).max())
rows=[]
for d in (1,-1):
    ent=signals(x,d,2.0,d>0)
    for mode,mp in (('tai',1),('kujira',20),('mix',20)):
        t=run_k(x,d,ent,'tai' if mode=='tai' else mode,mp); y=pd.to_datetime(t.ent).dt.year
        r=dict(向き='買い' if d>0 else '売り',形={'tai':'鯛(1玉・1h9割れ)','kujira':'ほったらかし(全部4h9割れ)','mix':'mix(芯4h・足し1h)'}[mode])
        for k,msk in (('選22-24',y.between(2022,2024)),('確15-21',y.between(2015,2021)),('確25',y==2025),('全',y>0)):
            s_=stat(t[msk]); r[k+'_p']=s_['sum']; r[k+'_pf']=s_['pf']
        r['玉']=len(t); r['同時最大']=t.attrs['maxpos']; r['含み損込みDD']=fdd(t,d); rows.append(r)
        t.to_csv(f"{out}/K4h_{'buy' if d>0 else 'sell'}_{mode}.csv",index=False)
print(pd.DataFrame(rows).to_string(index=False))
