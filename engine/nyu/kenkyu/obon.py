import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
exec(open(sys.argv[2]).read().split("print('■ マホカンタ")[0])   # 費用(マホカンタ)の決め方を同じに使う
from bugbug import bugbug
OB=[((8,11),(8,16))]
print('■ お盆(8/11〜8/16)の動き:日足の高安の幅の平均')
D=srv.feat('1D'); D=D[D.index.month==8]; rng=(D.h-D.l)*100; md=D.index.day
print(f"  8月のお盆 {rng[(md>=11)&(md<=16)].mean():.0f}p / 8月のほかの日 {rng[~((md>=11)&(md<=16))].mean():.0f}p / 1年の平均 {((srv.feat('1D').h-srv.feat('1D').l)*100).mean():.0f}p")
P,base=form3(yasumi=True); A=pd.concat([cost(t,int(t.d.iloc[0])) for t in P])
e=pd.to_datetime(A.ent); ob=A[(e.dt.month==8)&(e.dt.day>=11)&(e.dt.day<=16)].sort_values('ent')
print(f"\n■ 今の形(休みあり・費用込み)でお盆に入った玉 {len(ob)}(勝ち{int((ob.pips>0).sum())} 負け{int((ob.pips<0).sum())}) {ob.pips.sum():+,.0f}p")
for _,r in ob.iterrows(): print(f"    {r.kind} {r.ent:%Y/%m/%d %H時} {r.e:.3f} → {r.ext:%m/%d} {r.pips:+.0f}p")
ys=YASUMI+OB
ok,L=bugbug(lambda mk,d: run_tai(mk,'1D','4h','1h',d,('1D','219'),**K,yasumi=ys)[0], raw,'server',5,0.003)
Q,_=form3(yasumi=ys); B=pd.concat([cost(t,int(t.d.iloc[0])) for t in Q])
print(f"\n■ お盆も休みに足した  修正機:{'全部○' if ok else '×あり'}\n  今   {sp(A)}\n  お盆も {sp(B)}")
for nm,t in [('今',A),('お盆も',B)]:
    T,st=lot_sizing(t,base,1,102000,leverage=2000,fixed_lot=0.01,stopout=20); print(f"  {nm} 0.01ロット 最後 {st['最後の資金']:,}円 落ち込み率 {st['落ち込み率']}%")
