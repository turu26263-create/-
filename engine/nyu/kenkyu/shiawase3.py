# 11-11 たくちん「ご」:しあわせセット=「3つ利確して1つためで残す」(かがみ無限の 鏡2・鏡H1'「上の足の+2σタッチで3単位を利確し、1単位はためとして残す」)をクジラに当てる
# 【置き換え】クジラの1発=4単位(3+ため1)。入る足は1時間なので「上の足」=4時間。4時間+2σ(売りは−2σ)に触れたら3単位を利確(その足が始まる前に閉じた4時間足の線)。
#   ため1単位は今の降りのまま(4時間4.0σ利確・TS550・日足219)。3単位も、+2σに触れる前に今の降りが来たらそこで一緒に降りる。
#   入りは今の形と同じ(1セットが降り切るまで枠を使う)。鯛・押し目巡航・ドテン買いは触らない(ドテン買いは売りのため玉の4.0σ利確で構えるので今と同じ)
# 使い方: python3 shiawase3.py <MT4 1時間足の置き場>
import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *; from bugbug import bugbug
raw=load_cached(sys.argv[1]); srv=Market(raw,'server')
K=dict(maxpos=5,n8=False,reenter=True,tp=('4h',4.0),ts=550,avoid_in=(0,),avoid_out=(0,),kai_k9=3,big21_up=True,yasumi=True)
SPR=0.003
def shiawase(mk,d,k=2.0,kowasu=False):
    t,base=run_tai(mk,'1D','4h','1h',d,('1D','219'),**K); t=t.copy()
    O,H,L=base.o.values,base.h.values,base.l.values; idx=base.index
    TP=make_tp(mk,'1h',d,('4h',k))                                    # 1本前の足が閉じた時の4時間±2σ(先読みしない)
    x3=[];t3=[];p3=[]
    for r in t.itertuples():
        j=idx.get_loc(r.ent); kx=idx.get_loc(r.ext)
        last = kx if r.why=='利確' else kx-1                            # 網・TS は同じ足では網が先(損な方)。合図の降りは合図の足まで
        hit=None
        for i in range(j+1,last+1):
            v=TP[i]
            if np.isnan(v): continue
            ok = (v>r.e) if d>0 else (v<r.e-SPR)                         # 利確の線は入り値より有利な側にある時だけ(エンジンと同じ)
            if kowasu: ok=True
            if ok and ((d>0 and H[i]>=v-1e-9) or (d<0 and L[i]<=v+1e-9)): hit=i; break
        if hit is None: x3.append(r.x); t3.append(r.ext); p3.append(r.pips)
        else:
            x=max(O[hit],TP[hit]) if d>0 else min(O[hit],TP[hit])+SPR
            x3.append(x); t3.append(idx[hit]); p3.append((x-r.e)/PIP*d)
    t['x3']=x3; t['ext3']=t3; t['pips3']=p3; t['pips1']=t.pips
    t['pips']=0.75*t.pips3+0.25*t.pips1                                   # 1セット(4単位)を1玉ぶんに直した損益
    return t,base
# ---- 関所
make=lambda mk,d: shiawase(mk,d)[0]
ok,Lg=bugbug(make,raw,'server',5,SPR); print('修正機:', '全部○' if ok else '×あり'); print('\n'.join(l for l in Lg if l.startswith('×') or 'ローソク' in l))
for nm,kw in [('今度の形',{}),('わざと壊した形(入り値より不利な所でも3単位を降ろす)',{'kowasu':True})]:
    bad=0;late=0
    for d in (1,-1):
        t,_=shiawase(srv,d,**kw); m=t.ext3!=t.ext
        bad+=int(((t.pips3<-1e-6)&m).sum()); late+=int((pd.to_datetime(t.ext3)>pd.to_datetime(t.ext)).sum())
    print(f'  {nm}: 3単位の利確で負けた {bad} / 3単位がため玉より後に降りた {late}')
b,base=shiawase(srv,1); s,_=shiawase(srv,-1)
for nm,t in [('買い',b),('売り',s)]:
    m=t.ext3!=t.ext; print(f'{nm}: {len(t)}セット・3単位を+2σで先に利確 {int(m.sum())}セット(1回平均 {t.pips3[m].mean():+.1f}p)/ +2σの前に今の降りが来た {int((~m).sum())}セット')
# ---- 歩き 2016年11月の大山(1セットずつ)
print('--- 歩き(買い)2016/10〜12 ---')
F=srv.feat('4h')
for r in b[(b.ent>='2016-10-01')&(b.ent<='2016-12-31')].itertuples():
    print(f'  {r.n}発目 {r.ent:%m/%d %H時} {r.e:.3f} → 3単位 {pd.Timestamp(r.ext3):%m/%d %H時} {r.x3:.3f} {r.pips3:+.1f}p / ため1 {r.ext:%m/%d %H時} {r.x:.3f} {r.pips1:+.1f}p {r.why} → 1玉ぶん {r.pips:+.1f}p(今の形 {r.pips1:+.1f}p)')
r=b[(b.ent>='2016-11-10')].iloc[0]; a_=pd.Timestamp(r.ent).floor('4h')
for ts,q in F[a_-pd.Timedelta('8h'):a_+pd.Timedelta('2D')].iterrows():
    print(f'    4時間 {ts:%m/%d %H時} 高値 {q.h:.3f} 終値 {q.c:.3f} +2σ {q.md+2*q.sd:.3f}{"  ← 高値が+2σに届いた" if q.h>=q.md+2*q.sd else ""}')
# ---- 数字(今の形と、1つだけ変えた形の2行)
def blend(sh):
    if sh: bb,base=shiawase(srv,1); ss,_=shiawase(srv,-1)
    else:
        bb,base=run_tai(srv,'1D','4h','1h',1,('1D','219'),**K); ss,_=run_tai(srv,'1D','4h','1h',-1,('1D','219'),**K)
        for t in (bb,ss): t['ext3']=t.ext; t['x3']=t.x; t['pips3']=t.pips; t['pips1']=t.pips
    dt,_=run_doten(srv,1,xtf='4h',**K); tb,_=run_tai(srv,'1D','4h','1h',1,('4h','9割れ'),**{**K,'maxpos':1,'tp':None}); ob,_=run_oshime_d(srv,1); os_,_=run_oshime_d(srv,-1)
    rows=[]
    for t,k,d in [(bb,'買い',1),(ss,'売り',-1)]:
        for _ in range(3): rows.append(t.assign(ext=t.ext3,x=t.x3,pips=t.pips3,kind=k,d=d))   # 3単位
        rows.append(t.assign(pips=t.pips1,kind=k,d=d))                                            # ため1単位
    for t,k,d in [(dt,'ドテン買い',1),(tb,'鯛',1),(ob,'押し目買い',1),(os_,'押し目売り',-1)]:
        for _ in range(4): rows.append(t.assign(kind=k,d=d))
    T=pd.concat(rows,ignore_index=True); T_,st=lot_sizing(T,base,1,102000,leverage=2000,fixed_lot=0.0025,min_lot=0.0025,step=0.0025,stopout=20)
    T['p']=T.pips/4; return T,st                                                                  # 4行で1玉ぶん
print('決め方(先に決めた・前と同じ):確かめる年の合計が上がり、落ち込み率が上がらなければ残す')
for nm,sh in [('今の形',False),('しあわせセット(4時間+2σで3単位利確・ため1は今の降り)',True)]:
    T,st=blend(sh); y=pd.to_datetime(T.ent).dt.year
    f=lambda k: f"{int((T.kind==k).sum()/4)}玉 {T.p[T.kind==k].sum():+,.0f}p"
    print(f"  {nm}:\n     買い {f('買い')} / 売り {f('売り')} / ドテン買い {f('ドテン買い')} / 全部 {int(len(T)/4)}玉 {T.p.sum():+,.0f}p 選22-24 {T.p[y.between(2022,2024)].sum():+,.0f} 確かめる年 {T.p[y.between(2016,2021)|(y>=2025)].sum():+,.0f} 落ち込み率 {st['落ち込み率']}% 最後 {st['最後の資金']:,}円")
