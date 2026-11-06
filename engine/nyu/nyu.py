# ニューぶん回しエンジン(11-06 たくちん「eaあと ニューぶん回しエンジンつくるんがさき」)
#
# 作りの決まり
#  1. 先読みしない作り:上の足の値は「その足が閉じた時刻」に、下の足へ貼る(merge_asof backward)。足の途中の値は使わない
#  2. 線(EMA・帯・角度・9割れ・219)は足ごとに1回だけ計算して使い回す(Market のしまい場所)
#  3. 合図・降り・網は「並べた真偽」で作り、1玉ずつの売買だけ numba で回す(速い)
#  4. 選ぶ年と確かめる年を分ける/スプレッド2通り/含み損込みDD/降りの理由のカウンター/大山ひと山だけの見方
#  5. 暴走チェック:データを途中で切って前の戦が変わらないか(先読み)・同時に持つ玉が上限を超えないか・降りていない玉
#  6. 決まりの数字は【置き換え】。たくちんの言葉は変えない(遅行は21本前)
import os, glob, itertools, time
import numpy as np, pandas as pd
from numba import njit

AGG = dict(o='first', h='max', l='min', c='last')
PIP = 0.01

# ---------------------------------------------------------------- データ
def load_csv_dir(d):
    """MT4 書き出し形式(日付,時刻,O,H,L,C,V)の csv を全部読む。HistData も同じ形"""
    fs = sorted(glob.glob(os.path.join(d, '*.csv')))
    m = pd.concat([pd.read_csv(f, header=None, names='d t o h l c v'.split()) for f in fs])
    m.index = pd.to_datetime(m.d + ' ' + m.t, format='%Y.%m.%d %H:%M')
    m = m[['o', 'h', 'l', 'c']].sort_index()
    return m[~m.index.duplicated()]

def load_cached(d, cache_dir=None):
    """ターボ:csv を読んだ物を pickle にしまい、2回目からはそれを読む(csv が変わったら作り直す)"""
    import hashlib, pickle
    fs = sorted(glob.glob(os.path.join(d, '*.csv')))
    key = hashlib.md5(('|'.join(f'{f}:{os.path.getsize(f)}:{os.path.getmtime(f)}' for f in fs)).encode()).hexdigest()[:12]
    cache_dir = cache_dir or os.path.join(d, '.nyu_cache'); os.makedirs(cache_dir, exist_ok=True)
    p = os.path.join(cache_dir, f'raw_{key}.pkl')
    if os.path.exists(p): return pd.read_pickle(p)
    raw = load_csv_dir(d); raw.to_pickle(p, protocol=5); return raw

def ema(s, p): return s.ewm(span=p, adjust=False).mean()

class Market:
    """足と線のしまい場所。clock='est'(HistData:日足はNY17時区切り)/'server'(MT4:日足はサーバー0時区切り)"""
    def __init__(self, raw, clock='est'):
        self.raw = raw; self.clock = clock; self._b = {}; self._f = {}
    def bars(self, tf):
        if tf in self._b: return self._b[tf]
        if tf == '1D':
            b = self.raw.resample('24h', offset='17h').agg(AGG).dropna() if self.clock == 'est' else self.raw.resample('1D').agg(AGG).dropna()
            ln = pd.Timedelta('24h')
        elif tf.endswith('h') and int(tf[:-1]) > 24:          # 450h など。暦の時間で区切る(MT4 の期間変換と同じ)【置き換え】
            b = self.raw.resample(tf, origin='epoch').agg(AGG).dropna(); ln = pd.Timedelta(tf)
        else:
            b = self.raw.resample(tf).agg(AGG).dropna(); ln = pd.Timedelta(tf)
        b['k'] = b.index + ln                                  # 足が閉じた時刻(この時刻から使える)
        self._b[tf] = b; return b
    def feat(self, tf):
        """足ごとの線を1回だけ作る"""
        if tf in self._f: return self._f[tf]
        b = self.bars(tf).copy(); c = b.c
        b['e9'] = ema(c, 9); b['e21'] = ema(c, 21); b['e200'] = ema(c, 200)
        b['md'] = c.rolling(20).mean(); b['sd'] = c.rolling(20).std(ddof=0)
        b['h21'] = b.h.shift(21); b['l21'] = b.l.shift(21)        # 遅行スパン 21本前(たくちんの記憶)
        rng = b.h.rolling(150).max() - b.l.rolling(150).min()     # 21の角度:横1本6ドット・縦=直近150本の高安を500ドット・21の3本【置き換え】
        b['ang'] = np.degrees(np.arctan2((b.e21 - b.e21.shift(3)) / rng * 500, 18))
        mid = (b.o + b.c) / 2
        b['ware_b'] = (mid < b.e9) & (c < b.e9)                    # 9割れ(実体が渡り切った):買いを降りる
        b['ware_s'] = (mid > b.e9) & (c > b.e9)
        b['up921'] = b.e9 > b.e21                                  # 921 の並び
        self._f[tf] = b; return b
    def hl_order(self, tf):
        """足の中で高値と安値のどちらが先についたか(+1=高値が先/−1=安値が先/0=わからない)。元のデータ(1分足など)が細かい時だけわかる"""
        key = ('hlo', tf)
        if key in self._f: return self._f[key]
        b = self.bars(tf); r = self.raw
        if len(r) >= 2 and (r.index[1] - r.index[0]) >= (b.index[1] - b.index[0]):
            out = np.zeros(len(b), np.int64)
        else:
            bid = np.searchsorted(b.index.values, r.index.values, side='right') - 1           # 細かい足がどの足に入るか(空の足は無視)
            okr = (bid >= 0) & (r.index.values < b.k.values[np.clip(bid, 0, None)])
            z = pd.DataFrame({'b': bid[okr], 'h': r.h.values[okr], 'l': r.l.values[okr], 't': np.arange(okr.sum())})
            th = z.loc[z.groupby('b').h.idxmax(), ['b', 't']].set_index('b').t; tl = z.loc[z.groupby('b').l.idxmin(), ['b', 't']].set_index('b').t
            v = np.sign(tl - th).astype(np.int64)                                             # 高値が先(th<tl)=+1
            out = np.zeros(len(b), np.int64); out[v.index.values] = v.values
        self._f[key] = out; return out
    def on(self, base_tf, tf, cols):
        """tf の線を base_tf の足に貼る。base の足が閉じた時に確定している tf の足の値だけ使う"""
        key = ('on', base_tf, tf, tuple(cols))
        if key in self._f: return self._f[key]
        B = self.feat(base_tf); F = self.feat(tf)
        a = F[['k'] + list(cols)].rename(columns={c: f'{c}' for c in cols}).sort_values('k')
        y = pd.merge_asof(pd.DataFrame({'kb': B.k.values}), a, left_on='kb', right_on='k', direction='backward')
        y.index = B.index; y = y.drop(columns=['kb']).rename(columns={'k': 'k_' + tf})
        self._f[key] = y; return y

# ---------------------------------------------------------------- 1玉ずつの売買(numba)
@njit(cache=True)
def _sim(O, H, L, T, E, XC, KC, XA, KA, SLV, TPV, d, maxpos, spr, slmode, reenter, lock, lockcore, ts, ts_start, HLO):
    # E 入り / XC・KC 芯の降り(と、その合図の足が閉じた時刻)/ XA・KA 足し玉の降り / SLV 網の高さ(nan=網なし)/ TPV 利確の高さ(nan=なし)
    # slmode 0=網なし 1=網を上げるだけ(売りは下げるだけ)/ lock>0:玉が lock pips 伸びたら次の足から網を建値へ(しあわせセット)
    # 足の中の順番:網 → 利確 → 合図の降り(損な方を先に見る)
    n = len(O); mp = maxpos
    pj = np.zeros(mp, np.int64); pe = np.zeros(mp); psl = np.zeros(mp); pn = np.zeros(mp, np.int64); pc = np.zeros(mp, np.int64); act = np.zeros(mp, np.bool_)
    plk = np.zeros(mp, np.bool_); pmin = np.zeros(mp); pmax = np.zeros(mp); pts = np.zeros(mp, np.bool_)
    out_j = np.zeros(n, np.int64); out_i = np.zeros(n, np.int64); out_e = np.zeros(n); out_x = np.zeros(n); out_n = np.zeros(n, np.int64); out_c = np.zeros(n, np.int64); out_w = np.zeros(n, np.int64)
    out_lo = np.zeros(n); out_hi = np.zeros(n)
    m = 0; camp = 0; cnt = 0; maxheld = 0; amb = 0; amb_tp = 0
    for i in range(1, n - 1):
        exited = False
        for s in range(mp):
            if not act[s]: continue
            j = pj[s]
            if i >= j:
                if L[i] < pmin[s]: pmin[s] = L[i]
                if H[i] > pmax[s]: pmax[s] = H[i]
            if slmode == 1 and not np.isnan(SLV[i]):
                if np.isnan(psl[s]): psl[s] = SLV[i]
                elif d > 0: psl[s] = max(psl[s], SLV[i])
                else: psl[s] = min(psl[s], SLV[i])
            ex = np.nan; why = 0
            slhit = False; tphit = False
            if i > j and not np.isnan(psl[s]):
                slhit = (d > 0 and L[i] <= psl[s]) or (d < 0 and H[i] >= psl[s])
            if i > j and not np.isnan(TPV[i]):
                tphit = (d > 0 and TPV[i] > pe[s] and H[i] >= TPV[i]) or (d < 0 and TPV[i] < pe[s] and L[i] <= TPV[i])   # 利確は入り値より上にある時だけ
            tp_first = False
            if slhit and tphit:                                          # 同じ足で網と利確の両方に届いた:HLO で先を決める(0=わからない→損な方=網)
                amb += 1
                if (d > 0 and HLO[i] > 0) or (d < 0 and HLO[i] < 0):
                    if not (d > 0 and O[i] <= psl[s]) and not (d < 0 and O[i] >= psl[s]): tp_first = True; amb_tp += 1
            if slhit and not tp_first:
                if d > 0: ex = min(O[i], psl[s])
                else: ex = max(O[i], psl[s]) + spr
                why = 3
                if plk[s] and abs(psl[s] - pe[s]) < 1e-9: why = 5
                elif pts[s]: why = 6
            elif tphit:
                if d > 0: ex = max(O[i], TPV[i])
                else: ex = min(O[i], TPV[i]) + spr
                why = 4
            if np.isnan(ex):
                if pn[s] == 1:
                    if XC[i] and KC[i] > T[j]: ex = O[i + 1] - (0.0 if d > 0 else spr); why = 1
                else:
                    if XA[i] and KA[i] > T[j]: ex = O[i + 1] - (0.0 if d > 0 else spr); why = 2
            if not np.isnan(ex):
                out_j[m] = j; out_i[m] = i + (0 if why >= 3 else 1); out_e[m] = pe[s]; out_x[m] = ex; out_n[m] = pn[s]; out_c[m] = pc[s]; out_w[m] = why
                out_lo[m] = pmin[s]; out_hi[m] = pmax[s]; m += 1
                act[s] = False; cnt -= 1; exited = True
            else:
                if ts > 0 and i >= j:                                    # TS:この足までの一番上から ts pips 下へ(次の足から効く)。ts_start pips 伸びてから
                    fav = (pmax[s] - pe[s]) / 0.01 if d > 0 else (pe[s] - pmin[s]) / 0.01
                    if fav >= ts_start:
                        nsl = pmax[s] - ts * 0.01 if d > 0 else pmin[s] + ts * 0.01
                        if np.isnan(psl[s]) or (d > 0 and nsl > psl[s]) or (d < 0 and nsl < psl[s]):
                            psl[s] = nsl; pts[s] = True
            if np.isnan(ex) and lock > 0 and not plk[s] and i >= j and (lockcore or pn[s] > 1):
                fav = (pmax[s] - pe[s]) / 0.01 if d > 0 else (pe[s] - pmin[s]) / 0.01
                if fav >= lock:
                    plk[s] = True
                    if np.isnan(psl[s]) or (d > 0 and pe[s] > psl[s]) or (d < 0 and pe[s] < psl[s]): psl[s] = pe[s]; pts[s] = False
        if E[i] and cnt < mp and (reenter or not exited):
            e = O[i + 1] + (spr if d > 0 else 0.0); sl = SLV[i] if slmode >= 1 else np.nan
            if slmode >= 1 and not np.isnan(sl) and ((d > 0 and sl >= e) or (d < 0 and sl <= e)): continue
            if cnt == 0: camp += 1
            for s in range(mp):
                if not act[s]:
                    act[s] = True; pj[s] = i + 1; pe[s] = e; psl[s] = sl; pn[s] = cnt + 1; pc[s] = camp; plk[s] = False; pts[s] = False
                    pmin[s] = 1e18; pmax[s] = -1e18; cnt += 1; break
            if cnt > maxheld: maxheld = cnt
    held = cnt
    return out_j[:m], out_i[:m], out_e[:m], out_x[:m], out_n[:m], out_c[:m], out_w[:m], out_lo[:m], out_hi[:m], maxheld, held, amb, amb_tp

WHY = {1: '芯の降り', 2: '足しの降り', 3: '網', 4: '利確', 5: '建値', 6: 'TS'}

def simulate(base, d, E, XC, KC, XA=None, KA=None, SLV=None, maxpos=1, spr=0.003, reenter=True, TPV=None, lock=0.0, lockcore=True, ts=0.0, ts_start=0.0, HLO=None):
    """base=入る足の表(o,h,l,c と時刻)。真偽の並びを渡すと、1玉ずつの戦の表を返す。
    SLV=網の高さ(上げるだけ)/TPV=利確の高さ/lock=しあわせセット(伸びたら網を建値へ)。玉ごとに 逆に行った最大(mae)・伸びた最大(mfe)も返す"""
    O = base.o.values.astype(np.float64); H = base.h.values.astype(np.float64); L = base.l.values.astype(np.float64)
    T = base.index.values.astype('datetime64[ns]').astype(np.int64)
    f = lambda a: np.asarray(a, dtype=np.bool_)
    k = lambda a: np.asarray(pd.to_datetime(a).values.astype('datetime64[ns]').astype(np.int64)) if a is not None else None
    XA = XC if XA is None else XA; KA = KC if KA is None else KA
    nan = np.full(len(O), np.nan)
    sl = nan if SLV is None else np.asarray(SLV, dtype=np.float64)
    tp = nan if TPV is None else np.asarray(TPV, dtype=np.float64)
    r = _sim(O, H, L, T, f(E), f(XC), k(KC), f(XA), k(KA), sl, tp, d, maxpos, spr, 0 if SLV is None else 1, reenter, float(lock), bool(lockcore), float(ts), float(ts_start), np.zeros(len(O), np.int64) if HLO is None else np.asarray(HLO, dtype=np.int64))
    j, i, e, x, n, c, w, lo, hi, mx, held, amb, amb_tp = r
    t = pd.DataFrame({'ent': base.index.values[j], 'e': e, 'ext': base.index.values[np.minimum(i, len(O) - 1)], 'x': x,
                      'pips': (x - e) / PIP * d, 'n': n, 'camp': c, 'why': [WHY[v] for v in w]})
    t['mae'] = np.where(d > 0, lo - e, e - hi) / PIP; t['mfe'] = np.where(d > 0, hi - e, e - lo) / PIP
    t.attrs['maxheld'] = int(mx); t.attrs['held_at_end'] = int(held); t.attrs['同じ足で網と利確'] = int(amb); t.attrs['そのうち利確が先'] = int(amb_tp)
    return t

# ---------------------------------------------------------------- 成績
def stat(t):
    if len(t) == 0: return dict(n=0, sum=0.0, pf=np.nan, win=0)
    w = t.pips[t.pips > 0].sum(); l = -t.pips[t.pips < 0].sum()
    return dict(n=len(t), sum=round(float(t.pips.sum()), 1), pf=round(w / l, 2) if l else np.nan, win=int((t.pips > 0).sum()))

def float_dd(t, base, d):
    """含み損も入れた最大ドローダウン(入る足の終値で毎本の評価)"""
    if len(t) == 0: return 0.0
    C = base.c.values; idx = base.index.values; n = len(idx); fl = np.zeros(n); rl = np.zeros(n + 1)
    A = np.searchsorted(idx, t.ent.values); B = np.searchsorted(idx, t.ext.values)
    for a, b, e in zip(A, B, t.e.values): fl[a:b] += (C[a:b] - e) / PIP * d
    np.add.at(rl, B, t.pips.values); eq = fl + np.cumsum(rl)[:n]
    return round(float((np.maximum.accumulate(eq) - eq).max()), 1) if len(t) else 0.0

SPLIT = {'選22-24': (2022, 2024), '確15-21': (2015, 2021), '確25': (2025, 2025)}

def report(t, base=None, d=1, split=SPLIT):
    y = pd.to_datetime(t.ent).dt.year; r = {}
    for k, (a, b) in split.items():
        s = stat(t[y.between(a, b)]); r[k + '_p'] = s['sum']; r[k + '_pf'] = s['pf']; r[k + '_n'] = s['n']
    s = stat(t); r.update(全_p=s['sum'], 全_pf=s['pf'], 玉=s['n'], 勝=s['win'])
    if base is not None: r['含み損込みDD'] = float_dd(t, base, d)
    r['同時最大'] = t.attrs.get('maxheld', 0)
    for wv in ('芯の降り', '足しの降り', '網', '利確', '建値', 'TS'): r['降り_' + wv] = int((t.why == wv).sum())
    if len(t) and 'mfe' in t:
        w = t.pips > 0
        r['取れた割合%'] = round(float(t.pips[w].sum() / max(t.mfe[w].sum(), 1e-9) * 100), 0) if w.any() else 0
        r['伸びてから負けた玉'] = int(((t.mfe > 50) & ~w).sum())
    return r

def hitoyama(t, a, b):
    """大山ひと山だけ:その山の間に入った玉だけ"""
    return t[(t.ent >= pd.Timestamp(a)) & (t.ent <= pd.Timestamp(b))]

# ---------------------------------------------------------------- 暴走チェック
def bousou(make_trades, raw, cuts, **kw):
    """make_trades(raw)->trades。データを cuts の日で切って回し、切った日より前に降りた戦が全期間と同じか(先読みなし)"""
    full = make_trades(raw); res = []
    for cut in cuts:
        cut = pd.Timestamp(cut); p = make_trades(raw[raw.index < cut])
        lim = cut - pd.Timedelta('5D')
        f = full[pd.to_datetime(full.ext) < lim]; q = p[pd.to_datetime(p.ext) < lim]
        same = len(f) == len(q) and (f.ent.values == q.ent.values).all() and np.allclose(f.pips.values, q.pips.values)
        res.append((str(cut.date()), len(f), same))
    return res, full

# ---------------------------------------------------------------- ぶん回し
_G = {}
def _call(p):
    r = _G['fn'](**p); r.update(p); return r

def grid_turbo(fn, space, workers=None):
    """ターボ:組を CPU の数だけ並べて同時に回す(fork で Market を写すので読み直さない)"""
    import multiprocessing as mp
    keys = list(space); combos = [dict(zip(keys, c)) for c in itertools.product(*[space[k] for k in keys])]
    _G['fn'] = fn; t0 = time.time(); workers = workers or os.cpu_count()
    if workers <= 1 or len(combos) < 4: rows = [_call(p) for p in combos]
    else:
        with mp.get_context('fork').Pool(workers) as pool: rows = pool.map(_call, combos, chunksize=max(1, len(combos) // (workers * 4)))
    df = pd.DataFrame(rows); df.attrs['秒'] = round(time.time() - t0, 1); return df

def grid(fn, space, keep=None):
    """space={'名前':[値,...]}。fn(**組)->dict(成績)。全部の組を回して表で返す。台地(前後の値でも確かめる年がプラス)の印も付ける"""
    keys = list(space); rows = []; t0 = time.time()
    for combo in itertools.product(*[space[k] for k in keys]):
        p = dict(zip(keys, combo)); r = fn(**p); r.update(p); rows.append(r)
    df = pd.DataFrame(rows); df.attrs['秒'] = round(time.time() - t0, 1)
    return df

def daichi(df, keys, col='確15-21_p'):
    """数字の軸ごとに、前後の値でも col がプラスなら台地=True"""
    ok = []
    for _, r in df.iterrows():
        good = r[col] > 0
        for k in keys:
            vals = sorted(df[k].unique())
            if len(vals) < 3 or not np.issubdtype(type(vals[0]), np.number): continue
            i = vals.index(r[k])
            for nb in (i - 1, i + 1):
                if 0 <= nb < len(vals):
                    m = (df[k] == vals[nb])
                    for k2 in keys:
                        if k2 != k: m &= (df[k2] == r[k2])
                    if m.any() and df[m][col].iloc[0] <= 0: good = False
        ok.append(good)
    df = df.copy(); df['台地'] = ok; return df

# ================================================================ 改良(11-06 たくちん「エンジンさき 改良は?」)
def cost_adjust(t, d, swap_long=0.0, swap_short=0.0, spr_hour=None, wed3=True, rollover_hour=0):
    """研究台の甘い所を足す(付けなければ今と同じ)。
    swap_long/swap_short:1晩あたりの pips(買い・売り)。持っている間にサーバー時刻 rollover_hour を何回またいだか。水曜をまたぐ晩は3倍(wed3)
    spr_hour:{時: 足すpips}。その時刻(サーバー時刻)に入った・降りた玉に、広がったスプレッドを足す(例 {0: 5.0})"""
    t = t.copy(); ent = pd.to_datetime(t.ent); ext = pd.to_datetime(t.ext)
    if swap_long or swap_short:
        nights = []
        for a, b in zip(ent, ext):
            days = pd.date_range(a.normalize() + pd.Timedelta(hours=rollover_hour), b, freq='D')
            days = days[(days > a) & (days <= b)]
            nights.append(sum(3 if (wed3 and dd.weekday() == 2) else (0 if dd.weekday() >= 5 else 1) for dd in days))
        t['晩'] = nights; t['swap'] = t['晩'] * (swap_long if d > 0 else swap_short); t['pips'] = t.pips + t.swap
    if spr_hour:
        add = ent.dt.hour.map(lambda h: spr_hour.get(h, 0.0)).values + ext.dt.hour.map(lambda h: spr_hour.get(h, 0.0)).values
        t['広がり'] = add; t['pips'] = t.pips - add
    return t

def nenbetsu(t, span=3):
    """年ごとの強さ:年ごとの損益・負けた年の数・一番悪い年・span 年ずつ区切った時の PF"""
    y = pd.to_datetime(t.ent).dt.year; g = t.groupby(y).pips.sum()
    pf = {}
    ys = sorted(g.index)
    for i in range(len(ys) - span + 1):
        z = t[y.between(ys[i], ys[i + span - 1])]; pf[f'{ys[i]}-{ys[i+span-1]}'] = stat(z)['pf']
    return dict(年ごと=g.round(0).to_dict(), 負けた年=int((g < 0).sum()), 年の数=len(g), 一番悪い年=(int(g.idxmin()), round(float(g.min()), 0)), 区切りPF=pf)

def montecarlo(t, n=2000, seed=1, capital_yen=None, lot=0.1, pip_yen_per_lot=1000.0):
    """山(camp)ごとの損益の順番を n 通りに並べ替え、降りた順の最大DDの散らばりを見る(含み損は入れていない)。
    capital_yen と lot を入れると円にする(ドル円 1ロット=1pip 1000円)。1玉 lot ロットのつもり"""
    rng = np.random.default_rng(seed); g = t.groupby('camp').pips.sum().values; dds = np.empty(n)
    for k in range(n):
        eq = np.cumsum(rng.permutation(g)); dds[k] = (np.maximum.accumulate(np.r_[0, eq]) - np.r_[0, eq]).max()
    r = dict(山=len(g), DD中央=round(float(np.median(dds)), 0), DD95=round(float(np.percentile(dds, 95)), 0), DD99=round(float(np.percentile(dds, 99)), 0), 今の順のDD=round(float((np.maximum.accumulate(np.r_[0, np.cumsum(g)]) - np.r_[0, np.cumsum(g)]).max()), 0))
    if capital_yen:
        yen = pip_yen_per_lot * lot
        r.update(合計円=round(float(g.sum() * yen)), DD95円=round(r['DD95'] * yen), DD95の資金に対する割合=round(r['DD95'] * yen / capital_yen * 100, 1))
    return r

def hitotsuzutsu(run, base_kw, parts, split, extra=None):
    """1個ずつの道具:base_kw の形から、parts={名前: 上書きする kw} を1つずつ当てて、今との差を表にする。
    run(**kw)->(trades, base)。extra(t)->dict を足すと列が増える(大山など)"""
    rows = []
    for nm, over in [('今の形', {})] + list(parts.items()):
        kw = dict(base_kw); kw.update(over); t, b = run(**kw); r = report(t, b, kw.get('d', 1), split); r['名前'] = nm
        if extra: r.update(extra(t))
        rows.append(r)
    df = pd.DataFrame(rows); base = df.iloc[0]
    for c in [c for c in df.columns if c.endswith('_p')]: df[c + '差'] = (df[c] - base[c]).round(0)
    kk = [c for c in split if c.startswith('確')]
    df['判定'] = ['今' if i == 0 else ('○' if all(df.loc[i, f'{k}_p差'] >= 0 for k in kk) else ('×' if all(df.loc[i, f'{k}_p差'] < 0 for k in kk) else '△')) for i in range(len(df))]
    return df

# ================================================================ 改良2(11-06 たくちん「ab」)
def walk_forward(run_fn, space, years, learn=3, pick='全_pf', min_n=10):
    """歩いて確かめる:各年 Y について、Y-learn〜Y-1 年で space の中から pick が一番の組を選び、その組を Y 年に当てる。
    run_fn(**組)->trades。返り値:年ごとの 選んだ組・その年の損益、と 当てた年だけを足した合計(=見ていない年の成績)"""
    keys = list(space); combos = [dict(zip(keys, c)) for c in itertools.product(*[space[k] for k in keys])]
    allt = [(c, run_fn(**c)) for c in combos]; rows = []
    for Y in years:
        best = None; bv = -1e18
        for c, t in allt:
            y = pd.to_datetime(t.ent).dt.year; z = t[y.between(Y - learn, Y - 1)]; s = stat(z)
            v = s.get(pick.replace('全_', ''), np.nan) if pick != '全_p' else s['sum']
            if pick == '全_pf': v = s['pf']
            if s['n'] >= min_n and v is not None and not (isinstance(v, float) and np.isnan(v)) and v > bv: bv = v; best = (c, t)
        if best is None: continue
        c, t = best; y = pd.to_datetime(t.ent).dt.year; z = t[y == Y]
        rows.append(dict(年=Y, 選んだ組=str(c), 学んだ年の成績=round(bv, 2), その年の損益=round(z.pips.sum(), 1), 玉=len(z)))
    df = pd.DataFrame(rows); df.attrs['見ていない年の合計'] = round(df['その年の損益'].sum(), 1) if len(df) else 0; return df

def data_awase(raw_a, raw_b, tf='1h', shifts=range(-12, 13)):
    """データ合わせ:raw_a と raw_b の tf 足を、時刻を shift 時間ずらして重ね、終値の差が一番小さいずれを探す。
    返り値:一番合うずれ・その時の 重なった足の数・終値の差の平均(pips)・高値・安値の差・1p以内に合う割合"""
    A = raw_a.resample(tf).agg(AGG).dropna(); B0 = raw_b.resample(tf).agg(AGG).dropna(); best = None
    for sh in shifts:
        B = B0.copy(); B.index = B.index + pd.Timedelta(hours=sh); j = A.join(B, rsuffix='_b', how='inner')
        if len(j) < 100: continue
        dc = (j.c - j.c_b).abs().mean() / PIP
        if best is None or dc < best[1]: best = (sh, dc, j)
    sh, dc, j = best
    return dict(ずれ時間=sh, 重なった足=len(j), 終値の差の平均p=round(dc, 2), 高値の差の平均p=round((j.h - j.h_b).abs().mean() / PIP, 2),
                安値の差の平均p=round((j.l - j.l_b).abs().mean() / PIP, 2), 終値が1p以内=round(float(((j.c - j.c_b).abs() <= PIP).mean() * 100), 1))

def yen_curve(t, base, d=1, capital_yen=1_000_000, lot=0.1, leverage=25, pip_yen_per_lot=1000.0, unit=100_000):
    """円と証拠金:1玉 lot ロット。降りた順の資金の増え方と、持っている玉の証拠金(値段×1万通貨×lot/レバレッジ)が資金(含み損込み)を超えないか"""
    C = base.c.values; idx = base.index.values; n = len(idx); fl = np.zeros(n); rl = np.zeros(n + 1); held = np.zeros(n)
    A = np.searchsorted(idx, t.ent.values); B = np.searchsorted(idx, t.ext.values)
    for a, b, e in zip(A, B, t.e.values): fl[a:b] += (C[a:b] - e) / PIP * d; held[a:b] += 1
    np.add.at(rl, B, t.pips.values); eq_p = fl + np.cumsum(rl)[:n]
    yen = pip_yen_per_lot * lot; eq = capital_yen + eq_p * yen
    margin = held * C * unit * lot / leverage
    lvl = np.where(margin > 0, eq / np.maximum(margin, 1) * 100, np.inf)
    return dict(最後の資金=round(float(eq[-1])), 一番へこんだ資金=round(float(eq.min())), 一番へこんだ時=str(pd.Timestamp(idx[int(eq.argmin())]).date()),
                最大の証拠金=round(float(margin.max())), 証拠金維持率の一番低い=round(float(lvl.min()), 0), 同時最大玉=int(held.max()))

# ================================================================ エントリー調節(11-06 たくちん「10まん2000 レバレッジ33% で エントリ調節きくように」)
def lot_sizing(t, base, d=1, capital_yen=102_000, margin_cap=0.33, leverage=25, step=0.01, min_lot=0.01, max_lot=100.0,
               maxpos=5, fixed_lot=None, unit=100_000, pip_yen_per_lot=1000.0, compound=True, stopout=None, dd_pips_per_lot=None, dd_budget=None):
    """入るたびにロットを決めて、円で回し直す【置き換え】。
    margin_cap:持っている玉の証拠金の合計が、資金(含み損込み)の margin_cap を超えないようにする。残りの枠(maxpos−持っている玉)で割ってロットを決める
    fixed_lot:決め打ちのロット(None=上の決め方)。compound=False なら資金は最初のままでロットを決める
    返り値:玉ごとのロットを足した表と、円のまとめ(最後の資金・一番へこんだ資金・維持率・入れなかった合図)"""
    C = base.c.values; idx = base.index.values; T = t.sort_values('ent').reset_index(drop=True).copy()
    A = np.searchsorted(idx, T.ent.values); B = np.searchsorted(idx, T.ext.values)
    lots = np.zeros(len(T)); skip = 0; realized = 0.0; open_ = []          # (ext_index, entry_price, lot, pips)
    ev = sorted([(a, 1, k) for k, a in enumerate(A)] + [(b, 0, k) for k, b in enumerate(B)])   # 同じ足は降りが先
    for i, kind, k in ev:
        if kind == 0:
            if lots[k] > 0: realized += T.pips[k] * pip_yen_per_lot * lots[k]
            open_ = [o for o in open_ if o != k]; continue
        price = C[max(i - 1, 0)]
        fl = sum((C[max(i - 1, 0)] - T.e[o]) / PIP * d * pip_yen_per_lot * lots[o] for o in open_)
        eq = (capital_yen + realized + fl) if compound else capital_yen
        used = sum(price * unit * lots[o] / leverage for o in open_)
        per_lot = price * unit / leverage
        if fixed_lot is not None: lot = fixed_lot
        elif dd_pips_per_lot:                                          # 落ち込みで決める:1玉あたり DD(pips)×ロット×最大の発数 が 資金の dd_budget に収まる
            lot = np.floor(eq * dd_budget / (dd_pips_per_lot * pip_yen_per_lot) / step) * step
        else:
            room = eq * margin_cap - used; slots = max(maxpos - len(open_), 1)
            lot = np.floor(max(room, 0) / slots / per_lot / step) * step
        lot = min(lot, max_lot)
        cap_ = 1.0 if (fixed_lot is not None or dd_pips_per_lot) else margin_cap
        if lot < min_lot - 1e-12 or used + per_lot * lot > eq * cap_ + 1e-6: skip += 1; continue
        lots[k] = round(lot, 4); open_.append(k)
    T['lot'] = lots; T['円'] = T.pips * pip_yen_per_lot * T.lot
    # 毎本の資金(含み損込み)と証拠金
    n = len(idx); fl = np.zeros(n); rl = np.zeros(n + 1); mg = np.zeros(n)
    for a, b, e, l, p in zip(A, B, T.e.values, lots, T.pips.values):
        if l <= 0: continue
        fl[a:b] += (C[a:b] - e) / PIP * d * pip_yen_per_lot * l; mg[a:b] += C[a:b] * unit * l / leverage; rl[b] += p * pip_yen_per_lot * l
    eq = capital_yen + fl + np.cumsum(rl)[:n]
    lvl = np.where(mg > 0, eq / np.maximum(mg, 1e-9) * 100, np.inf)
    so_at = None
    if stopout is not None:                                         # 強制決済:維持率が stopout% を下回ったら全部決済して、そこで止まる(ゼロカットで0円より下にはならない)
        hit = np.where((lvl < stopout) | (eq <= 0))[0]
        if len(hit):
            k0 = hit[0]; so_at = str(pd.Timestamp(idx[k0])); eq = eq.copy(); eq[k0:] = max(eq[k0], 0.0); lvl = lvl.copy(); lvl[k0:] = np.inf
    peak = np.maximum.accumulate(eq)
    s = dict(最初の資金=capital_yen, 最後の資金=round(float(eq[-1])), 増えた倍率=round(float(eq[-1] / capital_yen), 2),
             一番へこんだ資金=round(float(eq.min())), 一番大きい落ち込み円=round(float((peak - eq).max())), 落ち込み率=round(float(((peak - eq) / peak).max() * 100), 1),
             証拠金維持率の一番低い=round(float(lvl.min()), 0), 入った玉=int((lots > 0).sum()), 入れなかった合図=skip,
             ロット最小=float(lots[lots > 0].min()) if (lots > 0).any() else 0, ロット最大=float(lots.max()), 強制決済=so_at)
    return T, s
