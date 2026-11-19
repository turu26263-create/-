# 11-11 たくちん「1」:決まった形(しあわせセットなし)と、しあわせセット入りを、口座の決まり(10.2万円・0.01ロット決め打ち・証拠金33%・維持率20%)で並べる
import sys, json, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0, '/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *
cfg = json.load(open('/home/user/-/engine/nyu/settei_kimari.json')); f = cfg['形']; k = cfg['口座']
srv = Market(load_cached(sys.argv[1]), 'server')
KW = dict(maxpos=f['maxpos'], n8=f['n8'], sao=f['sao'], reenter=True, tp=tuple(f['tp']), ts=f['ts'], avoid_in=tuple(f['avoid_in']), avoid_out=tuple(f['avoid_out']), kai_k9=f.get('kai_k9', 0), big21_up=f.get('big21_up', False), yasumi=f.get('yasumi', False))
t, b = run_tai(srv, f['big'], f['mid'], f['small'], 1, tuple(f['core_exit']), **KW); t['d'] = 1
u, _ = run_tai(srv, f['big'], f['mid'], f['small'], -1, tuple(f['core_exit']), **KW); u['d'] = -1; t = pd.concat([t, u], ignore_index=True)
dz = f['doten']; dt_, _ = run_doten(srv, dz['d'], xtf=dz.get('xtf'), **KW); dt_['d'] = dz['d']; t = pd.concat([t, dt_], ignore_index=True)
tz = f['tai']; KT = {**KW, 'maxpos': tz['maxpos'], 'tp': None, 'ts': tz['ts']}; tt_, _ = run_tai(srv, f['big'], f['mid'], f['small'], tz['d'], tuple(tz['exit']), **KT); tt_['d'] = tz['d']; t = pd.concat([t, tt_], ignore_index=True)
for d in (1, -1): oo, _ = run_oshime_d(srv, d, maxpos=f['oshime']['maxpos'], yasumi=f.get('yasumi', False)); oo['d'] = d; t = pd.concat([t, oo], ignore_index=True)
sz = {a: v for a, v in f['shiawase'].items() if a not in ('説明', 'dirs', 'shuu_muki')}
sh = pd.concat([run_shiawase(srv, d, yasumi=f.get('yasumi', False), shuu_muki=d in f['shiawase'].get('shuu_muki', []), **sz)[0].assign(d=d) for d in f['shiawase'].get('dirs', [1, -1])], ignore_index=True)
sh = sh[sh.ent >= t.ent.min()]
for nm, tt in (('今の決まった形', t), ('しあわせセット入り', pd.concat([t, sh], ignore_index=True))):
    T, s = lot_sizing(tt, b, 1, k['資金'], margin_cap=k['証拠金の上限'], leverage=k['レバレッジ'], fixed_lot=k['決め打ちのロット'], stopout=k['強制決済の維持率'])
    y = pd.to_datetime(T.ent).dt.year; ta = ~y.between(2022, 2024)
    print(nm, len(T), '玉', f"{T.pips.sum():+,.0f}p / 確かめる年 {T.pips[ta].sum():+,.0f} / 選22-24 {T.pips[~ta].sum():+,.0f}", s)
    print('   年ごと', {int(a): int(round(v)) for a, v in T.groupby(y).pips.sum().items()})
# 落ち込みの場所(降りた時の残高で見る)
z = T.sort_values('ext'); eq = 102000 + z['円'].cumsum(); pk = eq.cummax(); r = (pk - eq) / pk; j = r.idxmax()
print('   一番の落ち込み率の所', z.ext[j], f"{r[j]*100:.1f}%", '山の時', z.ext[(eq[:j+1]).idxmax()] if False else z.ext[eq.loc[:j].idxmax()])
