"""バグバグ修正機(11-06 たくちん「バグバグ修正機 スキルアップ」)
新しい部品・形を足したら、成績を見る前にこれを通す。今までに見つけたミスの型を全部ここで見る。

使い方(研究台):
    from bugbug import bugbug
    ok, lines = bugbug(lambda mk, d: run_tai(mk, '1D', '4h', '1h', d, ('1D','219'), **KW)[0], raw, 'server', maxpos=5, spr=0.003)
    make(mk, d) は Market と向き(1 買い / -1 売り)から玉の表を返す関数。
"""
import numpy as np, pandas as pd
from nyu import Market, kagami, bousou

NAMES = {'芯の降り', '足しの降り', '網', '利確', '建値', 'TS'}


def _overlap_max(t):
    ev = [(e, 1) for e in pd.to_datetime(t.ent)] + [(x, -1) for x in pd.to_datetime(t.ext)]
    ev.sort(key=lambda z: (z[0], z[1])); n = m = 0
    for _, s in ev: n += s; m = max(m, n)
    return m


def tama_check(t, maxpos, spr, d, bar='1h'):
    """玉の表だけで見られるミス。返り値 [(○×△, 文)]"""
    r = []; P = spr * 100  # スプレッドを p で
    if len(t) == 0: return [('△', '玉が0。入りの決まりが全部落としていないか')]
    ent = pd.to_datetime(t.ent); ext = pd.to_datetime(t.ext)
    g = bool(np.isfinite(t.pips.values).all()); r.append(('○' if g else '×', f'損益に数でない物が無い'))
    bad = int((ext <= ent).sum()); r.append(('○' if bad == 0 else '×', f'降りが入りより後(違う玉 {bad})'))
    odd = sorted(set(t.why) - NAMES); r.append(('○' if not odd else '×', f'降りの理由が決まった名前だけ{"" if not odd else " 知らない名前 " + str(odd)}'))
    m = _overlap_max(t); r.append(('○' if m <= maxpos else '×', f'同時に持つ玉 最大{m}(上限{maxpos})'))
    tp = t[t.why == '利確']; lo = int((tp.pips < -1e-6).sum())   # 利確はスプレッド込みでも負けない(11-07 売りのミスを見逃したので許しを0に)
    r.append(('○' if lo == 0 else '×', f'利確で負けた玉が無い(負け {lo})'))
    be = t[t.why == '建値']; lo = int((be.pips < -P - 1.0).sum())
    r.append(('○' if lo == 0 else '△', f'建値で大きく負けた玉(窓開けなら作りどおり) {lo}'))
    # 前から続いている合図を、いま出た合図と読む型(11-06 引け先取りのミス):入った次の足で合図で降りる玉が多すぎないか
    one = pd.Timedelta(bar)
    q = t[(t.why == '芯の降り') & ((ext - ent) <= one)]; share = len(q) / len(t)
    r.append(('○' if share < 0.05 else ('△' if share < 0.10 else '×'), f'入った次の足で合図で降りた玉 {len(q)}({share:.0%})  多ければ「前から続く合図」を読んでいないか見る'))
    dup = int(ent.duplicated().sum()); r.append(('○' if dup <= 0 else '△', f'同じ時刻に2玉以上入った {dup}(二重入りでないか)'))
    return r


def bugbug(make, raw, clock, maxpos=5, spr=0.003, cuts=None, bar='1h', both=True):
    """全部の型を通す。返り値 (全部○か, 行のリスト)"""
    L = []; ok = True
    def put(mark, s):
        nonlocal ok
        if mark == '×': ok = False
        L.append(f'{mark} {s}')
    mk = Market(raw, clock); dirs = (1, -1) if both else (1,)
    T = {d: make(mk, d) for d in dirs}
    for d in dirs:
        L.append(f'--- {"買い" if d > 0 else "売り"} {len(T[d])}玉 {T[d].pips.sum():+.1f}p ---')
        for mark, s in tama_check(T[d], maxpos, spr, d, bar): put(mark, s)
    # 二度回して同じ(しまい場所の取り違え)
    for d in dirs:
        u = make(mk, d); g = len(u) == len(T[d]) and np.allclose(u.pips.values, T[d].pips.values)
        put('○' if g else '×', f'同じ台で二度回して同じ({"買い" if d > 0 else "売り"})')
    # 順番(買いと売りの数えが混ざる)
    if both:
        m2 = Market(raw, clock); make(m2, 1); s2 = make(m2, -1)
        g = len(s2) == len(T[-1]) and np.allclose(s2.pips.values, T[-1].pips.values)
        put('○' if g else '×', '買いを先に回しても売りが同じ')
        g, msg = kagami(make, raw, clock); put('○' if g else '×', f'鏡(上下ひっくり返した買い = 元の売り):{msg}')
    # 先読み
    if cuts is None:
        ix = raw.index; cuts = [ix[int(len(ix) * f)].strftime('%Y-%m-%d') for f in (0.3, 0.55, 0.8)]
    res, _ = bousou(lambda r: make(Market(r, clock), 1), raw, cuts)
    put('○' if all(s for _, _, s in res) else '×', '先読みなし:' + ' '.join(f"{c} {n}玉 {'同じ' if s else '違う'}" for c, n, s in res))
    # 歩いて見る玉(ローソクで照らす候補)
    t = T[1]
    if len(t):
        w = t.sort_values('pips').iloc[0]; L.append(f'△ ローソクで見る:一番の負け {w.ent} → {w.ext} {w.pips:+.1f}p {w.why}')
        h = (pd.to_datetime(t.ext) - pd.to_datetime(t.ent)); s = t.loc[h.idxmin()]
        L.append(f'△ ローソクで見る:一番短い玉 {s.ent} → {s.ext} {s.pips:+.1f}p {s.why}')
    nb = sum(1 for x in L if x.startswith('×'))
    L.append(f'バグバグ修正機:{"全部○" if ok else f"×が{nb}つ → 成績を見る前に直す"}')
    return ok, L


if __name__ == '__main__':
    import sys
    from nyu import load_cached, simulate
    from tai_parts import run_tai, run_doten
    import tai_parts as tp_
    raw = load_cached(sys.argv[1]).loc['2016-03-01':'2020-12-31']
    KW = dict(maxpos=5, n8=False, reenter=True, tp=('4h', 3.5), ts=550, avoid_in=(0,), avoid_out=(0,), kai_k9=3, big21_up=True)
    for nm, f in [('決まった形2', lambda mk, d: run_tai(mk, '1D', '4h', '1h', d, ('1D', '219'), **KW)[0]),
                  ('利確の後921待ちドテン', lambda mk, d: run_doten(mk, d, **KW)[0])]:
        print(f'===== {nm} =====')
        ok, L = bugbug(f, raw, 'server', 5, 0.003); print('\n'.join(L))
    # わざと壊した形:ドテンの降りを「新しく出た219」でなく、入った時から続いている並びで読む(11-06 の引け先取りと同じ型のミス)を、修正機が見つけるか
    orig = tp_.simulate
    def broken(base, d, E, X, K, *a, **k):
        if len(a) > 3 and a[3] == 1:                                   # ドテンの玉(1玉)の時だけ壊す
            up = (base.e9 > base.e21).values; X = up if d > 0 else ~up   # 入った時から続いている並び(921の後の9>21)を降りの合図と読む
        return orig(base, d, E, X, K, *a, **k)
    tp_.simulate = broken
    print('===== わざと壊したドテン(見つけられるか) =====')
    ok, L = bugbug(lambda mk, d: run_doten(mk, d, **KW)[0], raw, 'server', 1, 0.003); print('\n'.join(L))
    tp_.simulate = orig
