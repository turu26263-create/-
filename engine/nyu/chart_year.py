# 1年の入り降りチャート(11-06 たくちん「2017 エントリ チャート出だして」)
# 使い方: python3 chart_year.py <MT4 1時間足の置き場> <年> <書き出し先.png>
import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0, __file__.rsplit('/', 1)[0])
from nyu import *; from tai_parts import *
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt; from matplotlib import font_manager
font_manager.fontManager.addfont('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'); plt.rcParams['font.family'] = 'WenQuanYi Zen Hei'; plt.rcParams['axes.unicode_minus'] = False
srv = Market(load_cached(sys.argv[1]), 'server'); Y = int(sys.argv[2]); out = sys.argv[3]; KK = int(sys.argv[4]) if len(sys.argv) > 4 else 0; UP = len(sys.argv) > 5 and sys.argv[5] == 'up'
SELL = len(sys.argv) > 6 and sys.argv[6] == 'sell'
t, b = run_tai(srv, '1D', '4h', '1h', 1, ('1D', '219'), maxpos=5, n8=False, reenter=True, tp=('4h', 3.5), ts=550, avoid_in=(0,), avoid_out=(0,), kai_k9=KK, big21_up=UP); t['d'] = 1
if SELL:
    ts_, _ = run_tai(srv, '1D', '4h', '1h', -1, ('1D', '219'), maxpos=5, n8=False, reenter=True, tp=('4h', 3.5), ts=550, avoid_in=(0,), avoid_out=(0,), kai_k9=KK, big21_up=UP); ts_['d'] = -1
    t = pd.concat([t, ts_]).sort_values('ent').reset_index(drop=True)
D = srv.feat('1D'); a, z = pd.Timestamp(f'{Y}-01-01'), pd.Timestamp(f'{Y+1}-01-01')
D = D[(D.index >= a - pd.Timedelta('20D')) & (D.index < z + pd.Timedelta('10D'))]
y = t[(t.ent >= a) & (t.ent < z)].reset_index(drop=True)
fig, (ax, ax2) = plt.subplots(2, 1, figsize=(22, 12), gridspec_kw={'height_ratios': [4, 1]}, sharex=True)
x = mdates = matplotlib.dates
for i, r in D.iterrows():                                          # 日足のローソク
    c = '#d23' if r.c < r.o else '#2a7'
    ax.plot([i, i], [r.l, r.h], color=c, lw=0.8); ax.add_patch(plt.Rectangle((mdates.date2num(i) - 0.35, min(r.o, r.c)), 0.7, max(abs(r.c - r.o), 0.005), color=c))
ax.plot(D.index, D.e9, color='#e60', lw=1.6, label='日足 EMA9'); ax.plot(D.index, D.e21, color='#36c', lw=1.6, label='日足 EMA21')
ax.fill_between(D.index, D.md - 2 * D.sd, D.md + 2 * D.sd, color='#999', alpha=0.08, label='日足 ±2σ')
up = D.e9 > D.e21                                                   # 日足921の間(刺身の期間)をうすく塗る
for s_, g in D[up].groupby((up != up.shift()).cumsum()[up]): ax.axvspan(g.index[0], g.index[-1] + pd.Timedelta('1D'), color='#2a7', alpha=0.06)
col = {'利確': '#1a9', 'TS': '#f80', '芯の降り': '#555', '足しの降り': '#555', '網': '#c00', '建値': '#888'}
for k, r in y.iterrows():
    ax.plot([r.ent, r.ext], [r.e, r.x], color='#1a9' if r.pips > 0 else '#c00', lw=1.2, alpha=0.8)
    if r.d > 0:
        ax.scatter(r.ent, r.e, marker='^', s=90, color='#06c', zorder=5, edgecolor='k', lw=0.5)
        ax.scatter(r.ext, r.x, marker='v', s=90, color=col.get(r.why, '#555'), zorder=5, edgecolor='k', lw=0.5)
    else:
        ax.scatter(r.ent, r.e, marker='v', s=110, color='#c0c', zorder=5, edgecolor='k', lw=0.5)
        ax.scatter(r.ext, r.x, marker='^', s=90, color=col.get(r.why, '#555'), zorder=5, edgecolor='k', lw=0.5)
    ax.annotate(f"{k+1}", (r.ent, r.e), xytext=(0, -16 if r.d > 0 else 12), textcoords='offset points', ha='center', fontsize=8, color='#06c')
ax.scatter([], [], marker='^', color='#06c', label='買い(番号)'); ax.scatter([], [], marker='v', color='#c0c', label='売り(番号)'); ax.scatter([], [], marker='v', color='#1a9', label='利確(4h±3.5σ)')
ax.scatter([], [], marker='v', color='#555', label='日足219で降り'); ax.scatter([], [], marker='v', color='#f80', label='TS 550p')
ax.legend(loc='upper left', fontsize=10, ncol=4); ax.grid(alpha=0.3)
ax.set_title(f'{Y}年 ドル円 日足 クジラの刺身' + (f'【許しの入りは日足9の{KK}本目から】' if KK else '') + ('【売り買い】' if SELL else '') + ('【日足21が上向きの時だけ】' if UP else '') + f'(決まった形:日足9上・4h21上・1hで入る・最大5発・4h+3.5σ利確・TS550・日足219で降り・0時は1時へ)  {len(y)}玉 合計{y.pips.sum():+.0f}p  緑の帯=日足921の間', fontsize=13)
cum = y.sort_values('ext'); ax2.step(cum.ext, cum.pips.cumsum(), where='post', color='#06c'); ax2.axhline(0, color='k', lw=0.6)
ax2.set_ylabel('降りた順の合計 p'); ax2.grid(alpha=0.3); ax.set_xlim(a - pd.Timedelta('5D'), z + pd.Timedelta('5D'))
plt.tight_layout(); plt.savefig(out, dpi=110)
print(f'{Y}年 {len(y)}玉 合計{y.pips.sum():+.1f}p')
NAME = {'芯の降り': '日足の921・219で降り', '足しの降り': '日足の921・219で降り', '利確': '利確(4h±3.5σ)', 'TS': 'TS 550p', '網': '網', '建値': '建値'}
for k, r in y.iterrows(): print(f" {k+1:2}番 {r.ent:%m/%d %H時} {r.e:.3f}で{'買い' if r.d > 0 else '売り'} → {r.ext:%m/%d %H時} {r.x:.3f}で降り {r.pips:+.0f}p {NAME.get(r.why, r.why)}(一番伸びた時 +{r.mfe:.0f}p・一番沈んだ時 {r.mae:.0f}p)")
