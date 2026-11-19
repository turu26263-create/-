# 11-11 たくちん「どっちも遅い921がわかってない」(チャートに赤で印:週足 2021/02・2021/09・2022/03、日足 2022/03 中・2022/06 頭)
# 印の所を1本ずつ読んだ:どこも「9が21の上で、ロウソクが9の上で閉じ、帯の上と下が両方外へ開いた(上帯が上がり下帯が下がった)」最初の足
#   日足 2022/03/08(終値115.66→3/22に120.83)・日足 2022/06/01(新しい921と同じ足・130.11→6/14に135.47)・週足 2021/02/19(新921)・2021/09/24・2022/03/04
#   前のクロードの竿元(しぼんだ後に終値が+2σの外)は 2022/02/10(帯が開く前の横ばい)と 2022/07/14(開き切った後のてっぺん)で、どちらも開き始めではなかった
# 【置き換え・照らす前に決めた】開き始めの921=日足で 9>21・終値>9・上帯(+2σ)が前の足より上がり下帯(−2σ)が前の足より下がった。1本前の足がこの3つ全部ではない(始まりの足)。売りは鏡うつし
#   入り方・降りは前の竿元の照らしと同じ(開き始めで1発+4時間の9への押し目で5発まで・日足219まで取り切り)。竿元の決め方だけを替えた
import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *
raw=load_cached(sys.argv[1]); srv=Market(raw,'server'); SPR=0.003
D=srv.feat('1D'); H=srv.feat('1h')
w=(4*D.sd); sq=(w<0.7*w.shift(1).rolling(100).mean()); sq6=sq.rolling(6,min_periods=1).max().fillna(0).astype(bool).values
def at1(t):
    j=np.searchsorted(H.index.values,np.datetime64(t)+np.timedelta64(1,'h')); return j if j<len(H) else None
F4=srv.feat('4h')
def oshime(d):
    tch=(F4.l<=F4.e9)&(F4.c>F4.e9) if d>0 else (F4.h>=F4.e9)&(F4.c<F4.e9)
    prev=(F4.l.shift(1)<=F4.e9.shift(1)) if d>0 else (F4.h.shift(1)>=F4.e9.shift(1))
    return F4.k.values[(tch&~prev.fillna(False)).values]                 # 押しから戻して閉じた4時間足の閉じた時刻
def run(d,mode='oshime'):
    out_=(D.c>D.md+2*D.sd).values if d>0 else (D.c<D.md-2*D.sd).values
    c9=(D.c>D.e9).values if d>0 else (D.c<D.e9).values; up=(D.e9>D.e21).values if d>0 else (D.e9<D.e21).values
    ub=(D.md+2*D.sd).values; lb=(D.md-2*D.sd).values
    opn=np.r_[False,(ub[1:]>ub[:-1])&(lb[1:]<lb[:-1])]
    sig=up&c9&opn
    OK=oshime(d); out=[]; i=101; n=len(D)
    def put(je,jx,xo,i,m):
        e=H.o.values[je]+(SPR if d>0 else 0); out.append(dict(ent=H.index[je],e=e,ext=H.index[jx],x=xo,pips=(xo-e)/0.01*d,sao=D.index[i],n=m,d=d))
    while i<n-1:
        if sig[i] and not sig[i-1]:
            k=i+1
            while k<n and not (up[k-1] and not up[k]): k+=1
            if k>=n: break
            jx=at1(D.k.values[k]); xo=H.o.values[jx]+(0 if d>0 else SPR)
            if mode=='221':
                for m,cnt in enumerate((2,2,1)):
                    q=i+m
                    if q>=k or (m>0 and not c9[q]): continue
                    for _ in range(cnt): put(at1(D.k.values[q]),jx,xo,i,m+1)
            else:
                j0=at1(D.k.values[i]); put(j0,jx,xo,i,1); cnt=1                 # 竿元で1発
                for kk in OK[(OK>H.index.values[j0])&(OK<np.datetime64(D.k.values[k]))]:
                    if cnt>=5: break
                    je=np.searchsorted(H.index.values,kk)
                    while je<len(H) and H.index[je].hour==0: je+=1
                    if je>=jx: break
                    cnt+=1; put(je,jx,xo,i,cnt)
            i=k
        else: i+=1
    return pd.DataFrame(out)
for mode,nm in [('oshime','開き始めの921で1発+押し目で足して5発まで(前の竿元の照らしは60回 −531p・確かめる年 −6,277)')]:
  t=pd.concat([run(1,mode),run(-1,mode)],ignore_index=True); y=pd.to_datetime(t.ent).dt.year
  _,st=lot_sizing(t,H,1,102000,leverage=2000,fixed_lot=0.01,stopout=20)
  g=t.groupby(['sao','d']).agg(玉=('pips','size'),合計=('pips','sum'),降り=('ext','first')).reset_index()
  print(f"{nm}:{len(g)}回 {len(t)}玉 {t.pips.sum():+,.0f}p 選22-24 {t.pips[y.between(2022,2024)].sum():+,.0f} 確かめる年 {t.pips[y.between(2016,2021)|(y>=2025)].sum():+,.0f} 落ち込み率 {st['落ち込み率']}% 最後 {st['最後の資金']:,}円 強制決済 {st['強制決済']}")
  print('  年ごと',{int(k):round(v) for k,v in t.groupby(y).pips.sum().items()})
  w_=g.合計>0; print(f'  勝った回 {int(w_.sum())} +{g.合計[w_].sum():,.0f}p / 負けた回 {int((~w_).sum())} {g.合計[~w_].sum():,.0f}p')
print('--- 開き始めの921を全部(日付・向き・入った玉・5発の合計・降りた日)---')
for r in g.itertuples(): q=t[(t.sao==r.sao)&(t.d==r.d)]; print(f"  {r.sao:%Y/%m/%d} {'買い' if r.d>0 else '売り'} {r.玉}玉 {r.合計:+,.0f}p → {pd.Timestamp(r.降り):%Y/%m/%d} | "+' '.join(f'{x.ent:%m/%d}' for x in q.itertuples()))
# 11-07 の大山13個に竿元で入れたか
YAMA=[('下げ','2016-06-06','2016-07-19'),('上げ','2016-10-06','2017-01-13'),('上げ','2022-01-31','2022-05-25'),('上げ','2022-06-02','2022-08-01'),('上げ','2022-08-22','2022-11-10'),('下げ','2022-11-10','2023-02-09'),('上げ','2023-04-17','2023-07-13'),('上げ','2023-08-02','2023-11-21'),('上げ','2024-03-21','2024-07-17'),('下げ','2024-07-17','2024-10-03'),('上げ','2024-10-03','2024-12-02'),('下げ','2025-01-22','2025-03-28'),('上げ','2025-09-22','2026-01-27')]
print('--- 大山13個(11-07 の表):山の中で入った玉 ---')
for k,a,b in YAMA:
    dd=1 if k=='上げ' else -1; q=t[(t.d==dd)&(t.ent>=a)&(t.ent<=b)]
    print(f"  {k} {a}〜{b}: " + (f"入った {len(q)}玉 {q.pips.sum():+,.0f}p(最初 {q.ent.min():%m/%d})" if len(q) else '入らなかった'))
