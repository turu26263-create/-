# 11-11 たくちん「しあわせセットは決めてない研鑽して 竿元からbb2丸まりがレンジ突入やから bb2からロウソク離れ出したら利確?にしたら上飛びが取れん?」
# 使い方: python3 hanare.py <MT4 1時間足の置き場> [seiseki]
import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *; from bugbug import bugbug
raw=load_cached(sys.argv[1]); srv=Market(raw,'server'); TF='4h'
K=dict(maxpos=5,n8=False,reenter=True,tp=('4h',4.0),ts=550,avoid_in=(0,),avoid_out=(0,),kai_k9=3,big21_up=True,yasumi=True)
make=lambda mk,d: run_tai(mk,'1D','4h','1h',d,('1D','219'),**K,hanare_tf=TF)[0]
ok,L=bugbug(make,raw,'server',5,0.003); print('修正機:', '全部○' if ok else '×あり'); print('\n'.join(l for l in L if l.startswith('×') or 'ローソク' in l))
kow=lambda mk,d: make(mk,d).assign(pips=lambda t: t.pips-(t.why=='離れ利確')*30)
b,base=make(srv,1),None; b0,_=run_tai(srv,'1D','4h','1h',1,('1D','219'),**K); s=make(srv,-1); s0,_=run_tai(srv,'1D','4h','1h',-1,('1D','219'),**K)
for nm,t in [('買い',b),('売り',s)]:
    q=t[t.why=='離れ利確']; print(f'{nm}: 離れ利確 {len(q)}玉・そのうち負け {int((q.pips<0).sum())}玉(一番負け {q.pips.min():+.1f}p)・入った次の足までに降りた {int(((q.ext-q.ent)<=pd.Timedelta("1h")).sum())}玉')
F=srv.feat('4h'); x=srv.feat('1h'); PX=hanare(srv,'1h','4h',1)
def aruki(a,bb):
    print(f'--- 歩き(買い)4時間足 {a}〜{bb} ---')
    for nm,tt in [('今の形',b0),('離れ利確つき',b)]:
        for r in tt[(tt.ent>=a)&(tt.ent<=bb)].itertuples(): print(f'  {nm} {r.n}発目 {r.ent:%m/%d %H時} {r.e:.3f} → {r.ext:%m/%d %H時} {r.x:.3f} {r.pips:+.1f}p {r.why}(伸びた最大 {r.mfe:+.0f}p)')
    w=F[a:bb]; up=w.md+2*w.sd; pu=(F.md+2*F.sd).shift(1)[a:bb]
    for ts,r in w.iterrows():
        u=up[ts]; k1=r.k; ev=(k1-pd.Timedelta('1h') in x.index) and not np.isnan(PX[x.index.get_loc(k1-pd.Timedelta('1h'))]) if (k1-pd.Timedelta('1h')) in x.index else False
        print(f'  {ts:%m/%d %H時} 高値 {r.h:.3f} 終値 {r.c:.3f} +2σ {u:.3f}({"上がる" if u>pu[ts] else "丸まり"}) 高値が+2σに{"届いた" if r.h>=u else "届かない"}{" ← 離れ出した(合図)" if ev else ""}')
aruki(pd.Timestamp('2016-11-09 12:00'),pd.Timestamp('2016-11-30 00:00'))
if len(sys.argv)>2:
    def blend(hf):
        KB={**K,'hanare_tf':hf}
        bb,base=run_tai(srv,'1D','4h','1h',1,('1D','219'),**KB); ss,_=run_tai(srv,'1D','4h','1h',-1,('1D','219'),**KB); dt,_=run_doten(srv,1,xtf='4h',**KB)   # ドテン買いは売りの4時間σの利確で構える(離れ利確では構えない)。売りと同じ形を渡す
        tb,_=run_tai(srv,'1D','4h','1h',1,('4h','9割れ'),**{**K,'maxpos':1,'tp':None}); ob,_=run_oshime_d(srv,1); os_,_=run_oshime_d(srv,-1)
        for t,k,d in [(bb,'買い',1),(ss,'売り',-1),(dt,'ドテン買い',1),(tb,'鯛',1),(ob,'押し目買い',1),(os_,'押し目売り',-1)]: t['kind']=k; t['d']=d
        return pd.concat([bb,ss,dt,tb,ob,os_],ignore_index=True),base
    print('決め方(先に決めた・前と同じ):確かめる年の合計が上がり、落ち込み率が上がらなければ残す')
    for nm,hf in [('今の形',None),('4時間の+2σから離れ出したら、利が乗っている玉を利確',TF)]:
        t,base=blend(hf); y=pd.to_datetime(t.ent).dt.year; T_,st=lot_sizing(t,base,1,102000,leverage=2000,fixed_lot=0.01,stopout=20)
        f=lambda k: f"{int((t.kind==k).sum())}玉 {t.pips[t.kind==k].sum():+,.0f}p"; g=lambda w: f"{int((t.why==w).sum())}玉 {t.pips[t.why==w].sum():+,.0f}p"
        print(f"  {nm}:\n     買い {f('買い')} / 売り {f('売り')} / ドテン買い {f('ドテン買い')} / 全部 {len(t)}玉 {t.pips.sum():+,.0f}p 選22-24 {t.pips[y.between(2022,2024)].sum():+,.0f} 確かめる年 {t.pips[y.between(2016,2021)|(y>=2025)].sum():+,.0f} 落ち込み率 {st['落ち込み率']}%\n     降りの中身:4時間4.0σの利確 {g('利確')} / 離れ利確 {g('離れ利確')} / 日足219・921 {int(t.why.isin(['芯の降り','足しの降り']).sum())}玉 {t.pips[t.why.isin(['芯の降り','足しの降り'])].sum():+,.0f}p / TS {g('TS')}")
