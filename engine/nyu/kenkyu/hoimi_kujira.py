# 11-11 たくちん「おれのリアル手法みて学習して しあわせセット行けるはず」
# リアル手法(呪文の書 ホイミ=鏡打ち ✋+1,581.72円 09-28/昨日式の前提書き/鏡=スクルト):
#   5分足921の上で、1分足−2σに届いて戻る所で3発 → 上の鏡(+2σ)で2発利確 → 1発残して積み重ね。全玉の網は直近の押し目安値の少し下(3〜5p)、押しで足すたびに引き上げる
# 【置き換え】足を1段ずつ上げてクジラの許しの中に置く(5分:1分=5倍 → 4時間:1時間=4倍)
#   許し=クジラと同じ(日足の終値が9の上・4時間の終値が21の上・日足21が上向き)/流れ=4時間9>21で9が上向き
#   入り=1時間足の安値が−2σに届き、終値が−2σの内に戻って閉じた足 → 次の足で1セット3単位
#   2単位=1時間+2σで利確/1単位(ため)=クジラの降り(4時間4.0σ利確・TS550・日足219)
#   網=全単位:直近の「−2σに届いた足」の安値の5p下。新しく届いた足が出るたび引き上げる(下げない)
#   ためは最大5セット(クジラ5発と同じ)。0時は1時へ・GWは入らない。売りは鏡うつし
import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *; from tai_parts import _mae1; from bugbug import bugbug
raw=load_cached(sys.argv[1]); srv=Market(raw,'server'); SPR=0.003
K=dict(maxpos=5,n8=False,reenter=True,tp=('4h',4.0),ts=550,avoid_in=(0,),avoid_out=(0,),kai_k9=3,big21_up=True,yasumi=True)
def hoimi_sig(mk,d):
    x=mk.feat('1h'); lo=x.md-2*x.sd; hi=x.md+2*x.sd
    touch=((x.l<=lo)&(x.c>lo)) if d>0 else ((x.h>=hi)&(x.c<hi))
    F=mk.feat('4h'); kc='hm_b' if d>0 else 'hm_s'
    if kc not in F.columns: mk._f['4h']=F.assign(**{kc:((F.e9>F.e21)&(F.e9>F.e9.shift(1))) if d>0 else ((F.e9<F.e21)&(F.e9<F.e9.shift(1)))})
    fl=mk.on('1h','4h',[kc])[kc].fillna(False).astype(bool).values
    D=mk.on('1h','1D',['c','e9','ang']); M=mk.on('1h','4h',['c','e21'])
    perm=((D.c>D.e9)&(M.c>M.e21)&(D.ang>0)) if d>0 else ((D.c<D.e9)&(M.c<M.e21)&(D.ang<0))
    E=touch.values&fl&perm.fillna(False).values
    net=pd.Series(np.where(touch.values,(x.l-0.05*1).values if d>0 else (x.h+0.05).values,np.nan),index=x.index).ffill().values
    return E, net
def hoimi(mk,d,kowasu=False):
    E,net=hoimi_sig(mk,d); base=mk.feat('1h'); idx=base.index
    E=E&~yasumi_mask(idx)
    fh=np.r_[idx.hour.values[1:],-1]; E=E.copy()
    for i in np.where(E&(fh==0))[0]: E[i]=False; E[min(i+1,len(E)-2)]=True
    XC,KC=EXITS['219'](mk,'1h','1D',d); XC=np.asarray(XC,bool)&~(fh==0)
    SL=_mae1(net)                                                      # 網は閉じた足の値だけ(1本前まで)
    if kowasu: SL=net                                                  # わざと壊す:いま動いている足の安値で網を決める
    B=simulate(base,d,E,XC,KC,None,None,SL,5,SPR,True,make_tp(mk,'1h',d,('4h',4.0)),0.0,True,550.0,0.0)   # ため1単位(枠を持つ)
    EB=np.zeros(len(idx),bool); EB[np.searchsorted(idx.values,pd.to_datetime(B.ent).values)-1]=True
    A=simulate(base,d,EB,XC,KC,None,None,SL,15,SPR,True,make_tp(mk,'1h',d,('1h',2.0)),0.0,True,0.0,0.0)   # 刈る2単位(ためと同じ足で入る)
    return A,B,base
# ---- 関所
for nm,role in [('刈る2単位','A'),('ため1単位','B')]:
    ok,Lg=bugbug(lambda mk,d: hoimi(mk,d)[0 if role=='A' else 1],raw,'server',15 if role=='A' else 5,SPR)
    print(f'修正機({nm}):','全部○' if ok else '×あり'); [print('  ',l) for l in Lg if l.startswith('×')]
for nm,kw in [('今度の形',{}),('わざと壊した形(いま動いている足の安値で網)',{'kowasu':True})]:
    ok,Lg=bugbug(lambda mk,d: hoimi(mk,d,**kw)[0],raw,'server',15,SPR); print(f'  {nm}: 修正機', '全部○' if ok else '×を出した '+'/'.join(l[:40] for l in Lg if l.startswith('×')))
for d,nm in [(1,'買い'),(-1,'売り')]:
    A,B,_=hoimi(srv,d); print(f'{nm}: {len(B)}セット / 刈る単位 {len(A)} 利確 {int((A.why=="利確").sum())} 網 {int((A.why=="網").sum())} 平均 {A.pips.mean():+.1f}p / ため 平均 {B.pips.mean():+.1f}p 降り {B.why.value_counts().to_dict()}')
# ---- 歩き 2016/10〜11 の大山(買い)
A,B,base=hoimi(srv,1); x=srv.feat('1h')
print('--- 歩き(買い)2016/10/01〜11/30 ---')
for r in B[(B.ent>='2016-10-01')&(B.ent<='2016-11-30')].itertuples():
    a=A[A.ent==r.ent]
    print(f'  {r.ent:%m/%d %H時} {r.e:.3f}(合図の足 安値 {x.l.shift(1)[r.ent]:.3f} −2σ {(x.md-2*x.sd).shift(1)[r.ent]:.3f}) 刈る2単位 '+' / '.join(f'{q.ext:%m/%d %H時} {q.pips:+.0f}p {q.why}' for q in a.itertuples())+f' | ため {r.ext:%m/%d %H時} {r.pips:+.0f}p {r.why}')
# ---- 数字(今の形と、ホイミを足した形の2行)
def blend(add):
    b,base=run_tai(srv,'1D','4h','1h',1,('1D','219'),**K); s,_=run_tai(srv,'1D','4h','1h',-1,('1D','219'),**K); dt,_=run_doten(srv,1,xtf='4h',**K)
    tb,_=run_tai(srv,'1D','4h','1h',1,('4h','9割れ'),**{**K,'maxpos':1,'tp':None}); ob,_=run_oshime_d(srv,1); os_,_=run_oshime_d(srv,-1)
    rows=[]
    for t,k,d in [(b,'買い',1),(s,'売り',-1),(dt,'ドテン買い',1),(tb,'鯛',1),(ob,'押し目買い',1),(os_,'押し目売り',-1)]: rows+=[t.assign(kind=k,d=d)]*3   # 0.01ロット=3行(1行0.01/3)
    if add:
        for d,k in [(1,'ホイミ買い'),(-1,'ホイミ売り')]:
            A,B,_=hoimi(srv,d); rows+=[A.assign(kind=k,d=d),A.assign(kind=k,d=d),B.assign(kind=k,d=d)]   # 1セット=刈る2+ため1=0.01ロットぶん
    T=pd.concat(rows,ignore_index=True); L=0.01/3
    _,st=lot_sizing(T,base,1,102000,leverage=2000,fixed_lot=L,min_lot=L,step=L,stopout=20)
    T['p']=T.pips/3; return T,st
print('決め方(先に決めた・前と同じ):確かめる年の合計が上がり、落ち込み率が上がらなければ残す。ホイミは1セット(3単位)=0.01ロットぶん')
for nm,add in [('今の形',False),('今の形+ホイミ(クジラの許しの中の鏡打ち・2刈り1ため)',True)]:
    T,st=blend(add); y=pd.to_datetime(T.ent).dt.year
    f=lambda k: f"{T.p[T.kind==k].sum():+,.0f}p"
    print(f"  {nm}:\n     全部 {T.p.sum():+,.0f}p 選22-24 {T.p[y.between(2022,2024)].sum():+,.0f} 確かめる年 {T.p[y.between(2016,2021)|(y>=2025)].sum():+,.0f} 落ち込み率 {st['落ち込み率']}% 最後 {st['最後の資金']:,}円 / ホイミ買い {f('ホイミ買い')} ホイミ売り {f('ホイミ売り')}")
