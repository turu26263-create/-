# 11-11 たくちん「竿先レンジ、しあわせセット MacＤ使ったらしあわせセット出来るやろ bb-2で買う4 bb2でさんりかく ためて、うえとびまち」
# 【置き換え】
#   竿先=クジラの許し(日足の終値が9の上・4時間の終値が21の上・日足21が上向き)の中で、直近6本の4時間足のどれかの終値が+2σの外(売りは逆)
#   レンジの差し込み=1時間足の安値が−2σに届いた(この足か2本前まで)
#   MACD=1時間足 12・26・9。ヒストグラムが下げ止まって上を向いた足(この足>1本前、1本前<=2本前)で閉じたら、次の足の始値で4単位(反転の瞬間を MACD で見る。前の照らしは−2σに届いた所で買い、刺さる途中で網に掛かっていた)
#   3単位=1時間+2σで利確/ため1単位=上飛び待ち(クジラの降り:4時間4.0σ・TS550・日足219)
#   網=全単位、入った時は1時間−3σ、巡航上昇で9の1p下に連れ上がる(たくちんの b1)
#   次のセットは前のセットの3単位を利確した後だけ/ためは最大5セット/売りは鏡うつし/0時は入らない・GWは入らない
import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *; from tai_parts import _mae1
raw=load_cached(sys.argv[1]); SPR=0.003; P=0.01
K=dict(maxpos=5,n8=False,reenter=True,tp=('4h',4.0),ts=550,avoid_in=(0,),avoid_out=(0,),kai_k9=3,big21_up=True,yasumi=True)
def hoimi(mk,d,kowasu=False):
    x=mk.feat('1h'); idx=x.index; n=len(x)
    O,H,L,C,E9=x.o.values,x.h.values,x.l.values,x.c.values,x.e9.values
    md,sd=x.md.values,x.sd.values
    F=mk.feat('4h'); kc='hm_b' if d>0 else 'hm_s'
    if kc not in F.columns: mk._f['4h']=F.assign(**{kc:((F.e9>F.e21)&(F.e9>F.e9.shift(1))) if d>0 else ((F.e9<F.e21)&(F.e9<F.e9.shift(1)))})
    fl=mk.on('1h','4h',[kc])[kc].fillna(False).astype(bool).values
    D=mk.on('1h','1D',['c','e9','ang']); M=mk.on('1h','4h',['c','e21'])
    ok=(((D.c>D.e9)&(M.c>M.e21)&(D.ang>0)) if d>0 else ((D.c<D.e9)&(M.c<M.e21)&(D.ang<0))).fillna(False).values & fl
    T4=make_tp(mk,'1h',d,('4h',4.0)); X219,K219=EXITS['219'](mk,'1h','1D',d); X219=np.asarray(X219,bool); K219=pd.to_datetime(K219).values.astype('datetime64[ns]').astype(np.int64)
    yas=yasumi_mask(idx); hr=idx.hour.values
    up3=(pd.Series(L).diff()>0)&(pd.Series(C).diff()>0); cru=(up3&up3.shift(1,fill_value=False)&up3.shift(2,fill_value=False)).values&((C>E9) if d>0 else (C<E9))
    if d<0: cru=((pd.Series(H).diff()<0)&(pd.Series(C).diff()<0)); cru=(cru&cru.shift(1,fill_value=False)&cru.shift(2,fill_value=False)).values&(C<E9)
    bo=(x.c>x.md+2*x.sd) if False else None
    F4=mk.feat('4h'); kz='sao_b' if d>0 else 'sao_s'
    if kz not in F4.columns: mk._f['4h']=F4.assign(**{kz:((F4.c>F4.md+2*F4.sd) if d>0 else (F4.c<F4.md-2*F4.sd)).rolling(6,min_periods=1).max().astype(bool)})
    sao=mk.on('1h','4h',[kz])[kz].fillna(False).astype(bool).values
    lo2=md-2*d*sd; tch=(L<=lo2) if d>0 else (H>=lo2)
    dip=pd.Series(tch).rolling(3,min_periods=1).max().astype(bool).values
    m=ema(x.c,12)-ema(x.c,26); hist=(m-ema(m,9)).values*d
    turn=np.r_[False,False,(hist[2:]>hist[1:-1])&(hist[1:-1]<=hist[:-2])]
    if kowasu: turn=np.r_[turn[1:],False]                              # わざと壊す:次の足の MACD を先に見る
    pos=[]; out=[]; pair_open=False; T=idx.values.astype('datetime64[ns]').astype(np.int64)
    for i in range(30,n-1):
        lvl=md[i-1]-2*d*sd[i-1]; net0=md[i-1]-3*d*sd[i-1]; tp2=md[i-1]+2*d*sd[i-1]
        
        trail=(E9[i-1]-d*P) if cru[i-1] else np.nan                  # 1本前に閉じた足で巡航なら9の1p下
        # 持っている玉
        keep=[]
        for p in pos:
            if i>p['j'] and not np.isnan(trail): p['net']=max(p['net'],trail) if d>0 else min(p['net'],trail)
            ex=None
            if i>p['j'] and ((d>0 and L[i]<=p['net']) or (d<0 and H[i]>=p['net'])):
                ex=(min(O[i],p['net']) if d>0 else max(O[i],p['net'])+SPR,'網')
            elif i>p['j']:
                tv=tp2 if p['r']=='刈る' else T4[i]
                if not np.isnan(tv) and ((d>0 and tv>p['e'] and H[i]>=tv) or (d<0 and tv<p['e']-SPR and L[i]<=tv)): ex=(max(O[i],tv) if d>0 else min(O[i],tv)+SPR,'利確')
                elif p['r']=='ため':
                    p['mx']=max(p['mx'],H[i]) if d>0 else min(p['mx'],L[i])
                    ts=p['mx']-d*5.50
                    if (d>0 and L[i]<=ts and ts>p['net']) or (d<0 and H[i]>=ts and ts<p['net']): ex=(min(O[i],ts) if d>0 else max(O[i],ts)+SPR,'TS')
            if ex is None and i>p['j'] and X219[i] and K219[i]>T[p['j']] and hr[i+1]!=0: ex=(O[i+1]+(0 if d>0 else SPR),'日足219'); xi=i+1
            else: xi=i
            if ex: out.append(dict(ent=idx[p['j']],e=p['e'],ext=idx[xi],x=ex[0],pips=(ex[0]-p['e'])/P*d,why=ex[1],r=p['r'],set=p['s'],mfe=(p['mx']-p['e'])/P*d))
            else: keep.append(p)
        pos=keep
        if pair_open and not any(p['r']=='刈る' for p in pos): pair_open=False
        # 入り:1本前に閉じた足で 竿先・差し込み・MACD の向き変わり → この足の始値
        nt=sum(1 for p in pos if p['r']=='ため')
        k=i-1
        if ok[k] and sao[k] and dip[k] and turn[k] and not pair_open and nt<5 and not yas[k] and hr[i]!=0:
            e=O[i]+(SPR if d>0 else 0.0); net0=md[k]-3*d*sd[k]
            if (d>0 and net0<e) or (d<0 and net0>e):
                for r in ('刈る','刈る','刈る','ため'): pos.append(dict(j=i,e=e,net=net0,r=r,s=i,mx=e))
                pair_open=True
    t=pd.DataFrame(out); t.attrs['open']=len(pos); return t
srv=Market(raw,'server')
# ---- 関所:鏡(上下ひっくり返して買い=元の売り)/先読み(途中で切って前の玉が同じ)/わざと壊した形
mir=Market(mirror_raw(raw),'server')
a=hoimi(srv,-1); b=hoimi(mir,1)
print('鏡:', '○ 同じ' if len(a)==len(b) and np.allclose(np.sort(a.pips.values),np.sort(b.pips.values),atol=1e-6) else f'× 売り{len(a)} 鏡の買い{len(b)}')
for cut in ['2019-06-01','2023-01-01']:
    c=Market(raw[:cut],'server'); full=hoimi(srv,1); part=hoimi(c,1)
    f2=full[full.ext<pd.Timestamp(cut)-pd.Timedelta('3D')]; p2=part[part.ext<pd.Timestamp(cut)-pd.Timedelta('3D')]
    print(f'先読み({cut}で切る):', '○ 前の玉が同じ' if len(f2)==len(p2) and np.allclose(f2.pips.values,p2.pips.values) else f'× {len(f2)} vs {len(p2)}')
kw=hoimi(srv,1,kowasu=True); c=Market(raw[:'2019-06-01'],'server'); kp=hoimi(c,1,kowasu=True)
f2=kw[kw.ext<'2019-05-28']; p2=kp[kp.ext<'2019-05-28']
print('わざと壊した形(次の足の MACD を先に見る):', '×を出した' if not (len(f2)==len(p2) and np.allclose(f2.pips.values,p2.pips.values)) else '×を出さない(この照らしでは拾えない型)')
for d,nm in [(1,'買い'),(-1,'売り')]:
    t=hoimi(srv,d); A=t[t.r=='刈る']; B=t[t.r=='ため']
    print(f'{nm}: {len(B)}セット / 刈る {len(A)} 単位 平均 {A.pips.mean():+.1f}p {A.why.value_counts().to_dict()} / ため 平均 {B.pips.mean():+.1f}p {B.why.value_counts().to_dict()} / 利確で負け {int(((t.why=="利確")&(t.pips<0)).sum())}')
# ---- 歩き 2016/10〜11(買い)
t=hoimi(srv,1); x=srv.feat('1h')
print('--- 歩き(買い)2016/10/01〜11/30 ---')
for s_,g in t[(t.ent>='2016-10-01')&(t.ent<='2016-11-30')].groupby('set',sort=False):
    r=g.iloc[0]; A=g[g.r=='刈る']; B=g[g.r=='ため'].iloc[0]
    print(f'  {r.ent:%m/%d %H時} 買い {r.e:.3f}(1本前の安値 {x.l.shift(1)[r.ent]:.3f}・−2σ {(x.md-2*x.sd).shift(1)[r.ent]:.3f}) 刈る3 {A.ext.iloc[0]:%m/%d %H時} {A.pips.iloc[0]:+.0f}p {A.why.iloc[0]} | ため {B.ext:%m/%d %H時} {B.pips:+.0f}p {B.why}')
# ---- 数字(今の形と、ホイミを足した形の2行)
def blend(add):
    b,base=run_tai(srv,'1D','4h','1h',1,('1D','219'),**K); s,_=run_tai(srv,'1D','4h','1h',-1,('1D','219'),**K); dt,_=run_doten(srv,1,xtf='4h',**K)
    tb,_=run_tai(srv,'1D','4h','1h',1,('4h','9割れ'),**{**K,'maxpos':1,'tp':None}); ob,_=run_oshime_d(srv,1); os_,_=run_oshime_d(srv,-1)
    rows=[]
    for t,k,d in [(b,'買い',1),(s,'売り',-1),(dt,'ドテン買い',1),(tb,'鯛',1),(ob,'押し目買い',1),(os_,'押し目売り',-1)]: rows+=[t.assign(kind=k,d=d)]*4
    if add:
        for d,k in [(1,'しあわせ買い'),(-1,'しあわせ売り')]: rows+=[hoimi(srv,d).assign(kind=k,d=d)]
    T=pd.concat(rows,ignore_index=True); L=0.0025
    _,st=lot_sizing(T,base,1,102000,leverage=2000,fixed_lot=L,min_lot=L,step=L,stopout=20)
    T['p']=T.pips/4; return T,st
print('決め方(先に決めた・前と同じ):確かめる年の合計が上がり、落ち込み率が上がらなければ残す。しあわせセットは1セット(4単位)=0.01ロットぶん')
for nm,add in [('今の形',False),('今の形+竿先レンジのしあわせセット(MACD・4買い・3刈り・1ため)',True)]:
    T,st=blend(add); y=pd.to_datetime(T.ent).dt.year
    f=lambda k: f"{T.p[T.kind==k].sum():+,.0f}p"
    print(f"  {nm}:\n     全部 {T.p.sum():+,.0f}p 選22-24 {T.p[y.between(2022,2024)].sum():+,.0f} 確かめる年 {T.p[y.between(2016,2021)|(y>=2025)].sum():+,.0f} 落ち込み率 {st['落ち込み率']}% 最後 {st['最後の資金']:,}円 / しあわせ買い {f('しあわせ買い')} しあわせ売り {f('しあわせ売り')}")
