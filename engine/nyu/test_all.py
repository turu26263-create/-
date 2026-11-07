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
chk('4時間版の鯛 売り', stat(run_tai(est,'4h','1h','5min',-1,('1h','9割れ'))[0]), (1820, -408.6))   # 11-06 売りの降りのスプレッドのミスを直した後(前は +683.4)
chk('日足版の鯛 買い縄8', stat(run_tai(est,'1D','4h','1h',1,('4h','9割れ'),n8=True)[0]), (265, 3040.5))
chk('日足クジラ20発', stat(run_tai(est,'1D','4h','1h',1,('1D','9割れ'),maxpos=20,n8=True,reenter=True)[0]), (284, 7942.2))
print('--- ええやつ帳 ---')
DA = ('2025-09-19', '2026-01-27'); FA = ('2021-03-26', '2025-04-15 18:00')
chk('クジラ5発 日足の大山', stat(hitoyama(run_tai(srv,'1D','4h','1h',1,('1D','219'),maxpos=5,n8=True,reenter=True)[0],*DA)), (5, 1936.7))
chk('クジラ5発 450hの大山', stat(hitoyama(run_tai(srv,'450h','1D','1h',1,('450h','219'),maxpos=5,n8=True,reenter=True)[0],*FA)), (5, 16604.3))
chk('上の小魚 日足の大山', stat(hitoyama(kozakana_ue(srv,1,5)[0],*DA)), (30, 217.4))
chk('上の小魚 450hの大山', stat(hitoyama(kozakana_ue(srv,1,5)[0],*FA)), (534, 5400.2))
chk('逆目99 4h 日足の大山', stat(hitoyama(gyakume_99(srv,'4h',-1)[0],*DA)), (28, 685.3))   # 11-06 売りの降りのミスを直した後(前は +702.1)
chk('鯛 日足段 買い spr1.0', stat(run_tai(est,'1D','4h','1h',1,('4h','9割れ'),n8=True,spr=0.01)[0]), (265, 2855.0))
chk('クジラmix 日足段 spr1.0', stat(run_tai(est,'1D','4h','1h',1,('1D','9割れ'),('4h','9割れ'),5,n8=True,spr=0.01,reenter=True)[0]), (284, 6051.9))
chk('鯛 4h段 売り spr1.0', stat(run_tai(est,'4h','1h','5min',-1,('1h','9割れ'),spr=0.01)[0]), (1820, -1682.6))   # 11-06 直した後(前は +1957.4)
chk('決まった形(クジラ5発・縄8なし・4h3.5σ利確・TS550・日足219・入り降り1時)', stat(run_tai(srv,'1D','4h','1h',1,('1D','219'),maxpos=5,n8=False,reenter=True,tp=('4h',3.5),ts=550,avoid_in=(0,),avoid_out=(0,))[0]), (299, 12928.4))
KN = dict(maxpos=5, n8=False, reenter=True, tp=('4h', 3.5), ts=550, avoid_in=(0,), avoid_out=(0,), kai_k9=3, big21_up=True)
chk('決まった形2(11-06「ご」)の買い:許し3本目・日足21上向き', stat(run_tai(srv,'1D','4h','1h',1,('1D','219'),**KN)[0]), (206, 13717.2))
chk('決まった形2の売り(鏡うつし)', stat(run_tai(srv,'1D','4h','1h',-1,('1D','219'),**KN)[0]), (153, 2241.4))
chk('前の決まった形(0時のまま)', stat(run_tai(srv,'1D','4h','1h',1,('1D','219'),maxpos=5,n8=False,reenter=True,tp=('4h',3.5),ts=550)[0]), (299, 12814.9))
chk('前の決まった形(縄8あり)', stat(run_tai(srv,'1D','4h','1h',1,('1D','219'),maxpos=5,n8=True,reenter=True,tp=('4h',3.5),ts=550)[0]), (291, 12448.3))
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
t, b = run_tai(srv,'1D','4h','1h',1,('1D','219'),maxpos=5,n8=True,reenter=True,tp=('4h',3.5),ts=550)
g = abs(cost_adjust(t,1).pips.sum() - t.pips.sum()) < 1e-6 and cost_adjust(t,1,spr_hour={0:10.0}).pips.sum() < t.pips.sum() and cost_adjust(t,1,swap_long=0.1).pips.sum() > t.pips.sum(); ok.append(g)
print(f"{'○' if g else '×'} 0時のスプレッド・スワップ:付けなければ同じ、0時+10pで減る、買いスワップ+で増える")
m1_, m2_ = montecarlo(t, 300, seed=7), montecarlo(t, 300, seed=7)
g = m1_ == m2_ and m1_['DD95'] >= m1_['DD中央'] >= 0; ok.append(g); print(f"{'○' if g else '×'} 並べ替えの試し:同じ種なら同じ答え・DD95≧中央")
T_, s_ = lot_sizing(t, b, 1, 102_000, fixed_lot=0.01)
g = abs(T_['円'].sum() - t.pips.sum() * 10) < 1e-3 and s_['入った玉'] == len(t); ok.append(g)
print(f"{'○' if g else '×'} エントリー調節:決め打ち0.01ロットなら 円 = pips×10、全部の玉に入る")
print('--- 暴走チェック2(11-06 たくちん「なんで暴走や?」)---')
raw_m = raw_s.copy(); K = 300.0
raw_m[['o', 'c']] = K - raw_s[['o', 'c']].values; raw_m['h'] = K - raw_s['l'].values; raw_m['l'] = K - raw_s['h'].values
mir = Market(raw_m, 'server')
KWm = dict(maxpos=5, n8=False, reenter=True, tp=('4h', 3.5), ts=550, avoid_in=(0,), avoid_out=(0,), kai_k9=3, big21_up=True)
ts_ = run_tai(Market(raw_s, 'server'), '1D', '4h', '1h', -1, ('1D', '219'), **KWm)[0]
tb_ = run_tai(mir, '1D', '4h', '1h', 1, ('1D', '219'), **KWm)[0]
g = len(ts_) == len(tb_) and (ts_.ent.values == tb_.ent.values).all() and (ts_.ext.values == tb_.ext.values).all() and np.allclose(ts_.pips.values, tb_.pips.values, atol=1e-6); ok.append(g)
print(f"{'○' if g else '×'} 鏡の照らし:値段を上下ひっくり返して買い={len(tb_)}玉 {tb_.pips.sum():+.1f}p / 元の売り={len(ts_)}玉 {ts_.pips.sum():+.1f}p(1玉ずつ同じか)")
m3 = Market(raw_s, 'server'); run_tai(m3, '1D', '4h', '1h', 1, ('1D', '219'), **KWm); after = run_tai(m3, '1D', '4h', '1h', -1, ('1D', '219'), **KWm)[0]
g = len(after) == len(ts_) and np.allclose(after.pips.values, ts_.pips.values); ok.append(g)
print(f"{'○' if g else '×'} 順番の照らし:買いを先に回しても売りは同じ {len(after)}玉 {after.pips.sum():+.1f}p")
print('--- 鏡の照らし(いろいろな形)---')
raw_s5 = raw_s.loc['2016-03-01':'2019-12-31']; raw_e5 = raw_e.loc['2016-01-01':'2017-12-31']
KB = dict(maxpos=5, n8=False, reenter=True, avoid_in=(0,), avoid_out=(0,))
cases = [('網=前の日', lambda m, d: run_tai(m,'1D','4h','1h',d,('1D','219'),sl='prevday',**KB)[0], raw_s5, 'server'),
         ('網=4hの21の20p下', lambda m, d: run_tai(m,'1D','4h','1h',d,('1D','219'),sl=('4h','e21',0.2),**KB)[0], raw_s5, 'server'),
         ('しあわせセット50p', lambda m, d: run_tai(m,'1D','4h','1h',d,('1D','219'),lock=50,**KB)[0], raw_s5, 'server'),
         ('足しだけしあわせセット', lambda m, d: run_tai(m,'1D','4h','1h',d,('1D','219'),lock=50,lockcore=False,**KB)[0], raw_s5, 'server'),
         ('TS200・100p伸びてから', lambda m, d: run_tai(m,'1D','4h','1h',d,('1D','219'),ts=200,ts_start=100,tp=('4h',3.5),**KB)[0], raw_s5, 'server'),
         ('芯は日足・足しは4h9割れ', lambda m, d: run_tai(m,'1D','4h','1h',d,('1D','9割れ'),('4h','9割れ'),maxpos=5,n8=True,reenter=True)[0], raw_s5, 'server'),
         ('終値9で降り', lambda m, d: run_tai(m,'1D','4h','1h',d,('1D','終値9'),maxpos=5,reenter=True)[0], raw_s5, 'server'),
         ('上の小魚', lambda m, d: kozakana_ue(m,d,5)[0], raw_s5, 'server'),
         ('逆目99 4h', lambda m, d: gyakume_99(m,'4h',-d)[0] if False else gyakume_99(m,'4h',d)[0], raw_s5, 'server'),
         ('5分足の鯛(縄8・1分足で先を決める)', lambda m, d: run_tai(m,'4h','1h','5min',d,('1h','9割れ'),n8=True,tp=('1h',3.5),ts=100,fine=True)[0], raw_e5, 'est')]
for nm, fn, rw, ck in cases:
    g, msg = kagami(fn, rw, ck); ok.append(g); print(f"{'○' if g else '×'} 鏡:{nm}:{msg}")
print('--- 利確の後921待ちドテン(11-07)---')
KD = dict(maxpos=5, n8=False, reenter=True, tp=('4h', 3.5), ts=550, avoid_in=(0,), avoid_out=(0,), kai_k9=3, big21_up=True)
g, msg = kagami(lambda m, d: run_doten(m, d, **KD)[0], raw_s5, 'server'); ok.append(g); print(f"{'○' if g else '×'} 鏡:ドテン:{msg}")
chk('売りの利確の後921待ちドテン買い', stat(run_doten(srv, 1, **KD)[0]), (41, -67.0))
from bugbug import bugbug
KB = dict(maxpos=5, n8=False, reenter=True, tp=('4h', 3.5), ts=550, avoid_in=(0,), avoid_out=(0,))
g, _ = bugbug(lambda mk, d: run_tai(mk, '1D', '4h', '1h', d, ('1D', '219'), **KB)[0], raw_s5, 'server', 5, 0.003); ok.append(g)
print(f"{'○' if g else '×'} バグバグ修正機:決まった形(売り買い)が全部○")
print('--- ターボ ---')
space = dict(maxpos=[1, 5], sao=[2.0, 2.5], lock=[0, 50], spr=[0.003, 0.01])
fn = lambda maxpos, sao, lock, spr: stat(run_tai(srv,'1D','4h','1h',1,('1D','219'),maxpos=maxpos,sao=sao,n8=True,reenter=True,lock=lock,spr=spr)[0])
t0 = time.time(); a = grid(fn, space); t1 = time.time(); b = grid_turbo(fn, space); t2 = time.time()
g = a.drop(columns=[]).sort_values(list(space)).reset_index(drop=True)[['sum', 'n']].equals(b.sort_values(list(space)).reset_index(drop=True)[['sum', 'n']]); ok.append(g)
print(f"{'○' if g else '×'} 16通り:1つずつ {t1-t0:.1f}秒 / 並べて(CPU {os.cpu_count()}) {t2-t1:.1f}秒、答えは同じ")
print(f'\n照らし {sum(ok)}/{len(ok)} 合格   全部で {time.time()-T0:.0f}秒')
