import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *
srv=Market(load_cached(sys.argv[1]),'server')
K=dict(maxpos=5,n8=False,reenter=True,tp=('4h',3.5),ts=550,avoid_in=(0,),avoid_out=(0,),kai_k9=3,big21_up=True)
b,_=run_tai(srv,'1D','4h','1h',1,('1D','219'),**K)
s,_=run_tai(srv,'1D','4h','1h',-1,('1D','219'),**K)
dt,_=run_doten(srv,1,xtf='4h',**K)
D=srv.feat('1D'); up=(D.e9>D.e21)
grp=(up!=up.shift()).cumsum()
rows=[]
for g,x in D.groupby(grp):
    if len(x)<3: continue
    u=bool(up.loc[x.index[0]]); st,en=x.index[0],x.k.iloc[-1]
    size=(x.h.max()-x.l.min())*100
    # 山の中の動き:買いは山の始まりの安値から一番上、売りは始まりの高値から一番下
    T=b if u else s
    m=T[(T.ent>=st)&(T.ent<en)]
    tot=m.pips.sum(); best=m.pips.max() if len(m) else 0
    rows.append(dict(向き='上げ' if u else '下げ',始=st.strftime('%Y/%m/%d'),終=en.strftime('%Y/%m/%d'),日数=len(x),山の大きさ=round(size),玉=len(m),取った合計=round(tot),一番取った玉=round(best),
                     一玉あたり=round(tot/len(m)) if len(m) else 0, 取れた割合=f"{(best/size*100 if size else 0):.0f}%"))
R=pd.DataFrame(rows)
pd.set_option('display.width',250)
print('日足の山(9と21の並びが続く間) 大きい順')
print(R.sort_values('山の大きさ',ascending=False).head(16).to_string(index=False))
big=R[R.山の大きさ>=1000]
print(f"\n大きさ1,000p以上の山 {len(big)}個:山の大きさ合計 {big.山の大きさ.sum():,}p / 取った合計 {big.取った合計.sum():+,}p / 一番取った玉の合計 {big.一番取った玉.sum():+,}p")
sm=R[R.山の大きさ<1000]
print(f"1,000p未満の山 {len(sm)}個:取った合計 {sm.取った合計.sum():+,}p")
