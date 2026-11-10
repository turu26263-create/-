import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *
srv=Market(load_cached(sys.argv[1]),'server')
K=dict(maxpos=5,n8=False,reenter=True,tp=('4h',4.0),ts=550,avoid_in=(0,),avoid_out=(0,),kai_k9=3,big21_up=True,yasumi=True)
def blend(smax=5,w=1.0):
    KS={**K,'maxpos':smax}
    b,base=run_tai(srv,'1D','4h','1h',1,('1D','219'),**K); s,_=run_tai(srv,'1D','4h','1h',-1,('1D','219'),**KS); dt,_=run_doten(srv,1,xtf='4h',**KS)   # ドテンは同じ売りの利確から
    tb,_=run_tai(srv,'1D','4h','1h',1,('4h','9割れ'),**{**K,'maxpos':1,'tp':None}); ob,_=run_oshime_d(srv,1); os_,_=run_oshime_d(srv,-1)
    for t,k,d in [(b,'買い',1),(s,'売り',-1),(dt,'ドテン買い',1),(tb,'鯛',1),(ob,'押し目買い',1),(os_,'押し目売り',-1)]: t['kind']=k; t['d']=d
    t=pd.concat([b,s,dt,tb,ob,os_],ignore_index=True); t['wp']=np.where(t.kind=='売り',t.pips*w,t.pips); return t,base
def line(nm,t,base,w=1.0):
    y=pd.to_datetime(t.ent).dt.year; s=t[t.kind=='売り']; d=t[t.kind=='ドテン買い']
    eq=t.sort_values('ext').wp.cumsum(); dd=(eq.cummax()-eq).max()
    r=dict(sum=t.wp.sum(),kak=t.wp[y.between(2016,2021)|(y>=2025)].sum(),sen=t.wp[y.between(2022,2024)].sum(),dd=dd)
    print(f"  {nm}: 売り {len(s)}玉 {s.wp.sum():+,.0f}p / ドテン買い {len(d)}玉 {d.pips.sum():+,.0f}p / 全部 {r['sum']:+,.0f}p 選22-24 {r['sen']:+,.0f} 確かめる年 {r['kak']:+,.0f} 降りた順の一番の落ち込み {dd:,.0f}p")
    return r
print('売りを半分にする照らし(11-10 たくちん「売りが弱いなら売りエントリはんぶんにする？」)。今の決まった形(ブレンド・利確4.0σ)と1つずつ比べた')
print('決め方(先に決めた):確かめる年の合計が上がり、一番の落ち込みが増えなければ残す\n')
A,base=blend(); a=line('今(売り5発・同じロット)',A,base)
B,_=blend(smax=3); b=line('売りの発数を5→3',B,base); print(f"   → {'残す' if (b['kak']>a['kak'] and b['dd']<=a['dd']) else '×'}")
B2,_=blend(smax=2); b2=line('売りの発数を5→2',B2,base); print(f"   → {'残す' if (b2['kak']>a['kak'] and b2['dd']<=a['dd']) else '×'}")
C,_=blend(w=0.5); c=line('売りのロットを半分(pipsを半分に数える)',C,base); print(f"   → {'残す' if (c['kak']>a['kak'] and c['dd']<=a['dd']) else '×'}")
s=A[A.kind=='売り']; s['n']=s.groupby('camp').cumcount()+1
print('\n売りの何発目ごと:', {int(k): f"{int(v['count'])}玉 {v['sum']:+,.0f}p" for k,v in s.groupby('n').pips.agg(['count','sum']).iterrows()})
y=pd.to_datetime(s.ent).dt.year; print('売りの年ごと:', s.groupby(y).pips.sum().round().astype(int).to_dict())
