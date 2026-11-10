import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *; from bugbug import bugbug
raw=load_cached(sys.argv[1]); srv=Market(raw,'server')
K=dict(maxpos=5,n8=False,reenter=True,tp=('4h',3.5),ts=550,avoid_in=(0,),avoid_out=(0,),kai_k9=3,big21_up=True,yasumi=True)
T=dict(maxpos=1,n8=False,reenter=True,ts=550,avoid_in=(0,),avoid_out=(0,),kai_k9=3,big21_up=True,yasumi=True)   # 鯛:同じ入り・1玉・4時間の9割れで降りる・TS550・利確なし
ok,L=bugbug(lambda mk,d: run_tai(mk,'1D','4h','1h',d,('4h','9割れ'),**T)[0], raw,'server',1,0.003)
print('鯛 修正機:', '全部○' if ok else [l for l in L if l.startswith('×')])
def sp(t):
    y=pd.to_datetime(t.ent).dt.year; f=lambda m: round(float(t.pips[m].sum())); st=stat(t)
    return f"{st['n']}玉 {st['sum']:+,.0f}p 勝率{st['win']/max(st['n'],1)*100:.1f}% PF{st['pf']} | 選22-24 {f(y.between(2022,2024)):+,} 確16-21 {f(y.between(2016,2021)):+,} 確25-26 {f(y>=2025):+,}"
b,base=run_tai(srv,'1D','4h','1h',1,('1D','219'),**K); s,_=run_tai(srv,'1D','4h','1h',-1,('1D','219'),**K); dt,_=run_doten(srv,1,xtf='4h',**K)
tb,_=run_tai(srv,'1D','4h','1h',1,('4h','9割れ'),**T); ts_,_=run_tai(srv,'1D','4h','1h',-1,('4h','9割れ'),**T)
for t,d in [(b,1),(s,-1),(dt,1),(tb,1),(ts_,-1)]: t['d']=d
f3=pd.concat([b,s,dt],ignore_index=True); tai=pd.concat([tb,ts_],ignore_index=True); al=pd.concat([f3,tai],ignore_index=True)
print('\n鯛だけ 買い',sp(tb)); print('鯛だけ 売り',sp(ts_)); print('鯛だけ',sp(tai))
print('\n形3     ',sp(f3)); print('形3+鯛  ',sp(al))
for nm,t in [('形3',f3),('形3+鯛',al)]:
    T_,st=lot_sizing(t,base,1,102000,leverage=2000,fixed_lot=0.01,stopout=20); print(f"  {nm} 0.01ロット 最後 {st['最後の資金']:,}円 一番へこんだ {st['一番へこんだ資金']:,}円 落ち込み率 {st['落ち込み率']}%")
k=lambda t: t.pips[pd.to_datetime(t.ent).dt.year.between(2016,2021)|(pd.to_datetime(t.ent).dt.year>=2025)].sum()
print(f"\n決め方(先に決めた):確かめる年の合計 {k(f3):+,.0f} → {k(al):+,.0f}")
tai=tai.sort_values('pips'); W={'芯の降り':'4h9割れ','TS':'TS550'}
print('\n鯛 一番負けた5玉'); [print(f"  {'買' if r.d>0 else '売'} {r.ent:%Y/%m/%d %H時} {r.e:.3f} → {r.ext:%m/%d %H時} {r.pips:+.0f}p {W.get(r.why,r.why)}") for _,r in tai.head(5).iterrows()]
print('鯛 一番勝った5玉'); [print(f"  {'買' if r.d>0 else '売'} {r.ent:%Y/%m/%d %H時} {r.e:.3f} → {r.ext:%m/%d %H時} {r.pips:+.0f}p {W.get(r.why,r.why)}") for _,r in tai.tail(5).iterrows()]
print('鯛 持った時間の中央',(pd.to_datetime(tai.ext)-pd.to_datetime(tai.ent)).median())
al2=pd.concat([f3,tb],ignore_index=True)
print('\n形3+鯛(買いだけ)',sp(al2)); T_,st=lot_sizing(al2,base,1,102000,leverage=2000,fixed_lot=0.01,stopout=20)
print(f"  0.01ロット 最後 {st['最後の資金']:,}円 一番へこんだ {st['一番へこんだ資金']:,}円 落ち込み率 {st['落ち込み率']}%  確かめる年の合計 {k(f3):+,.0f} → {k(al2):+,.0f}")
