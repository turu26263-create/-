# 11-19 たくちん「ナンピン反撃入れて」【置き換え】(クロードの読み。決まった形はまだ変えない)
# クジラの玉(買い/売り)を持っていて含み損の間に、1時間足の安値が4時間の-2σに届いたら構え(差し込み=ナンピンの場所)、
# その後1時間足で新しい921(売りは219)が出て、まだ一番安い入り値より下(売りは上)なら、次の足でナンピン1玉(反撃)。
# 降りはクジラと同じ:日足219(売りは921)・4時間±4.0σ利確・TS550。ナンピン玉は同時に2つまで。0時は1時へ・GWは入らない。
import sys, json, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0, '/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *
cfg = json.load(open('/home/user/-/engine/nyu/settei_kimari.json')); f = cfg['形']; k = cfg['口座']
KW = dict(maxpos=f['maxpos'], n8=f['n8'], sao=f['sao'], reenter=True, tp=tuple(f['tp']), ts=f['ts'], avoid_in=tuple(f['avoid_in']), avoid_out=tuple(f['avoid_out']), kai_k9=f.get('kai_k9', 0), big21_up=f.get('big21_up', False), yasumi=f.get('yasumi', False))
def run_nanpin(mk, d, maxpos=2, sig=2.0):
    KB = {**KW, 'narabi': f.get('narabi', False) and d > 0}
    main, base = run_tai(mk, '1D', '4h', '1h', d, ('1D', '219'), **KB)
    idx = base.index; n = len(idx); C = base.c.values; L = base.l.values; Hh = base.h.values
    pos = {t: i for i, t in enumerate(idx)}; worst = np.full(n, np.nan)
    for e, a, b in zip(main.e.values, pd.to_datetime(main.ent), pd.to_datetime(main.ext)):
        i0, i1 = pos.get(a), pos.get(b)
        if i0 is None or i1 is None: continue
        seg = worst[i0:i1]; worst[i0:i1] = np.where(np.isnan(seg), e, np.minimum(seg, e) if d > 0 else np.maximum(seg, e))
    band = tp_sigma(mk, '1h', '4h', sig, -d); band = np.r_[np.nan, band[:-1]]          # 4時間の-2σ(売りは+2σ)。1本前の足が閉じた時の線
    S = mk.feat('1h'); up = (S.e9 > S.e21).values; up1 = np.r_[up[0], up[:-1]]; cr = (~up1 & up) if d > 0 else (up1 & ~up)
    E = np.zeros(n, bool); armed = False; nk = 0
    for i in range(n):
        held = not np.isnan(worst[i])
        if not held: armed = False; continue
        loss = C[i] < worst[i] if d > 0 else C[i] > worst[i]
        if loss and ((L[i] <= band[i]) if d > 0 else (Hh[i] >= band[i])): armed = True; nk += 1
        if armed and cr[i] and loss: E[i] = True; armed = False
    E &= ~yasumi_mask(idx)
    fh = np.r_[idx.hour.values[1:], -1]; bad = np.isin(fh, (0,))
    for i in np.where(E & bad)[0]:
        E[i] = False; j = i + 1
        while j < n - 1 and bad[j]: j += 1
        E[j] = True
    XC, KC = exit_219(mk, '1h', '1D', d); XC = np.asarray(XC, bool) & ~bad
    t = simulate(base, d, E, XC, KC, None, None, None, maxpos, 0.003, True, make_tp(mk, '1h', d, tuple(f['tp'])), 0.0, True, f['ts'], 0.0)
    t.attrs['構え'] = nk; return t, base
if __name__ == '__main__':
    srv = Market(load_cached(sys.argv[1]), 'server')
    sz = {a: v for a, v in f['shiawase'].items() if a not in ('説明', 'dirs', 'shuu_muki')}
    P = []
    for d in (1, -1): x, b = run_tai(srv, '1D', '4h', '1h', d, tuple(f['core_exit']), **{**KW, 'narabi': f.get('narabi', False) and d > 0}); P.append(x.assign(d=d, kind='クジラ'))
    x, _ = run_doten(srv, 1, xtf='4h', **KW); P.append(x.assign(d=1, kind='ドテン'))
    tz = f['tai']; x, _ = run_tai(srv, '1D', '4h', '1h', 1, tuple(tz['exit']), **{**KW, 'narabi': f.get('narabi', False), 'maxpos': 1, 'tp': None, 'ts': tz['ts']}); P.append(x.assign(d=1, kind='鯛'))
    for d in (1, -1): x, _ = run_oshime_d(srv, d, maxpos=f['oshime']['maxpos'], yasumi=f.get('yasumi', False)); P.append(x.assign(d=d, kind='押し目'))
    t0 = pd.concat(P, ignore_index=True)
    sh = pd.concat([run_shiawase(srv, d, yasumi=f.get('yasumi', False), shuu_muki=d in f['shiawase'].get('shuu_muki', []), **sz)[0].assign(d=d, kind='しあわせ') for d in f['shiawase'].get('dirs', [1, -1])], ignore_index=True)
    t0 = pd.concat([t0, sh[sh.ent >= t0.ent.min()]], ignore_index=True)
    NP = [run_nanpin(srv, d) for d in (1, -1)]
    np_ = pd.concat([NP[0][0].assign(d=1, kind='ナンピン反撃'), NP[1][0].assign(d=-1, kind='ナンピン反撃')], ignore_index=True)
    print('決め方(先に決めた):確かめる年の合計が上がり、落ち込み率が上がらなければ残す')
    for nm, tt in (('今の決まった形', t0), ('ナンピン反撃を足した形', pd.concat([t0, np_], ignore_index=True))):
        T, s = lot_sizing(tt, b, 1, k['資金'], margin_cap=k['証拠金の上限'], leverage=k['レバレッジ'], fixed_lot=k['決め打ちのロット'], stopout=k['強制決済の維持率'])
        y = pd.to_datetime(T.ent).dt.year; ta = ~y.between(2022, 2024)
        print(f"\n{nm}: {len(T)}玉 {T.pips.sum():+,.0f}p / 確かめる年 {T.pips[ta].sum():+,.0f} / 選22-24 {T.pips[~ta].sum():+,.0f} / 落ち込み率 {s['落ち込み率']}% / 最後の資金 {s['最後の資金']:,} / 入れなかった合図 {s['入れなかった合図']}")
        print('   年ごと', {int(a): int(round(v)) for a, v in T.groupby(y).pips.sum().items()})
    for d, (x, _) in zip((1, -1), NP):
        y = pd.to_datetime(x.ent).dt.year
        print(f"\nナンピン反撃 {'買い' if d > 0 else '売り'}: 構え {x.attrs['構え']}回 / {len(x)}玉 {x.pips.sum():+,.0f}p 勝ち {int((x.pips>0).sum())} / 降り {x.why.value_counts().to_dict()}")
        print('   年ごと', {int(a): int(round(v)) for a, v in x.groupby(y).pips.sum().items()})
        if len(x): print('   一番得', x.loc[x.pips.idxmax(), ['ent', 'e', 'ext', 'pips']].to_dict(), '\n   一番損', x.loc[x.pips.idxmin(), ['ent', 'e', 'ext', 'pips']].to_dict())
