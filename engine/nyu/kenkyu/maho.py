import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *; from bugbug import bugbug
raw=load_cached(sys.argv[1]); srv=Market(raw,'server')
K=dict(maxpos=5,n8=False,reenter=True,tp=('4h',3.5),ts=550,avoid_in=(0,),avoid_out=(0,),kai_k9=3,big21_up=True)
# 【置き換え】ドル円の金利差(アメリカ政策金利−日本)の年平均の見当(%)。業者は買いに8割払い、売りから1.2倍取る見当
SA={2016:0.5,2017:1.2,2018:2.0,2019:2.3,2020:0.5,2021:0.2,2022:1.8,2023:5.1,2024:5.0,2025:3.7,2026:2.8}
SPR_H={23:1.0,0:5.0,1:1.0}   # 【置き換え】時刻(サーバー)ごとに足すスプレッド p(入りと降りの両方)
H=srv.feat('1h')
def cost(t,d):
    t=t.copy(); sw=[]
    for a,b,e in zip(pd.to_datetime(t.ent),pd.to_datetime(t.ext),t.e):
        days=pd.date_range(a.normalize(),b,freq='D'); days=days[(days>a)&(days<=b)]; v=0.0
        for dd in days:
            if dd.weekday()>=5: continue
            n=3 if dd.weekday()==2 else 1; dif=SA.get(dd.year,2.0)/100
            p=100*e*dif/365*(0.8 if d>0 else -1.2); v+=n*p
        sw.append(v)
    t['swap']=sw; eh=pd.to_datetime(t.ent).dt.hour; xh=pd.to_datetime(t.ext).dt.hour
    t['spr']=-(eh.map(lambda h:SPR_H.get(h,0)).values+xh.map(lambda h:SPR_H.get(h,0)).values)
    t['pips']=t.pips+t.swap+t.spr; return t
def form3(**x):
    b,base=run_tai(srv,'1D','4h','1h',1,('1D','219'),**K,**x); s,_=run_tai(srv,'1D','4h','1h',-1,('1D','219'),**K,**x); dt,_=run_doten(srv,1,xtf='4h',**K,**x)
    b['kind']='買い'; s['kind']='売り'; dt['kind']='ドテン買い'; b['d']=1; s['d']=-1; dt['d']=1
    return [b,s,dt],base
def sp(t):
    y=pd.to_datetime(t.ent).dt.year; f=lambda m: round(float(t.pips[m].sum())); st=stat(t)
    return f"{st['n']}玉 {st['sum']:+,.0f}p 勝率{st['win']/max(st['n'],1)*100:.1f}% PF{st['pf']} | 選22-24 {f(y.between(2022,2024)):+,} 確16-21 {f(y.between(2016,2021)):+,} 確25-26 {f(y>=2025):+,}"
print('■ マホカンタ(はね返ってくる費用):スワップ(年ごとの金利差の見当)と時刻ごとのスプレッドを形3に入れた')
P,base=form3()
C=[cost(t,int(t.d.iloc[0])) for t in P]
for t0,t1 in zip(P,C):
    print(f"  {t0.kind.iloc[0]}: 前 {sp(t0)}\n       後 {sp(t1)}  (スワップ {t1.swap.sum():+,.0f}p・スプレッド {t1.spr.sum():+,.0f}p)")
a0=pd.concat(P); a1=pd.concat(C); print(f"  全部: 前 {sp(a0)}\n        後 {sp(a1)}")
T,st=lot_sizing(a1,base,1,102000,leverage=2000,fixed_lot=0.01,stopout=20); print(f"  0.01ロット(費用込み) 最後 {st['最後の資金']:,}円 一番へこんだ {st['一番へこんだ資金']:,}円 落ち込み率 {st['落ち込み率']}%")
print('\n■ サンタの休み(12/20〜12/31)・寝正月(1/1〜1/5)・イカの産卵(ゴールデンウィーク 4/29〜5/6)は新しく入らない(持っている玉はそのまま)')
ok,L=bugbug(lambda mk,d: run_tai(mk,'1D','4h','1h',d,('1D','219'),**K,yasumi=True)[0], raw,'server',5,0.003)
print('  バグバグ修正機:', '全部○' if ok else [l for l in L if l.startswith('×')])
Q,_=form3(yasumi=True); Q=[cost(t,int(t.d.iloc[0])) for t in Q]; a2=pd.concat(Q)
print(f"  費用込み 休みなし {sp(a1)}\n  費用込み 休みあり {sp(a2)}")
T,st=lot_sizing(a2,base,1,102000,leverage=2000,fixed_lot=0.01,stopout=20); print(f"  0.01ロット(費用込み・休みあり) 最後 {st['最後の資金']:,}円 一番へこんだ {st['一番へこんだ資金']:,}円 落ち込み率 {st['落ち込み率']}%")
k=lambda t: set(zip(t.kind,t.ent))
gone=a1[[x not in k(a2) for x in zip(a1.kind,a1.ent)]].sort_values('ent'); new=a2[[x not in k(a1) for x in zip(a2.kind,a2.ent)]]
print(f"  休みで入らなくなった玉 {len(gone)}(勝ち{int((gone.pips>0).sum())} 負け{int((gone.pips<0).sum())}) {gone.pips.sum():+,.0f}p / 代わりに出た玉 {len(new)} {new.pips.sum():+,.0f}p")
for _,r in gone.iterrows(): print(f"    消 {r.kind} {r.ent:%Y/%m/%d %H時} {r.e:.3f} {r.pips:+.0f}p")
