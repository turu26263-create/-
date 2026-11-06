# ターボエンジンの照らしを1本で(11-06 たくちん「まずはぶん回しエンジンつくりきる ぶん回しturboエンジンにする」)
# 回帰(前の数字が同じか)・ええやつ帳・暴走チェック・新しい部品の確かめ・並べて回しても同じか・速さ
# 使い方: python3 test_all.py <HistData 1分足の置き場> <MT4 1時間足の置き場>
import sys, time, warnings; warnings.filterwarnings('ignore')
from nyu import *; from tai_parts import *
H, M = sys.argv[1], sys.argv[2]; ok = []; T0 = time.time()
def chk(nm, got, want):
    g = (got['n'], round(got['sum'], 1)); good = g == want; ok.append(good)
    print(f"{'○' if good else '×'} {nm}: {g[0]}玉 {g[1]:+.1f}p (期待 {want[0]}玉 {want[1]:+.1f}p)")
t0 = time.time(); raw_e = load_cached(H); raw_s = load_cached(M); print(f'読み込み(しまい場所から) {time.time()-t0:.1f}秒')
est = Market(raw_e, 'est'); srv = Market(raw_s, 'server')
print('--- 回帰 ---')
chk('4時間版の鯛 買い縄8', stat(run_tai(est,'4h','1h','5min',1,('1h','9割れ'),n8=True)[0]), (1969, 3910.8))
chk('4時間版の鯛 売り', stat(run_tai(est,'4h','1h','5min',-1,('1h','9割れ'))[0]), (1820, 683.4))
chk('日足版の鯛 買い縄8', stat(run_tai(est,'1D','4h','1h',1,('4h','9割れ'),n8=True)[0]), (265, 3040.5))
chk('日足クジラ20発', stat(run_tai(est,'1D','4h','1h',1,('1D','9割れ'),maxpos=20,n8=True,reenter=True)[0]), (284, 7942.2))
print('--- ええやつ帳 ---')
DA = ('2025-09-19', '2026-01-27'); FA = ('2021-03-26', '2025-04-15 18:00')
chk('クジラ5発 日足の大山', stat(hitoyama(run_tai(srv,'1D','4h','1h',1,('1D','219'),maxpos=5,n8=True,reenter=True)[0],*DA)), (5, 1936.7))
chk('クジラ5発 450hの大山', stat(hitoyama(run_tai(srv,'450h','1D','1h',1,('450h','219'),maxpos=5,n8=True,reenter=True)[0],*FA)), (5, 16604.3))
chk('上の小魚 日足の大山', stat(hitoyama(kozakana_ue(srv,1,5)[0],*DA)), (30, 217.4))
chk('上の小魚 450hの大山', stat(hitoyama(kozakana_ue(srv,1,5)[0],*FA)), (534, 5400.2))
chk('逆目99 4h 日足の大山', stat(hitoyama(gyakume_99(srv,'4h',-1)[0],*DA)), (28, 702.1))
chk('鯛 日足段 買い spr1.0', stat(run_tai(est,'1D','4h','1h',1,('4h','9割れ'),n8=True,spr=0.01)[0]), (265, 2855.0))
chk('クジラmix 日足段 spr1.0', stat(run_tai(est,'1D','4h','1h',1,('1D','9割れ'),('4h','9割れ'),5,n8=True,spr=0.01,reenter=True)[0]), (284, 6051.9))
chk('鯛 4h段 売り spr1.0', stat(run_tai(est,'4h','1h','5min',-1,('1h','9割れ'),spr=0.01)[0]), (1820, 1957.4))
chk('決まった形(クジラ5発・4h3.5σ利確・TS550・日足219)', stat(run_tai(srv,'1D','4h','1h',1,('1D','219'),maxpos=5,n8=True,reenter=True,tp=('4h',3.5),ts=550)[0]), (291, 12448.3))
chk('日足クジラ5発 全期間(MT4)', stat(run_tai(srv,'1D','4h','1h',1,('1D','219'),maxpos=5,n8=True,reenter=True)[0]), (220, 11688.7))
print('--- 暴走チェック ---')
res, full = bousou(lambda r: run_tai(Market(r,'server'),'1D','4h','1h',1,('1D','219'),maxpos=5,n8=True,reenter=True,lock=50,tp=('1D',3.5))[0], raw_s, ['2018-06-01','2021-06-01','2024-01-10'])
g = all(s for _, _, s in res) and full.attrs['maxheld'] <= 5; ok.append(g)
print(f"{'○' if g else '×'} クジラ5発+しあわせセット+利確 で先読みなし:", ' '.join(f"{c} {n}玉 {'同じ' if s else '違う'}" for c, n, s in res), '同時最大', full.attrs['maxheld'])
print('--- 新しい部品 ---')
t, b = run_tai(srv,'1D','4h','1h',1,('1D','219'),maxpos=5,n8=True,reenter=True,lock=50)
z = t[t.why == '建値']; op = b.o.reindex(z.ext).values
gap = (abs(z.x.values - op) < 1e-9) & (z.x.values < z.e.values)                 # 窓開けで網を飛び越えた時は始値で降りる
g = len(z) > 0 and ((abs(z.pips.values) < 1e-6) | gap).all(); ok.append(g)
print(f"{'○' if g else '×'} しあわせセット(+50pで網を建値):建値で降りた玉 {len(z)}、損益0 が {int((abs(z.pips.values)<1e-6).sum())}・窓開けで始値 {int(gap.sum())}")
t = run_tai(srv,'1D','4h','1h',1,('1D','219'),maxpos=5,n8=True,reenter=True,tp=('1D',3.5))[0]
g = (t.why == '利確').sum() > 0 and (t[t.why == '利確'].pips > 0).all(); ok.append(g)
print(f"{'○' if g else '×'} 利確(日足+3.5σ):利確で降りた玉 {(t.why=='利確').sum()}、全部プラス")
t = run_tai(srv,'1D','4h','1h',1,('1D','219'),maxpos=5,n8=True,reenter=True,sl='prevday')[0]
g = (t.why == '網').sum() > 0; ok.append(g); print(f"{'○' if g else '×'} 網(前の日の安値・上げるだけ):網で降りた玉 {(t.why=='網').sum()}")
t = run_tai(srv,'1D','4h','1h',1,('1D','219'),maxpos=5,n8=True,reenter=True)[0]
g = (t.mae <= 0.0001).all() and (t.mfe >= -0.0001).all() and (t.mfe >= t.pips - 0.01).all(); ok.append(g)
print(f"{'○' if g else '×'} 含み損の最大(mae)≦0・伸びの最大(mfe)≧取れた分")
t = run_tai(srv,'1D','4h','1h',1,('1D','219'),maxpos=5,n8=True,reenter=True,tp=('4h',3.5))[0]
g = (t.why == '利確').sum() > 0 and (t[t.why == '利確'].pips > 0).all(); ok.append(g)
print(f"{'○' if g else '×'} 利確(4h+3.5σ)は入り値より上の時だけ効く:利確 {(t.why=='利確').sum()}玉、負けの利確 {int(((t.why=='利確')&(t.pips<=0)).sum())}(11-06 直したミスの照らし)")
t = run_tai(srv,'1D','4h','1h',1,('1D','219'),maxpos=5,n8=True,reenter=True,lock=50,lockcore=False)[0]
g = ((t.why == '建値') & (t.n == 1)).sum() == 0 and (t.why == '建値').sum() > 0; ok.append(g)
print(f"{'○' if g else '×'} しあわせセットを足した玉だけ(lockcore=False):芯の建値 {int(((t.why=='建値')&(t.n==1)).sum())}・足しの建値 {int((t.why=='建値').sum())}")
print('--- ターボ ---')
space = dict(maxpos=[1, 5], sao=[2.0, 2.5], lock=[0, 50], spr=[0.003, 0.01])
fn = lambda maxpos, sao, lock, spr: stat(run_tai(srv,'1D','4h','1h',1,('1D','219'),maxpos=maxpos,sao=sao,n8=True,reenter=True,lock=lock,spr=spr)[0])
t0 = time.time(); a = grid(fn, space); t1 = time.time(); b = grid_turbo(fn, space); t2 = time.time()
g = a.drop(columns=[]).sort_values(list(space)).reset_index(drop=True)[['sum', 'n']].equals(b.sort_values(list(space)).reset_index(drop=True)[['sum', 'n']]); ok.append(g)
print(f"{'○' if g else '×'} 16通り:1つずつ {t1-t0:.1f}秒 / 並べて(CPU {os.cpu_count()}) {t2-t1:.1f}秒、答えは同じ")
print(f'\n照らし {sum(ok)}/{len(ok)} 合格   全部で {time.time()-T0:.0f}秒')
