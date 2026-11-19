# 11-19 たくちん「べつのおおやま いちにちまえから 画像出して」
# 大山(日足の219〜921が1,000p以上)を1つ選び、始まりの1日前から、ローソク・9(青)・21(赤)・帯(±1σ・±2σ)と
# 歩いて作り直した玉(全部品)の入り・降りを番号つきの札で描く。1枚目=1時間足で始まりの数日、2枚目=4時間足で山の全部
# 使い方: python3 oyama_gazou.py 2024-07-16 2024-10-01 [1時間足で見る日数]
import sys, numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib import font_manager
plt.rcParams['font.family'] = 'IPAGothic'
st = pd.Timestamp(sys.argv[1]); en = pd.Timestamp(sys.argv[2]); ndays = int(sys.argv[3]) if len(sys.argv) > 3 else 8
OUT = '/home/user/-/engine/kekka_tai/nyu'
r = pd.read_csv('/home/user/data/mt4/USDJPY60.csv', header=None, names=list('dtohlcv')); r.index = pd.to_datetime(r.d + ' ' + r.t, format='%Y.%m.%d %H:%M')
RAW = r[['o', 'h', 'l', 'c']].astype(float); AG = dict(o='first', h='max', l='min', c='last')
def sen(b):
    b = b.copy(); b['e9'] = b.c.ewm(span=9, adjust=False).mean(); b['e21'] = b.c.ewm(span=21, adjust=False).mean()
    b['md'] = b.c.rolling(20).mean(); b['sd'] = b.c.rolling(20).std(ddof=0); return b
H1 = sen(RAW); H4 = sen(RAW.resample('4h').agg(AG).dropna()); D1 = sen(RAW.resample('1D').agg(AG).dropna())
A = pd.read_csv(f'{OUT}/歩いて検証_全部品_入口出口_20261119.csv', parse_dates=['ent', 'ext'])
mae = st - pd.Timedelta('1D')                                  # 始まりの1日前から
T = A[(A.ent >= mae) & (A.ent <= en + pd.Timedelta('1D'))].sort_values(['ent', '部品']).reset_index(drop=True)
T['番'] = np.arange(1, len(T) + 1)
MUKI = {'クジラ買い': 1, 'クジラ売り': -1, 'ドテン買い': 1, '鯛': 1, '押し目買い': 1, '押し目売り': -1, 'しあわせ買い': 1, 'しあわせ売り': -1}
IRO = {'クジラ買い': '#1a56db', 'クジラ売り': '#d62828', 'ドテン買い': '#0e9f6e', '鯛': '#7e3af2', '押し目買い': '#0694a2', '押し目売り': '#c27803', 'しあわせ買い': '#e74694', 'しあわせ売り': '#9f580a'}
# 日足の219/921 が確定した時刻
up = D1.e9 > D1.e21; cr = up != up.shift(); kak = [(t + pd.Timedelta('1D'), '日足921確定' if up.loc[t] else '日足219確定') for t in D1.index[cr][1:]]

def kaku(B, a, b, ttl, fn, w):
    x = B[(B.index >= a) & (B.index <= b)]; xi = np.arange(len(x)); pos = {t: i for i, t in enumerate(x.index)}
    def at(t):   # 時刻 t を含む足の番号
        k = x.index.searchsorted(t, side='right') - 1; return k if 0 <= k < len(x) else None
    fig, ax = plt.subplots(figsize=(w, 9), dpi=110)
    for c, cl, lw, ls in [('e9', '#2f6fd6', 1.6, '-'), ('e21', '#d23b3b', 1.6, '-')]: ax.plot(xi, x[c], color=cl, lw=lw, ls=ls, label={'e9': '9', 'e21': '21'}[c])
    for k_, cl, ls in [(1, '#9a9a9a', '--'), (2, '#d6b34a', '-')]:
        for s in (1, -1): ax.plot(xi, x.md + s * k_ * x.sd, color=cl, lw=0.9, ls=ls, label=f'±{k_}σ' if s > 0 else None)
    bw = 0.6
    for i, (o, h, l, c) in enumerate(x[['o', 'h', 'l', 'c']].values):
        yo = c >= o; ax.vlines(i, l, h, color='#333', lw=0.8)
        ax.add_patch(plt.Rectangle((i - bw / 2, min(o, c)), bw, max(abs(c - o), 0.002), facecolor='white' if yo else '#222', edgecolor='#222', lw=0.7))
    rngy = x.h.max() - x.l.min(); off = rngy * 0.025
    for t, nm in kak:
        k = at(t)
        if k is not None and a <= t <= b: ax.axvline(k - 0.5, color='#555', ls=':', lw=1.2); ax.text(k + 0.3, x.l.min() - rngy * 0.02, nm, fontsize=10, color='#333', rotation=90, va='top')
    stk = {}
    for rw in T.itertuples():
        d = MUKI[rw.部品]; cl = IRO[rw.部品]; k = at(rw.ent) if a <= rw.ent <= b else None   # 窓の外の入りは描かない(右端に積もっていたのを直した)
        if k is not None:
            n_ = stk.get(k, 0); stk[k] = n_ + 1
            yv = (x.l.iloc[k] - off * (1 + 1.6 * n_)) if d > 0 else (x.h.iloc[k] + off * (1 + 1.6 * n_))
            ax.scatter(k, yv, marker='^' if d > 0 else 'v', s=90, color=cl, zorder=5, edgecolor='black', lw=0.5)
            ax.text(k + 0.4, yv, str(rw.番), fontsize=9, color=cl, weight='bold', va='center')
        k2 = at(rw.ext)
        if k2 is not None and a <= rw.ext <= b:
            ax.scatter(k2, rw.x, marker='x', s=80, color=cl, zorder=6, lw=2); ax.text(k2 + 0.4, rw.x, f'{rw.番}降', fontsize=8, color=cl)
    lab = [(i, t) for i, t in enumerate(x.index) if (t.hour == 0 if B is H1 else (t.hour == 0 and t.dayofweek == 0))]
    ax.set_xticks([i for i, _ in lab]); ax.set_xticklabels([t.strftime('%m/%d') for _, t in lab], fontsize=9)
    for i, t in lab: ax.axvline(i - 0.5, color='#eee', lw=0.8, zorder=0)
    hs = [plt.Line2D([], [], marker='^', ls='', color=IRO[k]) for k in IRO if k in set(T.部品)]
    l1 = ax.legend(loc='upper right', fontsize=9); ax.add_artist(l1)
    ax.legend(hs, [k for k in IRO if k in set(T.部品)], loc='lower left', fontsize=9, title='入り(▲買い▼売り)・降り(×)')
    ax.set_title(ttl, fontsize=13); ax.set_xlim(-1, len(x) + 2); ax.set_ylim(x.l.min() - rngy * 0.18, x.h.max() + rngy * 0.08); ax.grid(axis='y', color='#eee')
    fig.tight_layout(); fig.savefig(fn); plt.close(fig); print('描いた', fn, len(x), '本')

nm = f'{st:%Y%m%d}'
kaku(H1, mae, mae + pd.Timedelta(f'{ndays}D'), f'大山 {st:%Y/%m/%d}〜{en:%m/%d}(1時間足・始まりの1日前 {mae:%m/%d} から {ndays}日)', f'{OUT}/大山_{nm}_1時間足.png', 20)
kaku(H4, mae, en + pd.Timedelta('3D'), f'大山 {st:%Y/%m/%d}〜{en:%m/%d}(4時間足・山の全部)', f'{OUT}/大山_{nm}_4時間足.png', 22)
T['入り値'] = T.e.round(3); T['降り値'] = T.x.round(3); T['p'] = T.pips.round(0)
print(T[['番', '部品', 'ent', '入り値', '局面', 'ext', '降り値', 'why', 'p']].to_string(index=False))
