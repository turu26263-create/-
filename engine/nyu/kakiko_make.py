# かきこチャート(クジラの刺身)を作る:決まった形をエンジンで回して、入り降りをチャートのページに入れる(11-06 たくちん「かきこ チャート ぶん回しエンジンで回したのをチャートでここに出して」)
# 使い方: python3 kakiko_make.py <MT4 1時間足の置き場> <書き出し先.html>   公開版 https://claude.ai/artifact/FPRUFZsCfHjKWaXpZfoBAt
import sys, json, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0, __file__.rsplit('/', 1)[0])
from nyu import *; from tai_parts import *
here = __file__.rsplit('/', 1)[0]; cfg = json.load(open(here + '/settei_kimari.json')); f = cfg['形']; k = cfg['口座']
srv = Market(load_cached(sys.argv[1]), 'server')
KW = dict(maxpos=f['maxpos'], n8=f['n8'], sao=f['sao'], reenter=True, tp=tuple(f['tp']), ts=f['ts'], avoid_in=tuple(f['avoid_in']), avoid_out=tuple(f['avoid_out']), kai_k9=f.get('kai_k9', 0), big21_up=f.get('big21_up', False))
t, b = run_tai(srv, f['big'], f['mid'], f['small'], 1, tuple(f['core_exit']), **KW); t['d'] = 1
if f.get('uri'):   # 売りも同じ決まりの鏡うつし(11-06)。0.01ロット決め打ちなので円は pips×10 を玉ごとに足す
    u, _ = run_tai(srv, f['big'], f['mid'], f['small'], -1, tuple(f['core_exit']), **KW); u['d'] = -1; t = pd.concat([t, u], ignore_index=True)
if f.get('doten'):   # 11-07 決まった形3:売りの利確の後921待ちドテン買い
    dz = f['doten']; dt_, _ = run_doten(srv, dz['d'], xtf=dz.get('xtf'), **KW); dt_['d'] = dz['d']; t = pd.concat([t, dt_], ignore_index=True)
T, s = lot_sizing(t, b, 1, k['資金'], margin_cap=k['証拠金の上限'], leverage=k['レバレッジ'], fixed_lot=k['決め打ちのロット'], stopout=k['強制決済の維持率'])
H = srv.bars('1h'); sec = H.index.values.astype('datetime64[s]').astype('int64')       # 時刻は秒(サーバー時刻をそのまま)
bars = [[int(a), int(round(o * 1000)), int(round(h * 1000)), int(round(l * 1000)), int(round(c * 1000))] for a, o, h, l, c in zip(sec, H.o, H.h, H.l, H.c)]
T = T.sort_values('ent').reset_index(drop=True); s2 = lambda x: int(pd.Timestamp(x).to_datetime64().astype('datetime64[s]').astype('int64'))
tr = [dict(i=n + 1, en=s2(r.ent), ep=round(float(r.e), 3), ex=s2(r.ext), xp=round(float(r.x), 3), p=round(float(r.pips), 1), w=r.why, n=int(r.n), c=int(r.camp), y=round(float(r['円'])), mfe=round(float(r.mfe)), mae=round(float(r.mae)), d=int(r.d)) for n, r in T.iterrows()]
y = pd.to_datetime(T.ent).dt.year; yr = {int(a): dict(p=round(float(g.pips.sum()), 1), y=round(float(g['円'].sum())), n=len(g)) for a, g in T.groupby(y)}
data = dict(bars=bars, trades=tr, sum=s, years=yr, total_p=round(float(T.pips.sum()), 1))
open(sys.argv[2], 'w').write(open(here + '/kakiko_template.html').read().replace('__DATA__', json.dumps(data, ensure_ascii=False, separators=(',', ':'))))
print('書いた', sys.argv[2], len(bars), '本', len(tr), '玉')
