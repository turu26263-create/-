import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *
srv=Market(load_cached(sys.argv[1]),'server'); spr=0.003
D=srv.feat('1D'); H=srv.feat('1h'); up=(D.e9>D.e21); grp=(up!=up.shift()).cumsum()
K=dict(maxpos=5,n8=False,reenter=True,tp=('4h',3.5),ts=550,avoid_in=(0,),avoid_out=(0,),kai_k9=3,big21_up=True)
b,_=run_tai(srv,'1D','4h','1h',1,('1D','219'),**K); s,_=run_tai(srv,'1D','4h','1h',-1,('1D','219'),**K)
def px(t):  # 日足が閉じた時刻 t の後、1時の1時間足の始値(0時はスプレッドが開くので1時)
    i=H.index.searchsorted(t + pd.Timedelta('1h')); return H.index[i], H.o.iloc[i]
rows=[]
gl=list(D.groupby(grp))
for n,(g,x) in enumerate(gl[1:-1],1):           # 最初と最後(終わっていない山)は除く
    u=bool(up.loc[x.index[0]]); size=(x.h.max()-x.l.min())*100
    t0,e=px(x.k.iloc[0]-pd.Timedelta('1D')+pd.Timedelta('1D')) if False else px(D.k.loc[x.index[0]])   # 921(219)が出た日足が閉じた時
    t1,c=px(x.k.iloc[-1])                      # 最後の日足が閉じた次の日足で並びが逆になる=219(921)が出た日足が閉じた時
    nx=gl[n+1][1]; t1,c=px(D.k.loc[nx.index[0]])
    p=((c-(e+spr))/0.01) if u else (((e)-(c+spr))/0.01)
    T=b if u else s; got=T[(T.ent>=x.index[0])&(T.ent<nx.index[0])].pips.sum()
    rows.append(dict(向き='上げ' if u else '下げ',入り=t0.strftime('%Y/%m/%d'),降り=t1.strftime('%Y/%m/%d'),山=round(size),一発=round(p),五発=round(5*p),形2で取った=round(got),大山=size>=1000))
R=pd.DataFrame(rows); pd.set_option('display.width',250); pd.set_option('display.max_rows',200)
big=R[R.大山]
print('大山(1,000p以上)で 何も無し・5発・日足921で入り日足219で降り(売りは219で入り921で降り)')
print(big.drop(columns='大山').to_string(index=False))
print(f"\n大山{len(big)}個:5発の合計 {big.五発.sum():+,}p / 形2で取った合計 {big.形2で取った.sum():+,}p / 山の大きさの合計 {big.山.sum():,}p")
sm=R[~R.大山]
print(f"\n同じことを全部の山でやると(山の大きさは開けてみないと分からないので):山{len(R)}個 5発の合計 {R.五発.sum():+,}p(大山 {big.五発.sum():+,} / 小さい山{len(sm)}個 {sm.五発.sum():+,})")
print(f"  小さい山で一番負けた5発 {sm.五発.min():+,}p・負けた山 {int((sm.五発<0).sum())}個")
y=pd.to_datetime(R.入り).dt.year
print('  年ごと(5発):',R.groupby(y).五発.sum().to_dict())
R['日数']=[ (pd.Timestamp(r.降り)-pd.Timestamp(r.入り)).days for r in R.itertuples()]
print('\n小さい山を日数で分けた(5発):')
print(sm.assign(日数=R.loc[sm.index,'日数']).groupby(pd.cut(R.loc[sm.index,'日数'],[0,7,14,30,60,999])).五発.agg(['count','sum','mean']).round().to_string())
print('\n2020年の山(歩き):'); print(R[pd.to_datetime(R.入り).dt.year==2020].drop(columns='大山').to_string(index=False))
