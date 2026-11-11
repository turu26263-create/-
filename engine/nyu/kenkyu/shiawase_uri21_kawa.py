# 13本目 11-11 たくちん「ご」:降りだけ替える → 日足の終値が9と21の両方の上で閉じたら全部降りる(魚が川の上に出た)。21を少しはみ出しても9の下なら持つ
# 12本目 11-11 たくちん「うりも21の下取れるやろう」:週足219の間の売りを、+2σ ではなく日足21(赤)への戻りで売り、21の下を取る
# 【置き換え・照らす前に決めた】(週足219・レンジ・200のまわり・GW・0時・刈る3+ため1・利確 −2σ/−3.5σ は前と同じ)
#   入り:前の日足の終値が日足21の下 → 値が前の日足の21まで戻ったら、その値で4単位売る(+2σ では売らない)
#   降り:日足の終値が21の上で閉じたら、次の足(0時は1時)で全部降りる(21の下でなくなった)。箱割れは使わない
import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0, '/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *
raw = load_cached(sys.argv[1]); mk = Market(raw, 'server'); x = mk.feat('1h')
W = raw.resample('W-MON', label='left', closed='left').agg(dict(o='first', h='max', l='min', c='last')).dropna()
W['k'] = W.index + pd.Timedelta('7D'); W['w219'] = ema(W.c, 9) < ema(W.c, 21)
ok = pd.merge_asof(pd.DataFrame({'kb': x.index + pd.Timedelta('1h')}), W[['k', 'w219']], left_on='kb', right_on='k', direction='backward').w219.fillna(False).values.astype(bool)
run_shiawase(mk, -1)                                    # レンジの列を作る
spr = 0.003; P = 0.01; d = -1
n = len(x); O, H, L = x.o.values, x.h.values, x.l.values; idx = x.index; hr = idx.hour.values
y = mk.on('1h', '1D', ['c', 'md', 'sd', 'e200', 'e21', 'e9', 'sh_rng']); kd = y['k_1D'].values
md, sd, dc, e2, e21 = y.md.values, y.sd.values, y.c.values, y.e200.values, y.e21.values; rg = y.sh_rng.fillna(False).values.astype(bool); e9 = y.e9.values
newday = np.r_[False, kd[1:] != kd[:-1]]; ym = yasumi_mask(idx)
pos = []; out = []; pair = False; camp = 0
for i in range(1, n - 1):
    tp2 = md[i-1] - 2 * sd[i-1]; tp35 = md[i-1] - 3.5 * sd[i-1]; keep = []
    for p in pos:
        ex = None
        if i > p['j']:
            if p['brk'] and hr[i] != 0: ex = (O[i] + spr, '川の上で閉じた')
            else:
                tv = tp2 if p['r'] == '刈る' else tp35
                if not np.isnan(tv) and tv < p['e'] - spr and L[i] <= tv: ex = (min(O[i], tv) + spr, '利確')
        if ex: out.append(dict(ent=idx[p['j']], e=p['e'], ext=idx[i], x=ex[0], pips=(p['e'] - ex[0]) / P, why=ex[1], r=p['r'], camp=p['c']))
        else: keep.append(p)
    pos = keep
    if newday[i]:
        for p in pos:
            if dc[i] > e21[i] and dc[i] > e9[i]: p['brk'] = True
    if pair and not any(p['r'] == '刈る' for p in pos): pair = False
    lv = e21[i-1]
    if rg[i-1] and ok[i-1] and not ym[i-1] and not pair and hr[i] != 0 and sum(1 for p in pos if p['r'] == 'ため') < 5 and not np.isnan(lv) and dc[i-1] < lv and H[i] >= lv:
        e = max(O[i], lv)
        if abs(e - e2[i-1]) > sd[i-1]:
            camp += 1
            for r in ('刈る', '刈る', '刈る', 'ため'): pos.append(dict(j=i, e=e, r=r, c=camp, brk=False))
            pair = True
t = pd.DataFrame(out); t = t[t.ent >= '2016-10-01']; yy = t.ent.dt.year; ta = ~yy.between(2022, 2024)
print(f"21の下を取る売り(降り=川の上): {t.camp.nunique()}セット {t.pips.sum():+,.0f}p / 確かめる年 {t.pips[ta].sum():+,.0f} / 選22-24 {t.pips[~ta].sum():+,.0f}(+2σの売り 24セット −377p・確かめる年 +4,982)")
print('   年ごと', {int(k): int(round(v)) for k, v in t.groupby(yy).pips.sum().items()})
print(f"   刈る:利確 {int(((t.r=='刈る')&(t.why=='利確')).sum())} 川の上 {int(((t.r=='刈る')&(t.why!='利確')).sum())} 平均 {t.pips[t.r=='刈る'].mean():+.1f}p / ため 平均 {t.pips[t.r=='ため'].mean():+.1f}p")
print('--- 歩き ---')
for c, g in t.groupby('camp'):
    k = g[g.r == '刈る']; m = g[g.r == 'ため'].iloc[0]
    print(f"  売り {g.ent.iloc[0]:%Y/%m/%d %H時} {g.e.iloc[0]:.2f} → 刈る {k.ext.iloc[0]:%m/%d} {k.pips.iloc[0]:+.0f}×3 {k.why.iloc[0]} / ため {m.ext:%Y/%m/%d} {m.pips:+.0f} {m.why} | 計 {g.pips.sum():+.0f}")
