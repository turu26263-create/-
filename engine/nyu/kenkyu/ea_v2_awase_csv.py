# 11-12 たくちん「mt4で回して」:今の決まった形を研究台で回し、1玉ずつの表を MT4 のテスターと合わせる用に書き出す
import sys, json, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0, '/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *
cfg = json.load(open('/home/user/-/engine/nyu/settei_kimari.json')); f = cfg['形']; k = cfg['口座']
srv = Market(load_cached(sys.argv[1]), 'server')
KW = dict(maxpos=f['maxpos'], n8=f['n8'], sao=f['sao'], reenter=True, tp=tuple(f['tp']), ts=f['ts'], avoid_in=tuple(f['avoid_in']), avoid_out=tuple(f['avoid_out']), kai_k9=f.get('kai_k9', 0), big21_up=f.get('big21_up', False), yasumi=f.get('yasumi', False))
P = []
for d in (1, -1): x, b = run_tai(srv, f['big'], f['mid'], f['small'], d, tuple(f['core_exit']), **KW); P.append(x.assign(d=d, 部品='クジラ買い' if d > 0 else 'クジラ売り'))
x, _ = run_doten(srv, 1, xtf='4h', **KW); P.append(x.assign(d=1, 部品='ドテン買い'))
tz = f['tai']; x, _ = run_tai(srv, f['big'], f['mid'], f['small'], 1, tuple(tz['exit']), **{**KW, 'maxpos': 1, 'tp': None, 'ts': tz['ts']}); P.append(x.assign(d=1, 部品='鯛'))
for d in (1, -1): x, _ = run_oshime_d(srv, d, maxpos=5, yasumi=True); P.append(x.assign(d=d, 部品='押し目買い' if d > 0 else '押し目売り'))
sz = {a: v for a, v in f['shiawase'].items() if a not in ('説明', 'dirs', 'shuu_muki')}
for d in f['shiawase']['dirs']:
    x, _ = run_shiawase(srv, d, yasumi=True, shuu_muki=d in f['shiawase']['shuu_muki'], **sz); P.append(x.assign(d=d, 部品=('しあわせ買い ' if d > 0 else 'しあわせ売り ') + x.r))
t = pd.concat(P, ignore_index=True); T, s = lot_sizing(t, b, 1, k['資金'], margin_cap=k['証拠金の上限'], leverage=k['レバレッジ'], fixed_lot=k['決め打ちのロット'], stopout=k['強制決済の維持率'])
T = T.sort_values(['ent', '部品']).reset_index(drop=True)
out = pd.DataFrame({'部品': T['部品'], '向き': np.where(T.d > 0, '買い', '売り'), '入り(サーバー時刻)': pd.to_datetime(T.ent).dt.strftime('%Y.%m.%d %H:%M'), '入り値': T.e.round(3),
                    '降り(サーバー時刻)': pd.to_datetime(T.ext).dt.strftime('%Y.%m.%d %H:%M'), '降り値': T.x.round(3), 'pips': T.pips.round(1), '降りた訳': T.why, '円(0.01ロット)': T['円'].round(0)})
out.to_csv(sys.argv[2], index=False, encoding='utf-8-sig')
print(len(out), '玉', round(T.pips.sum(), 1), 'p', s['最後の資金'], '円', s['落ち込み率'], '%')
print(out.groupby('部品').pips.agg(['count', 'sum']).round(1).to_string())
