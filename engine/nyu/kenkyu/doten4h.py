import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *; from bugbug import bugbug
raw=load_cached(sys.argv[1]); srv=Market(raw,'server')
K=dict(maxpos=5,n8=False,reenter=True,tp=('4h',3.5),ts=550,avoid_in=(0,),avoid_out=(0,),kai_k9=3,big21_up=True)
ok,L=bugbug(lambda mk,d: run_doten(mk,d,xtf='4h',**K)[0], raw,'server',1,0.003)
print('\n'.join(l for l in L if not l.startswith('○')))
WHY={'芯の降り':'4hの219(売りは921)','TS':'TS550'}
def sp(t):
    y=pd.to_datetime(t.ent).dt.year; f=lambda m: round(float(t.pips[m].sum()))
    st=stat(t); return f"{st['n']}玉 {st['sum']:+,.0f}p PF{st['pf']} 勝{st['win']} | 選22-24 {f(y.between(2022,2024)):+,} 確16-21 {f(y.between(2016,2021)):+,} 確25-26 {f(y>=2025):+,}"
for d,nm in [(1,'売りの利確 → 921待ちドテン買い'),(-1,'買いの利確 → 219待ちドテン売り')]:
    a,_=run_doten(srv,d,**K); b,_=run_doten(srv,d,xtf='4h',**K); b=b.sort_values('ent')
    print(f'\n=== {nm}\n  降り1h {sp(a)}\n  降り4h {sp(b)}  持った時間の中央 {(pd.to_datetime(b.ext)-pd.to_datetime(b.ent)).median()}')
    m=a.merge(b,on='ent',how='outer',suffixes=('_1h','_4h'))
    for _,r in m.sort_values('ent').iterrows():
        f=lambda v,mf,w: '----' if pd.isna(v) else f"{v:+6.0f}p(伸び{mf:+.0f}) {WHY.get(w,w) if w!='芯の降り' else ''}"
        print(f"  {r.ent:%Y/%m/%d %H時} {r.e_4h if not pd.isna(r.e_4h) else r.e_1h:.3f}  1h降り {f(r.pips_1h,r.mfe_1h,'')}  →  4h降り {f(r.pips_4h,r.mfe_4h,r.why_4h)}")
