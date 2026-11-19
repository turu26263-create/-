# 11-19 引き継ぎのご待ち①を今の決まった形(しあわせ入り)で照らす:買いと鯛は日足が921の並びの時だけ入る。形は変えない(比べるだけ)
import sys, json, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0, '/home/user/eng/engine/nyu')
from nyu import *; from tai_parts import *
cfg = json.load(open('/home/user/eng/engine/nyu/settei_kimari.json')); f = cfg['形']; k = cfg['口座']
srv = Market(load_cached(sys.argv[1]), 'server')
KW = dict(maxpos=f['maxpos'], n8=f['n8'], sao=f['sao'], reenter=True, tp=tuple(f['tp']), ts=f['ts'], avoid_in=tuple(f['avoid_in']), avoid_out=tuple(f['avoid_out']), kai_k9=f.get('kai_k9', 0), big21_up=f.get('big21_up', False), yasumi=f.get('yasumi', False))
sz = {a: v for a, v in f['shiawase'].items() if a not in ('説明', 'dirs', 'shuu_muki')}
def katachi(nb):
    KB = {**KW, 'narabi': nb}; P = []
    t, b = run_tai(srv, f['big'], f['mid'], f['small'], 1, tuple(f['core_exit']), **KB); P.append(t.assign(d=1, kind='買い'))
    u, _ = run_tai(srv, f['big'], f['mid'], f['small'], -1, tuple(f['core_exit']), **KW); P.append(u.assign(d=-1, kind='売り'))
    dz = f['doten']; dt_, _ = run_doten(srv, dz['d'], xtf=dz.get('xtf'), **KW); P.append(dt_.assign(d=dz['d'], kind='ドテン買い'))
    tz = f['tai']; tt_, _ = run_tai(srv, f['big'], f['mid'], f['small'], tz['d'], tuple(tz['exit']), **{**KB, 'maxpos': tz['maxpos'], 'tp': None, 'ts': tz['ts']}); P.append(tt_.assign(d=tz['d'], kind='鯛'))
    for d in (1, -1): oo, _ = run_oshime_d(srv, d, maxpos=f['oshime']['maxpos'], yasumi=f.get('yasumi', False)); P.append(oo.assign(d=d, kind='押し目'))
    t0 = pd.concat(P, ignore_index=True)
    sh = pd.concat([run_shiawase(srv, d, yasumi=f.get('yasumi', False), shuu_muki=d in f['shiawase'].get('shuu_muki', []), **sz)[0].assign(d=d, kind='しあわせ') for d in f['shiawase'].get('dirs', [1, -1])], ignore_index=True)
    return pd.concat([t0, sh[sh.ent >= t0.ent.min()]], ignore_index=True), b
print('決め方(先に決めた):確かめる年の合計が上がり、落ち込み率が上がらなければ残す')
R = {}
for nm, nb in (('今の決まった形', False), ('①買いと鯛は日足921の並びの時だけ', True)):
    tt, b = katachi(nb)
    T, s = lot_sizing(tt, b, 1, k['資金'], margin_cap=k['証拠金の上限'], leverage=k['レバレッジ'], fixed_lot=k['決め打ちのロット'], stopout=k['強制決済の維持率'])
    y = pd.to_datetime(T.ent).dt.year; ta = ~y.between(2022, 2024); R[nm] = T
    g = lambda kk: f"{int((T.kind==kk).sum())}玉 {T.pips[T.kind==kk].sum():+,.0f}p"
    print(f"\n{nm}: {len(T)}玉 {T.pips.sum():+,.0f}p / 確かめる年 {T.pips[ta].sum():+,.0f} / 選22-24 {T.pips[~ta].sum():+,.0f} / 落ち込み率 {s['落ち込み率']}% / 最後の資金 {s.get('最後の資金')}")
    print('   買い', g('買い'), '| 鯛', g('鯛'))
    print('   年ごと', {int(a): int(round(v)) for a, v in T.groupby(y).pips.sum().items()})
a, c = R['今の決まった形'], R['①買いと鯛は日足921の並びの時だけ']
ka = lambda T: set(zip(T.kind, T.ent.astype(str), T.d))
kie = a[[x not in ka(c) for x in zip(a.kind, a.ent.astype(str), a.d)]]
print(f"\n消えた玉 {len(kie)}:", kie.groupby('kind').pips.agg(['count', 'sum']).round(0).to_dict('index'))
print('消えた玉の降りた日数(3日以内)', int(((pd.to_datetime(kie.ext) - pd.to_datetime(kie.ent)).dt.days <= 3).sum()))
