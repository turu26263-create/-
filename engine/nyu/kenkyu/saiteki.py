import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *
srv=Market(load_cached(sys.argv[1]),'server')
P0=dict(tp=3.5,ts=550,sao=2.0,k9=3,maxpos=5,pk=10,wk=3,tpk=3.5)
def blend(P):
    K=dict(maxpos=P['maxpos'],n8=False,reenter=True,tp=('4h',P['tp']),ts=P['ts'],sao=P['sao'],avoid_in=(0,),avoid_out=(0,),kai_k9=P['k9'],big21_up=True,yasumi=True)
    b,base=run_tai(srv,'1D','4h','1h',1,('1D','219'),**K); s,_=run_tai(srv,'1D','4h','1h',-1,('1D','219'),**K); dt,_=run_doten(srv,1,xtf='4h',**K)
    tb,_=run_tai(srv,'1D','4h','1h',1,('4h','9割れ'),**{**K,'maxpos':1,'tp':None}); ob,_=run_oshime_d(srv,1,pk=P['pk'],wk=P['wk'],tpk=P['tpk']); os_,_=run_oshime_d(srv,-1,pk=P['pk'],wk=P['wk'],tpk=P['tpk'])
    for t,d in [(b,1),(s,-1),(dt,1),(tb,1),(ob,1),(os_,-1)]: t['d']=d
    t=pd.concat([b,s,dt,tb,ob,os_],ignore_index=True); y=pd.to_datetime(t.ent).dt.year
    T_,st=lot_sizing(t,base,1,102000,leverage=2000,fixed_lot=0.01,stopout=20)
    return dict(n=len(t),sum=t.pips.sum(),sen=t.pips[y.between(2022,2024)].sum(),kak=t.pips[y.between(2016,2021)|(y>=2025)].sum(),dd=st['落ち込み率'])
NM=dict(tp='利確 4時間±σ',ts='TS(p)',sao='竿先 1時間±σ',k9='許しは日足9に乗って何本目から',maxpos='クジラ何発',pk='押し目巡航:前の山を見る日数',wk='押し目巡航:帯の開きを比べる日数',tpk='押し目巡航:利確 日足±σ')
G=dict(tp=[2.5,3.0,3.5,4.0,4.5],ts=[350,450,550,650,750],sao=[1.5,1.75,2.0,2.25,2.5],k9=[1,2,3,4,5],maxpos=[3,4,5,6,7],pk=[6,8,10,12,14],wk=[1,2,3,4,5],tpk=[2.5,3.0,3.5,4.0,4.5])
print('ミナデイン最適化:【置き換え】の数字を1つずつ前後に動かした(ほかは今のまま。かけ合わせはしない)')
print('決め方(先に決めた):①選ぶ年(22-24)で今より良い ②その両隣も今以上(台地。端は片隣)③確かめる年(16-21・25-26)の合計が今以上 ④落ち込み率が今以下。4つとも○の数字だけ「候補」\n')
base0=blend(P0); print(f"今:{base0['n']}玉 {base0['sum']:+,.0f}p 選22-24 {base0['sen']:+,.0f} 確かめる年 {base0['kak']:+,.0f} 落ち込み率 {base0['dd']}%\n")
for k,vals in ({} if len(sys.argv)>2 else G).items():
    R=[blend({**P0,k:v}) for v in vals]; print(f"■ {NM[k]}(今 {P0[k]})")
    for i,(v,r) in enumerate(zip(vals,R)):
        tag=''
        if v==P0[k]: tag='← 今'
        else:
            nb=[R[j] for j in (i-1,i+1) if 0<=j<len(R)]
            c1=r['sen']>base0['sen']; c2=all(x['sen']>=base0['sen'] for x in nb); c3=r['kak']>=base0['kak']; c4=r['dd']<=base0['dd']
            tag=('★候補' if (c1 and c2 and c3 and c4) else '')+f"  ①{'○' if c1 else '×'}②{'○' if c2 else '×'}③{'○' if c3 else '×'}④{'○' if c4 else '×'}"
        print(f"   {v:>5}: {r['n']:>4}玉 {r['sum']:>+8,.0f}p 選22-24 {r['sen']:>+7,.0f} 確かめる年 {r['kak']:>+7,.0f} 落ち込み率 {r['dd']:>4}% {tag}")
    print()
print('■ 利確の台地を細かく確かめる(3.75・4.0・4.25)')
for v in (3.5,3.75,4.0,4.25,4.5):
    r=blend({**P0,'tp':v}); print(f"   {v:>5}: {r['n']:>4}玉 {r['sum']:>+8,.0f}p 選22-24 {r['sen']:>+7,.0f} 確かめる年 {r['kak']:>+7,.0f} 落ち込み率 {r['dd']:>4}%")
