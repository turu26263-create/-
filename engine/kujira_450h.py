# 450時間足のクジラ(11-06 たくちん「いや450h」)
# 450時間足 = 時刻を450時間ごとに区切った足(MT4 の期間変換と同じく暦の時間で区切る。区切りの始まりは1970-01-01 0時 EST)【置き換え】
# 形:450hの9上(縄1)・日足の21上(縄2)・1hで入る(縄3〜5)・縄4改と縄8は450h。合図のたびに足す(最大20発)
#   ほったらかし=全部 450hの9割れまで / mix=芯は450hの9割れ・足しは日足の9割れ / 鯛=1玉だけ日足の9割れ
import sys,warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,__file__.rsplit('/',1)[0])
import engine_tai_g as G
from engine_tai_g import *
from engine_kujira import attach2,run_k
_bars=G.bars
def bars450(m1,tf):
    if tf=='450h':
        b=m1.resample('450h',origin='epoch').agg(AGG).dropna(); b['k']=b.index+pd.Timedelta('450h'); return b
    return _bars(m1,tf)
G.bars=bars450
def ware2(m1,tf,pre):
    b=bars450(m1,tf); b['e9']=ema(b.c,9); mid=(b.o+b.c)/2
    b['wb']=(mid<b.e9)&(b.c<b.e9); b['ws']=(mid>b.e9)&(b.c>b.e9); return b[['k','wb','ws']].rename(columns={'k':pre+'k','wb':pre+'wb','ws':pre+'ws'})
m1=load(sys.argv[1]); out=sys.argv[2]
B=bars450(m1,'450h'); print('450時間足',len(B),'本',B.index[0],'〜',B.index[-1])
x=G.prep(m1,'450h','1D','1h'); x=attach2(x,ware2(m1,'1D','a_'),'a_'); x=attach2(x,ware2(m1,'450h','b_'),'b_')
h=bars450(m1,'1h'); C=h.c.values; idx=h.index.values
def fdd(t,d):
    eq=np.zeros(len(idx))
    for e,ent,ext,p in zip(t.e.values,t.ent.values,t.ext.values,t.pips.values):
        a=np.searchsorted(idx,ent); b=np.searchsorted(idx,ext); eq[a:b]+=(C[a:b]-e)*100*d; eq[b:]+=p
    return round((np.maximum.accumulate(eq)-eq).max())
rows=[]
for d in (1,-1):
    ent=G.signals(x,d,2.0,d>0)
    for mode,mp in (('tai',1),('kujira',20),('mix',20)):
        t=run_k(x,d,ent,mode,mp); y=pd.to_datetime(t.ent).dt.year
        r=dict(向き='買い' if d>0 else '売り',形={'tai':'鯛(1玉・日足9割れ)','kujira':'ほったらかし(全部450h9割れ)','mix':'mix(芯450h・足し日足)'}[mode])
        for k,msk in (('選22-24',y.between(2022,2024)),('確15-21',y.between(2015,2021)),('確25',y==2025),('全',y>0)):
            s_=stat(t[msk]); r[k+'_p']=s_['sum']; r[k+'_pf']=s_['pf']
        r['玉']=len(t); r['戦']=t.camp.nunique(); r['同時最大']=t.attrs['maxpos']; r['含み損込みDD']=fdd(t,d) if len(t) else 0; rows.append(r)
        t.to_csv(f"{out}/K450_{'buy' if d>0 else 'sell'}_{mode}.csv",index=False)
print(pd.DataFrame(rows).to_string(index=False))
