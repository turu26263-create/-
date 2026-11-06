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
def _sim(O, H, L, T, E, XC, KC, XA, KA, SLV, TPV, d, maxpos, spr, slmode, reenter, lock, lockcore, ts, ts_start):
    # E 入り / XC・KC 芯の降り(と、その合図の足が閉じた時刻)/ XA・KA 足し玉の降り / SLV 網の高さ(nan=網なし)/ TPV 利確の高さ(nan=なし)
    # slmode 0=網なし 1=網を上げるだけ(売りは下げるだけ)/ lock>0:玉が lock pips 伸びたら次の足から網を建値へ(しあわせセット)
    # 足の中の順番:網 → 利確 → 合図の降り(損な方を先に見る)
    n = len(O); mp = maxpos
    pj = np.zeros(mp, np.int64); pe = np.zeros(mp); psl = np.zeros(mp); pn = np.zeros(mp, np.int64); pc = np.zeros(mp, np.int64); act = np.zeros(mp, np.bool_)
    plk = np.zeros(mp, np.bool_); pmin = np.zeros(mp); pmax = np.zeros(mp); pts = np.zeros(mp, np.bool_)
    out_j = np.zeros(n, np.int64); out_i = np.zeros(n, np.int64); out_e = np.zeros(n); out_x = np.zeros(n); out_n = np.zeros(n, np.int64); out_c = np.zeros(n, np.int64); out_w = np.zeros(n, np.int64)
    out_lo = np.zeros(n); out_hi = np.zeros(n)
    m = 0; camp = 0; cnt = 0; maxheld = 0
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
            if i > j and not np.isnan(psl[s]):
                if d > 0 and L[i] <= psl[s]: ex = min(O[i], psl[s]); why = 3
                if d < 0 and H[i] >= psl[s]: ex = max(O[i], psl[s]) + spr; why = 3
                if why == 3 and plk[s] and abs(psl[s] - pe[s]) < 1e-9: why = 5
                elif why == 3 and pts[s]: why = 6
            if np.isnan(ex) and i > j and not np.isnan(TPV[i]):
                if d > 0 and TPV[i] > pe[s] and H[i] >= TPV[i]: ex = max(O[i], TPV[i]); why = 4          # 利確は入り値より上にある時だけ(線が入り値より下がったら効かない)
                if d < 0 and TPV[i] < pe[s] and L[i] <= TPV[i]: ex = min(O[i], TPV[i]) + spr; why = 4
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
    return out_j[:m], out_i[:m], out_e[:m], out_x[:m], out_n[:m], out_c[:m], out_w[:m], out_lo[:m], out_hi[:m], maxheld, held

WHY = {1: '芯の降り', 2: '足しの降り', 3: '網', 4: '利確', 5: '建値', 6: 'TS'}

def simulate(base, d, E, XC, KC, XA=None, KA=None, SLV=None, maxpos=1, spr=0.003, reenter=True, TPV=None, lock=0.0, lockcore=True, ts=0.0, ts_start=0.0):
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
    r = _sim(O, H, L, T, f(E), f(XC), k(KC), f(XA), k(KA), sl, tp, d, maxpos, spr, 0 if SLV is None else 1, reenter, float(lock), bool(lockcore), float(ts), float(ts_start))
    j, i, e, x, n, c, w, lo, hi, mx, held = r
    t = pd.DataFrame({'ent': base.index.values[j], 'e': e, 'ext': base.index.values[np.minimum(i, len(O) - 1)], 'x': x,
                      'pips': (x - e) / PIP * d, 'n': n, 'camp': c, 'why': [WHY[v] for v in w]})
    t['mae'] = np.where(d > 0, lo - e, e - hi) / PIP; t['mfe'] = np.where(d > 0, hi - e, e - lo) / PIP
    t.attrs['maxheld'] = int(mx); t.attrs['held_at_end'] = int(held)
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
