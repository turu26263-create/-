# DragonTactics_Infinite_Reach_v3.mq4 の決まりをそのまま Python に写したバックテスト
# データ: HistData 1分足(Bid、EST固定) -> 5分足・1時間足に組む
import sys, glob, numpy as np, pandas as pd

SPREAD = float(sys.argv[1]) if len(sys.argv) > 1 else 0.3   # pips
FILES = sys.argv[2:] or sorted(glob.glob(sys.path[0] + '/data/m1/*.csv'))
PIP = 0.01
MAXPOS, ADDSTEP, CHB, CHK = 14, 20.0, 22, 3.0
MAXSPREAD = 3.0
LOTYEN_PER_PIP = 100.0  # 0.1ロット = 1万通貨 -> 1pip=100円

dfs = []
for f in FILES:
    d = pd.read_csv(f, header=None, names=['d', 't', 'o', 'h', 'l', 'c', 'v'])
    d.index = pd.to_datetime(d.d + ' ' + d.t, format='%Y.%m.%d %H:%M')
    dfs.append(d[['o', 'h', 'l', 'c']])
m1 = pd.concat(dfs).sort_index()
m1 = m1[~m1.index.duplicated()]
agg = dict(o='first', h='max', l='min', c='last')
m5 = m1.resample('5min').agg(agg).dropna()
h1 = m1.resample('1h').agg(agg).dropna()

def emas(c):
    return [c.ewm(span=p, adjust=False).mean() for p in (5, 9, 21)]

def order(c):
    a, b, s = emas(c)
    return np.where((a > b) & (b > s), 1, np.where((a < b) & (b < s), -1, 0))

m5['loc'] = pd.Series(order(m5.c), index=m5.index).shift(1)          # 確定足(shift1)
h1o = pd.Series(order(h1.c), index=h1.index)
# M5 足が開いた時点で、最後に確定した H1 足の並び
h1_closed_at = h1o.copy(); h1_closed_at.index = h1o.index + pd.Timedelta(hours=1)
m5['trend'] = h1_closed_at.reindex(m5.index, method='ffill')
tr = pd.concat([m5.h - m5.l, (m5.h - m5.c.shift()).abs(), (m5.l - m5.c.shift()).abs()], axis=1).max(axis=1)
atr = tr.rolling(14).mean().shift(1)
hh = m5.h.rolling(CHB).max().shift(1)
ll = m5.l.rolling(CHB).min().shift(1)
m5['chL'] = hh - CHK * atr     # 買いの損切り
m5['chS'] = ll + CHK * atr     # 売りの損切り
m5 = m5.dropna()

O, H, L, C = m5.o.values, m5.h.values, m5.l.values, m5.c.values
LOC, TRD, CHL, CHS = m5['loc'].values, m5.trend.values, m5.chL.values, m5.chS.values
T = m5.index
spr = SPREAD * PIP

pos = []         # [dir, entry, sl, open_time]
trades = []      # (open, close, dir, pips, reason, campaign)
camp = 0
eq_closed = 0.0
eq_curve = np.zeros(len(m5))

def close_all(i, why, px_bid):
    global eq_closed, pos
    for d, e, sl, ot in pos:
        exitp = px_bid if d > 0 else px_bid + spr
        p = (exitp - e) / PIP * d
        eq_closed += p
        trades.append((ot, T[i], d, p, why, camp))
    pos = []

def open_(i, d):
    global camp
    px = O[i] + spr if d > 0 else O[i]
    sl = CHL[i] if d > 0 else CHS[i]
    if d > 0 and sl > px: sl = px - 10 * PIP
    if d < 0 and sl < px: sl = px + 10 * PIP
    if not pos: camp += 1
    pos.append([d, px, sl, T[i]])

for i in range(len(m5)):
    trend, loc = int(TRD[i]), int(LOC[i])
    # --- 足の始まり:EAの判断 ---
    if pos:
        d = pos[0][0]
        if trend == -d:
            close_all(i, 'doten', O[i])
            if loc == trend and SPREAD <= MAXSPREAD: open_(i, trend)
        elif trend == 0:
            close_all(i, 'narabi_kuzure', O[i])
        else:
            bid = O[i]
            for p in pos:
                sl = CHL[i] if d > 0 else CHS[i]
                if d > 0 and sl > p[2] + 0.001 and sl < bid: p[2] = sl
                if d < 0 and sl < p[2] - 0.001 and sl > bid + spr: p[2] = sl
            if len(pos) < MAXPOS and loc == d:
                px = O[i] if d > 0 else O[i] + spr
                if d * (px - pos[-1][1]) >= ADDSTEP * PIP: open_(i, d)
    elif trend != 0 and loc == trend:
        open_(i, trend)
    # --- 足の途中:損切りに掛かるか ---
    keep = []
    for p in pos:
        d, e, sl, ot = p
        if d > 0 and L[i] <= sl:
            ex = min(O[i], sl) if O[i] <= sl else sl
            pp = (ex - e) / PIP; eq_closed += pp; trades.append((ot, T[i], d, pp, 'SL', camp))
        elif d < 0 and H[i] + spr >= sl:
            ex = max(O[i] + spr, sl) if O[i] + spr >= sl else sl
            pp = (e - ex) / PIP; eq_closed += pp; trades.append((ot, T[i], d, pp, 'SL', camp))
        else:
            keep.append(p)
    pos = keep
    fl = sum(((C[i] - e) if d > 0 else (e - C[i] - spr)) / PIP for d, e, sl, ot in pos)
    eq_curve[i] = eq_closed + fl

tr = pd.DataFrame(trades, columns=['open', 'close', 'dir', 'pips', 'why', 'camp'])
g = tr[tr.pips > 0].pips.sum(); l = -tr[tr.pips <= 0].pips.sum()
cp = tr.groupby('camp').pips.sum()
peak = np.maximum.accumulate(eq_curve); dd = (peak - eq_curve).max()
print(f'期間 {T[0]} - {T[-1]}  スプレッド {SPREAD}pips')
print(f'玉の数 {len(tr)}  勝ち {int((tr.pips>0).sum())}  勝率 {(tr.pips>0).mean()*100:.1f}%')
print(f'戦(一番槍から全部決済まで) {len(cp)}  勝ち {int((cp>0).sum())}  勝率 {(cp>0).mean()*100:.1f}%')
print(f'総獲得値幅 {tr.pips.sum():+,.0f} pips   PF {g/l if l else float("inf"):.2f}')
print(f'最大ドローダウン {dd:,.0f} pips = 0.1ロットで {dd*LOTYEN_PER_PIP:,.0f}円')
print('降りた理由', tr.why.value_counts().to_dict())
print('年ごと pips', tr.groupby(tr.close.dt.year).pips.sum().round(0).to_dict())
first = tr.iloc[0]; print('最初の玉', first.open, '買い' if first.dir > 0 else '売り')
tr.to_csv(sys.path[0] + f'/trades_v3_spr{SPREAD}.csv', index=False)
