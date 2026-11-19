# 11-19 たくちん「エンジンとリアル合わすように」:Kujira3_v3(並び+カウンター反撃7段)と同じ決まりで研究台を回し、
# 1玉ずつ(入り・降り・段のロット・円)を MT4 のテスターの記録と合わせる用に書き出す
import sys, json, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0, '/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *
cfg = json.load(open('/home/user/-/engine/nyu/settei_kimari.json')); f = cfg['形']; k = cfg['口座']
srv = Market(load_cached('/home/user/data/mt4'), 'server')
KW = dict(maxpos=f['maxpos'], n8=f['n8'], sao=f['sao'], reenter=True, tp=tuple(f['tp']), ts=f['ts'], avoid_in=tuple(f['avoid_in']), avoid_out=tuple(f['avoid_out']), kai_k9=f.get('kai_k9', 0), big21_up=f.get('big21_up', False), yasumi=f.get('yasumi', False))
NB = {**KW, 'narabi': f.get('narabi', False)}
P = [run_tai(srv, '1D', '4h', '1h', 1, tuple(f['core_exit']), **NB)[0].assign(d=1, 部品='クジラ買い'),
     run_tai(srv, '1D', '4h', '1h', -1, tuple(f['core_exit']), **KW)[0].assign(d=-1, 部品='クジラ売り'),
     run_doten(srv, 1, xtf='4h', **KW)[0].assign(d=1, 部品='ドテン買い')]
tz = f['tai']; P.append(run_tai(srv, '1D', '4h', '1h', 1, tuple(tz['exit']), **{**NB, 'maxpos': 1, 'tp': None, 'ts': tz['ts'], 'ng_hours': tuple(tz.get('ng_hours', ()))})[0].assign(d=1, 部品='鯛'))
for d in (1, -1): P.append(run_oshime_d(srv, d, maxpos=f['oshime']['maxpos'], yasumi=f.get('yasumi', False))[0].assign(d=d, 部品='押し目買い' if d > 0 else '押し目売り'))
t = pd.concat(P, ignore_index=True)
sz = {a: v for a, v in f['shiawase'].items() if a not in ('説明', 'dirs', 'shuu_muki')}
for d in f['shiawase']['dirs']:
    x, _ = run_shiawase(srv, d, yasumi=True, shuu_muki=d in f['shiawase']['shuu_muki'], **sz)
    x = x.assign(d=d, 部品=('しあわせ買い ' if d > 0 else 'しあわせ売り ') + x.r); t = pd.concat([t, x[x.ent >= t.ent.min()]], ignore_index=True)
t['ent'] = pd.to_datetime(t.ent); t['ext'] = pd.to_datetime(t.ext); t = t.sort_values(['ent', 'ext', '部品']).reset_index(drop=True)
DAN = [0.01, 0.03, 0.06, 0.15, 0.30, 0.60, 1.20]; lv = 0; L = np.zeros(len(t))
for _, kind, i in sorted([(t.ext[i], 1, i) for i in range(len(t))] + [(t.ent[i], 0, i) for i in range(len(t))], key=lambda z: (z[0], z[1])):
    if kind == 0: L[i] = DAN[lv]
    else: lv = 0 if t.pips[i] > 0 else min(lv + 1, 6)
out = pd.DataFrame({'部品': t['部品'], '向き': np.where(t.d > 0, '買い', '売り'), '入り(サーバー時刻)': t.ent.dt.strftime('%Y.%m.%d %H:%M'), '入り値': t.e.round(3),
                    '降り(サーバー時刻)': t.ext.dt.strftime('%Y.%m.%d %H:%M'), '降り値': t.x.round(3), 'pips': t.pips.round(1), '降りた訳': t.why,
                    'ロット(カウンター反撃)': L, '円': (t.pips * L * 1000).round(0)})
out.to_csv('/home/user/-/ea/Kujira3_v3_研究台の玉_MT4あわせ用.csv', index=False, encoding='utf-8-sig')
print(len(out), '玉', round(t.pips.sum(), 1), 'p', f"{out['円'].sum():+,.0f}円", '段ごと', {d: int((L == d).sum()) for d in DAN})
