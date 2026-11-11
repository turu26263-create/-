# 11-11 たくちん「日足の大山 ロウソク3本目まで921でええとここ 無視リーチ5発 次の足何発か次の足何発か入れて 最後まで何もせずに取り切ったら？」
# 【置き換え】日足921(9が21を上抜けて閉じた足)の次の日から3本の日足で5発:1本目 2発・2本目 2発・3本目 1発(各日の1時の始値)
#   「ええとこ」=その前の日足が閉じた時、まだ 9>21 で終値が9の上(売りは逆)。崩れていたらその日は入らない
#   降り=日足219(売りは921)が閉じた次の日の1時の始値だけ。利確・TS・網は無し(何もせず取り切る)。スプレッド0.3p。売りは鏡うつし
#   11-07 の「何も無し・5発」(日足921の次の日に5発まとめて)と並べる
import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *
raw=load_cached(sys.argv[1]); srv=Market(raw,'server'); SPR=0.003
D=srv.feat('1D'); H=srv.feat('1h')
def at1(day_close):                       # その日足が閉じた後の最初の1時の1時間足
    j=np.searchsorted(H.index.values, np.datetime64(day_close)+np.timedelta64(1,'h'))
    return j if j<len(H) else None
def run(d, haichi):
    up=(D.e9>D.e21).values if d>0 else (D.e9<D.e21).values; c9=(D.c>D.e9).values if d>0 else (D.c<D.e9).values
    out=[]; i=1; n=len(D)
    while i<n-1:
        if up[i] and not up[i-1]:                                     # 921 が閉じた足
            k=i+1
            while k<n and up[k]: k+=1                                  # 219 が閉じた足 k
            if k>=n: break
            jx=at1(D.k.values[k]);
            if jx is None: break
            xo=H.o.values[jx]+(0 if d>0 else SPR)
            for m,cnt in enumerate(haichi):                            # m 本目の日足で cnt 発
                q=i+m                                                  # 前の日足 q が閉じた所で見る
                if q>=k or not (up[q] and c9[q]): continue
                je=at1(D.k.values[q])
                if je is None or je>=jx: continue
                e=H.o.values[je]+(SPR if d>0 else 0)
                for _ in range(cnt): out.append(dict(ent=H.index[je],e=e,ext=H.index[jx],x=xo,pips=(xo-e)/0.01*d,why='日足219',yama=D.index[i],n=m+1))
            i=k
        else: i+=1
    return pd.DataFrame(out)
def yama_hyo(t):
    g=t.groupby('yama').agg(玉=('pips','size'),合計=('pips','sum')); return g
print('並べる2つ:A=11-07 の形(921の次の日に5発まとめて)/B=今度の形(1本目2発・2本目2発・3本目1発、ええとこだけ)')
for nm,hai in [('A 5発まとめて',(5,)),('B 2・2・1',(2,2,1))]:
    t=pd.concat([run(1,hai).assign(d=1),run(-1,hai).assign(d=-1)],ignore_index=True); y=pd.to_datetime(t.ent).dt.year
    _,st=lot_sizing(t,H,1,102000,leverage=2000,fixed_lot=0.01,stopout=20)
    g=yama_hyo(t); big=g.合計>0
    print(f"  {nm}: {len(t)}玉 {t.pips.sum():+,.0f}p 選22-24 {t.pips[y.between(2022,2024)].sum():+,.0f} 確かめる年 {t.pips[y.between(2016,2021)|(y>=2025)].sum():+,.0f} 落ち込み率 {st['落ち込み率']}% 最後 {st['最後の資金']:,}円 強制決済 {st['強制決済']}")
    print('     年ごと', {int(k):round(v) for k,v in t.groupby(y).pips.sum().items()})
    print(f'     山 {len(g)}個:勝った山 {int(big.sum())}個 +{g.合計[big].sum():,.0f}p / 負けた山 {int((~big).sum())}個 {g.合計[~big].sum():,.0f}p')
t=pd.concat([run(1,(2,2,1)).assign(d=1),run(-1,(2,2,1)).assign(d=-1)],ignore_index=True)
print('--- 歩き:B の玉(2016/10 の大山・2020年)---')
for a,b in [('2016-10-01','2016-10-31'),('2020-01-01','2020-04-30')]:
    for r in t[(t.ent>=a)&(t.ent<=b)].itertuples(): print(f"  {'買い' if r.d>0 else '売り'} {r.n}本目 {r.ent:%Y/%m/%d %H時} {r.e:.3f} → {r.ext:%m/%d %H時} {r.x:.3f} {r.pips:+.0f}p")
