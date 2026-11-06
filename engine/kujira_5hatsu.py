# クジラの刺身 5発(11-06 たくちん「大山日足9で無限リーチ5発 そんぎりもなんもせんで日足9の終わりクジラの刺身で」)
# 入りの合図=日足版の鯛(日足の9上・4hの21上・1hで入る・縄4〜5・買いは縄8)。合図のたびに足す(最大5発)。損切りなし。日足の9の終わりで全部降りる
#   終わり='9割れ'=確定日足の実体の真ん中と終値が9の下 / '終値'=確定日足の終値が9の下だけ
import sys,warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,__file__.rsplit('/',1)[0])
from engine_tai_g import *
from engine_kujira import attach2,run_k
m1=load(sys.argv[1]); out=sys.argv[2]
D=bars(m1,'1D'); D['e9']=ema(D.c,9); mid=(D.o+D.c)/2
x0=prep(m1,'1D','4h','1h'); h=bars(m1,'1h'); C=h.c.values; idx=h.index.values
def fdd(t,d):
    eq=np.zeros(len(idx))
    for e,ent,ext,p in zip(t.e.values,t.ent.values,t.ext.values,t.pips.values):
        a=np.searchsorted(idx,ent); b=np.searchsorted(idx,ext); eq[a:b]+=(C[a:b]-e)*100*d; eq[b:]+=p
    return round((np.maximum.accumulate(eq)-eq).max())
rows=[]
for owari in ('9割れ','終値'):
    if owari=='9割れ': wb=(mid<D.e9)&(D.c<D.e9); ws=(mid>D.e9)&(D.c>D.e9)
    else: wb=D.c<D.e9; ws=D.c>D.e9
    w=pd.DataFrame({'b_k':D.k,'b_wb':wb,'b_ws':ws}); x=attach2(x0,w,'b_')
    x['a_wb']=False; x['a_ws']=False; x['a_k']=x['b_k']
    for d in (1,-1):
        t=run_k(x,d,signals(x,d,2.0,d>0),'kujira',5); y=pd.to_datetime(t.ent).dt.year
        r=dict(向き='買い' if d>0 else '売り',終わり=owari)
        for k,msk in (('選22-24',y.between(2022,2024)),('確15-21',y.between(2015,2021)),('確25',y==2025),('全',y>0)):
            s_=stat(t[msk]); r[k+'_p']=s_['sum']; r[k+'_pf']=s_['pf']
        g=t.groupby('camp').pips.sum()
        r['玉']=len(t); r['クジラ']=len(g); r['勝ったクジラ']=int((g>0).sum()); r['含み損込みDD']=fdd(t,d); rows.append(r)
        t.to_csv(f"{out}/K5_{'buy' if d>0 else 'sell'}_{owari}.csv",index=False)
print(pd.DataFrame(rows).to_string(index=False))
