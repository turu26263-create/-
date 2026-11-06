# 重ね(11-06 たくちん「日足大山の無限リーチしてそのままうごかさず ぜんぶさしみとったら?」)
# クジラ層=日足の無限リーチ(kujira 最大20発・どの玉も日足の9割れまで持つ)+ 鯛層①4時間版 + 鯛層②日足版。1玉=0.1ロットのつもりで p を足すだけ
import sys,warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,__file__.rsplit('/',1)[0])
from engine_tai_g import *
m1=load(sys.argv[1]); h=bars(m1,'1h'); C=h.c.values; idx=h.index.values
L={'クジラ買い':('kujira/K_buy_kujira_20',1),'クジラ売り':('kujira/K_sell_kujira_20',-1),
   '鯛①買い(4h版)':('bunmawashi/buy_1h_2.0_縄8あり',1),'鯛①売り(4h版)':('bunmawashi/sell_1h_2.0_縄8なし',-1),
   '鯛②買い(日足版)':('hiashi/D_buy_4h_2.0_縄8あり',1),'鯛②売り(日足版)':('hiashi/D_sell_4h_2.5_縄8あり',-1)}
T={k:(pd.read_csv(f'engine/kekka_tai/{f}.csv',parse_dates=['ent','ext']),d) for k,(f,d) in L.items()}
def curve(names):
    eq=np.zeros(len(idx))
    for n in names:
        t,d=T[n]
        for e,x0,ent,ext,p in zip(t.e.values,t.x.values,t.ent.values,t.ext.values,t.pips.values):
            a=np.searchsorted(idx,ent); b=np.searchsorted(idx,ext)
            eq[a:b]+=(C[a:b]-e)*100*d; eq[b:]+=p
    return eq
def show(nm,names):
    t=pd.concat([T[n][0] for n in names]); y=pd.to_datetime(t.ext).dt.year
    eq=curve(names); dd=(np.maximum.accumulate(eq)-eq).max()
    r=dict(組=nm,玉=len(t),全=round(t.pips.sum()),PF=stat(t)['pf'],選22_24=round(t.pips[y.between(2022,2024)].sum()),確15_21=round(t.pips[y.between(2015,2021)].sum()),確25=round(t.pips[y==2025].sum()),含み損込みDD=round(dd))
    return r,t.groupby(y).pips.sum().round()
rows=[];years={}
for nm,names in (('クジラ買いだけ',['クジラ買い']),
                 ('鯛①②だけ(買い売り)',['鯛①買い(4h版)','鯛①売り(4h版)','鯛②買い(日足版)','鯛②売り(日足版)']),
                 ('クジラ買い+鯛①②全部',['クジラ買い','鯛①買い(4h版)','鯛①売り(4h版)','鯛②買い(日足版)','鯛②売り(日足版)']),
                 ('クジラ買い売り+鯛①②全部',list(L))):
    r,yy=show(nm,names); rows.append(r); years[nm]=yy
print(pd.DataFrame(rows).to_string(index=False))
print('\n年ごと(降りた年で数えた)'); print(pd.DataFrame(years).fillna(0).astype(int).to_string())
