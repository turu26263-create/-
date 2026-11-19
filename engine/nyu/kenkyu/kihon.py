import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *; from bugbug import bugbug
raw=load_cached(sys.argv[1]); srv=Market(raw,'server')
C=dict(maxpos=5,n8=False,reenter=True,avoid_in=(0,),avoid_out=(0,),kai_k9=3,big21_up=True)
F2=dict(tp=('4h',3.5),ts=550)                       # 付属品つき(今の形2)
KI=dict(kawa_chi=False,sao=99.0)                    # 基本だけ:青赤(9・21)の判定だけ。川の外(±1σ)・遅行・竿先(2σ)・利確(3.5σ)・TS は外す
ok,L=bugbug(lambda mk,d: run_tai(mk,'1D','4h','1h',d,('1D','219'),**C,**KI)[0], raw,'server',5,0.003)
print('\n'.join(l for l in L if not l.startswith('○')))
def sp(t):
    y=pd.to_datetime(t.ent).dt.year; f=lambda m: round(float(t.pips[m].sum()))
    st=stat(t); return f"{st['n']}玉 {st['sum']:+,.0f}p PF{st['pf']} | 選22-24 {f(y.between(2022,2024)):+,} 確16-21 {f(y.between(2016,2021)):+,} 確25-26 {f(y>=2025):+,}"
for nm,X in [('付属品つき(形2)',F2),('基本だけ(青赤)',KI)]:
    b,base=run_tai(srv,'1D','4h','1h',1,('1D','219'),**C,**X); s,_=run_tai(srv,'1D','4h','1h',-1,('1D','219'),**C,**X)
    b['d']=1; s['d']=-1; t=pd.concat([b,s],ignore_index=True)
    T,st=lot_sizing(t,base,1,102000,leverage=2000,fixed_lot=0.01,stopout=20)
    print(f"\n{nm}\n  買い {sp(b)}\n  売り {sp(s)}\n  売り買い {sp(t)}\n  0.01ロット 最後 {st['最後の資金']:,}円 一番へこんだ {st['一番へこんだ資金']:,}円 落ち込み率 {st['落ち込み率']}%  一番負けた玉 {t.pips.min():+.0f}p")
