# 11-11 たくちん「竿元からはいらんと意味がない」「押し目とか」 → 竿元で1発、そのあと押し目で足して5発まで、日足219まで取り切り
#   押し目【置き換え】=4時間足の安値が4時間の9に触れ、終値が9の上で閉じた足(売りは逆)。1本前の4時間足は9に触れていない(新しい押し)。その次の1時間足の始値で1発(0時は1時へ)
#   (リアル:2022年の3山は 打診の後、最初の押しで大玉 → 小さく足す → 全部ついて行く網。ここでは玉の大きさは同じ0.01のまま、入る所だけまねる)
# 竿元=竿の根っこ(たくちん 10-29「入るのはレンジのあとbbしぼんだ後のバンドブレイクが竿根っこやで」)
# 【置き換え】日足の竿元=日足の帯(±2σの幅)が直前6本のどこかで、ふだん(その前100本の平均)の0.7倍より狭くしぼみ、終値が+2σの外で閉じた最初の1本(売りは−2σの外)(決まり帳 根1 の日足版)
#   入り:竿元の足が閉じた次の日から3本で 2・2・1発(各日の1時の始値)。2・3本目は前の日足の終値がまだ9の上の時だけ(売りは下)
#   降り:入った後に新しく出た日足219(売りは921)が閉じた次の日の1時の始値だけ。利確・TS・網は無し(何もせず取り切る)。スプレッド0.3p
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
    OK=oshime(d); out=[]; i=101; n=len(D)
    def put(je,jx,xo,i,m):
        e=H.o.values[je]+(SPR if d>0 else 0); out.append(dict(ent=H.index[je],e=e,ext=H.index[jx],x=xo,pips=(xo-e)/0.01*d,sao=D.index[i],n=m,d=d))
    while i<n-1:
        if out_[i] and not out_[i-1] and sq6[i-1]:
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
for mode,nm in [('221','前の形(竿元から3日で2・2・1発)'),('oshime','竿元で1発+押し目で足して5発まで')]:
  t=pd.concat([run(1,mode),run(-1,mode)],ignore_index=True); y=pd.to_datetime(t.ent).dt.year
  _,st=lot_sizing(t,H,1,102000,leverage=2000,fixed_lot=0.01,stopout=20)
  g=t.groupby(['sao','d']).agg(玉=('pips','size'),合計=('pips','sum'),降り=('ext','first')).reset_index()
  print(f"{nm}:{len(g)}回 {len(t)}玉 {t.pips.sum():+,.0f}p 選22-24 {t.pips[y.between(2022,2024)].sum():+,.0f} 確かめる年 {t.pips[y.between(2016,2021)|(y>=2025)].sum():+,.0f} 落ち込み率 {st['落ち込み率']}% 最後 {st['最後の資金']:,}円 強制決済 {st['強制決済']}")
  print('  年ごと',{int(k):round(v) for k,v in t.groupby(y).pips.sum().items()})
  w_=g.合計>0; print(f'  勝った回 {int(w_.sum())} +{g.合計[w_].sum():,.0f}p / 負けた回 {int((~w_).sum())} {g.合計[~w_].sum():,.0f}p')
print('--- 竿元を全部(日付・向き・入った玉・5発の合計・降りた日)---')
for r in g.itertuples(): q=t[(t.sao==r.sao)&(t.d==r.d)]; print(f"  {r.sao:%Y/%m/%d} {'買い' if r.d>0 else '売り'} {r.玉}玉 {r.合計:+,.0f}p → {pd.Timestamp(r.降り):%Y/%m/%d} | "+' '.join(f'{x.ent:%m/%d}' for x in q.itertuples()))
# 11-07 の大山13個に竿元で入れたか
YAMA=[('下げ','2016-06-06','2016-07-19'),('上げ','2016-10-06','2017-01-13'),('上げ','2022-01-31','2022-05-25'),('上げ','2022-06-02','2022-08-01'),('上げ','2022-08-22','2022-11-10'),('下げ','2022-11-10','2023-02-09'),('上げ','2023-04-17','2023-07-13'),('上げ','2023-08-02','2023-11-21'),('上げ','2024-03-21','2024-07-17'),('下げ','2024-07-17','2024-10-03'),('上げ','2024-10-03','2024-12-02'),('下げ','2025-01-22','2025-03-28'),('上げ','2025-09-22','2026-01-27')]
print('--- 大山13個(11-07 の表)のうち、山の中で竿元の玉が入ったか ---')
for k,a,b in YAMA:
    dd=1 if k=='上げ' else -1; q=t[(t.d==dd)&(t.ent>=a)&(t.ent<=b)]
    print(f"  {k} {a}〜{b}: " + (f"入った {len(q)}玉 {q.pips.sum():+,.0f}p(最初 {q.ent.min():%m/%d})" if len(q) else '竿元なし'))
