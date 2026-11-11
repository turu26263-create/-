# 11-11 たくちん「うり研鑽して」:しあわせセットの売り(買いの鏡うつし)を、上の大山の途中では売らない
# 【置き換え・照らす前に決めた・1つだけ】週足(月曜0時からの7日足・閉じた週だけ)の9が21の下(219の並び)の間だけ売る。
#   週足が921(上げの大山の途中)の間は売らない。ほかの決まり(レンジ・箱・±2σ・200のまわり・降り)は今のまま
import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0, '/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *
raw = load_cached(sys.argv[1]); mk = Market(raw, 'server'); x = mk.feat('1h')
W = raw.resample('W-MON', label='left', closed='left').agg(dict(o='first', h='max', l='min', c='last')).dropna()
W['k'] = W.index + pd.Timedelta('7D'); W['e9'] = ema(W.c, 9); W['e21'] = ema(W.c, 21); W['w219'] = W.e9 < W.e21
y = pd.merge_asof(pd.DataFrame({'kb': x.index + pd.Timedelta('1h')}), W[['k', 'w219']], left_on='kb', right_on='k', direction='backward')
ok = y.w219.fillna(False).values.astype(bool)
a = run_shiawase(mk, -1)[0]; b = run_shiawase(mk, -1, ok=ok)[0]
for nm, t in (('今の売り', a), ('週足219の間だけの売り', b)):
    t = t[t.ent >= '2016-10-01']; yy = t.ent.dt.year; ta = ~yy.between(2022, 2024)
    print(f"{nm}: {t.camp.nunique()}セット {t.pips.sum():+,.0f}p / 確かめる年 {t.pips[ta].sum():+,.0f} / 選22-24 {t.pips[~ta].sum():+,.0f}")
    print('   年ごと', {int(k): int(round(v)) for k, v in t.groupby(yy).pips.sum().items()})
print('週足219の週', int(W.w219.sum()), '/', len(W))
print('--- 歩き:週足219の間の売り ---')
for c, g in b[b.ent >= '2016-10-01'].groupby('camp'):
    k = g[g.r == '刈る']; m = g[g.r == 'ため'].iloc[0]
    print(f"  売り {g.ent.iloc[0]:%Y/%m/%d %H時} {g.e.iloc[0]:.2f} → 刈る {k.ext.iloc[0]:%m/%d} {k.pips.iloc[0]:+.0f}×3 {'利確' if k.why.iloc[0]=='利確' else '箱割れ'} / ため {m.ext:%Y/%m/%d} {m.pips:+.0f} {'利確' if m.why=='利確' else '箱割れ'} | 計 {g.pips.sum():+.0f}")
