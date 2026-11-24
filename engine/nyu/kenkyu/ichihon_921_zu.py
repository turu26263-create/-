# ichihon_921.py の表を図にする:ローソク・9/21・川(1σ)・遅行スパン(21本前に描く)と、921/219 の合図の足に番号札。引数=始め 終わり
import sys, pandas as pd, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
for p in ['/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc']:
    try: fm.fontManager.addfont(p); plt.rcParams['font.family'] = fm.FontProperties(fname=p).get_name(); break
    except Exception: pass
a, b = sys.argv[1], sys.argv[2]; out = sys.argv[3]
r = pd.read_csv('/home/user/data/mt4/USDJPY60.csv', header=None, names=['d', 't', 'o', 'h', 'l', 'c', 'v'])
r.index = pd.to_datetime(r.d + ' ' + r.t, format='%Y.%m.%d %H:%M'); c = r.c
r['e9'] = c.ewm(span=9, adjust=False).mean(); r['e21'] = c.ewm(span=21, adjust=False).mean(); r['md'] = c.rolling(20).mean(); r['sd'] = c.rolling(20).std(ddof=0)
r['chi'] = c.shift(-21)                                     # 遅行スパン:今の終値を21本前の位置に描く
w = r.loc[a:b].copy(); x = np.arange(len(w))
K = pd.read_csv('/home/user/-/engine/kekka_tai/nyu/ichihon_1h921_219_kouho.csv'); K['足'] = pd.to_datetime(K['足']); K = K[(K['足'] >= w.index[0]) & (K['足'] <= w.index[-1])].reset_index(drop=True)
TM = pd.read_csv('/home/user/-/engine/kekka_tai/nyu/ichihon_1h921_219_tama.csv'); TM['入った足'] = pd.to_datetime(TM['入った足']); TM['降りた足'] = pd.to_datetime(TM['降りた足'])
fig, (ax, tx) = plt.subplots(2, 1, figsize=(22, 14), gridspec_kw=dict(height_ratios=[3, 1.4]))
for k, (t, v) in enumerate(w.iterrows()):
    col = '#d33' if v.c >= v.o else '#36c'; ax.vlines(k, v.l, v.h, color=col, lw=0.7); ax.add_patch(plt.Rectangle((k - 0.35, min(v.o, v.c)), 0.7, max(abs(v.c - v.o), 0.002), color=col))
ax.plot(x, w.e9, color='#1565c0', lw=1.2, label='9'); ax.plot(x, w.e21, color='#c62828', lw=1.2, label='21')
ax.fill_between(x, w.md - w.sd, w.md + w.sd, color='#9e9e9e', alpha=0.18, label='川(1σ)'); ax.plot(x, w.md + 2 * w.sd, color='#bbb', lw=0.6, ls='--'); ax.plot(x, w.md - 2 * w.sd, color='#bbb', lw=0.6, ls='--', label='±2σ(竿先)')
ax.plot(x, w.chi, color='#2e7d32', lw=0.9, label='遅行スパン(21本前に描く)')
pos = {t: k for k, t in enumerate(w.index)}; lines = []
for m, q in K.iterrows():
    k = pos.get(q['足']); 
    if k is None: continue
    buy = q['向き'].startswith('買'); ok = q['判定'] == '入る'; y = w.l.iloc[k] - 0.15 if buy else w.h.iloc[k] + 0.15
    ax.annotate(f'{m+1}', (k, y), ha='center', va='center', fontsize=9, color='white', fontweight='bold',
                bbox=dict(boxstyle='circle,pad=0.2', fc=('#2e7d32' if ok else '#9e9e9e') if buy else ('#c62828' if ok else '#9e9e9e'), ec='none'))
    lines.append(f"{m+1}. {q['足'].strftime('%m/%d %H時')} {q['向き']} 終{q['終']:.3f} 川:{q['川']} 遅行21:{q['遅行21']} 9/21:{q['e9']}/{q['e21']} → {q['判定']}{'' if ok else '(止めた門:' + q['止めた門'] + ')'} エンジン:{q['エンジン']} {q['あわせ']}")
for _, t in TM[(TM['入った足'] >= w.index[0]) & (TM['入った足'] <= w.index[-1])].iterrows():
    k1 = pos.get(t['入った足']); k2 = pos.get(t['降りた足'])
    if k1 is not None: ax.annotate('入' + ('▲' if t['向き'] == '買い' else '▼'), (k1, t['入り値']), fontsize=10, color='k', fontweight='bold')
    if k2 is not None: ax.annotate(f"出({t['理由']}) {t['pips']:+.0f}p", (k2, t['降り値']), fontsize=9, color='#6a1b9a')
tk = list(range(0, len(w), max(1, len(w) // 20))); ax.set_xticks(tk); ax.set_xticklabels([w.index[i].strftime('%m/%d %H') for i in tk], rotation=45, fontsize=8)
ax.legend(loc='upper left', fontsize=9); ax.set_title(f'1時間足 {a}〜{b}:921(緑の札=入る/灰=入らない)・219(赤の札=入る/灰=入らない)と 入口・出口')
tx.axis('off'); tx.text(0, 1, '\n'.join(lines[:40]), va='top', fontsize=8.5, family=plt.rcParams['font.family'])
plt.tight_layout(); plt.savefig(out, dpi=110); print(len(lines), '札')
