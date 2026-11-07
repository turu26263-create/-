# ニューぶん回しエンジンの部品:鯛の刺身とクジラ(決まりは engine_tai2・engine_kujira と同じ。数字は【置き換え】)
import numpy as np, pandas as pd
from nyu import Market, simulate

def tai_entry(mk, big, mid, small, d, sao=2.0, n8=False, kawa_chi=True, lag21=True, kai_k9=0, big21_up=False):
    key = ('tai_entry', big, mid, small, d, sao, n8, kawa_chi, kai_k9, big21_up)            # 合図のしまい場所(ぶん回しで同じ合図を作り直さない)
    if key in mk._f: return mk._f[key]
    E = _tai_entry(mk, big, mid, small, d, sao, n8, kawa_chi, kai_k9)
    if big21_up:   # 大きい足の21が向きの方へ傾いている時だけ(下向きの21で買わない)
        a = mk.on(small, big, ['ang']).ang.values; E = E & ((a > 0) if d > 0 else (a < 0))
    mk._f[key] = E; return E

def _tai_entry(mk, big, mid, small, d, sao=2.0, n8=False, kawa_chi=True, kai_k9=0):
    """縄1 big の9上 / 縄2 mid の21上 / 縄3 small の921 / 縄3改 許しが出た時にもう921済み / 縄4 川の外+遅行21本前 / 縄4改 big の21上 / 縄5 竿先で入らない / 縄8 big の角度55度超で入らない"""
    S = mk.feat(small); x = S
    M = mk.on(mid, big, ['c', 'e9']).join(mk.feat(mid)[['c', 'e21', 'k']].rename(columns={'c': 'cm'}))
    M['pb'] = (M.c > M.e9) & (M.cm > M.e21); M['ps'] = (M.c < M.e9) & (M.cm < M.e21)
    a = M[['k', 'pb', 'ps']].sort_values('k')
    perm = pd.merge_asof(pd.DataFrame({'kb': S.k.values}), a, left_on='kb', right_on='k', direction='backward')
    perm.index = S.index
    q = mk.on(small, big, ['c', 'e21', 'ang'])
    up = x.e9 > x.e21; up1 = up.shift(1, fill_value=False)
    if d > 0:
        p = perm.pb.fillna(False).astype(bool); cross = up & ~up1; side = up
        kawa = x.c > x.md + x.sd; chi = x.c > x.h21; qq = q.c > q.e21; ns = x.c <= x.md + sao * x.sd; ang = q.ang
    else:
        p = perm.ps.fillna(False).astype(bool); cross = ~up & up1; side = ~up
        kawa = x.c < x.md - x.sd; chi = x.c < x.l21; qq = q.c < q.e21; ns = x.c >= x.md - sao * x.sd; ang = -q.ang
    e921 = cross & p; kai = p & ~p.shift(1, fill_value=False) & side & ~cross
    if kai_k9:   # 許しが出た瞬間の入りは、大きい足の終値が9の向こうに kai_k9 本続いてから(たくちん「9のってからロウソク3本目まで竿先」)
        B = mk.feat(big); kc = 'k9b' if d > 0 else 'k9s'                  # 買いと売りで数え方を分ける(11-06 直したミス:同じ列名で買いの数えが売りに残っていた)
        if kc not in B.columns:
            s9 = (B.c > B.e9) if d > 0 else (B.c < B.e9); mk._f[big] = B.assign(**{kc: s9.groupby((~s9).cumsum()).cumsum()})
        kk = mk.on(small, big, [kc])[kc].fillna(0).values; kai = kai & (kk >= kai_k9)
        p_ok = p.copy()
        # 許しが出た瞬間を4本目まで待った時は、4本目になった最初の足で入る(その時もまだ許しの中・9>21)
        first = pd.Series(kk >= kai_k9, index=x.index) & ~pd.Series(kk >= kai_k9, index=x.index).shift(1, fill_value=False)
        kai = kai | (first & p_ok & side & ~cross & (kk == kai_k9))
    filt = (kawa & chi) if kawa_chi else True
    ent = ((e921 & filt) | (kai & qq)) & ns
    if n8: ent = ent & ~(ang > 55)
    return ent.fillna(False).values

def exit_ware(mk, small, tf, d):
    """tf の9割れ(実体の真ん中と終値が9の向こう)。small の足に貼る"""
    c = 'ware_b' if d > 0 else 'ware_s'; y = mk.on(small, tf, [c])
    return y[c].fillna(False).astype(bool).values, y['k_' + tf].values

def exit_219(mk, small, tf, d):
    """tf の219(9が21の下。売りは921)"""
    y = mk.on(small, tf, ['up921'])
    v = y.up921.fillna(True if d > 0 else False).astype(bool)
    return (~v if d > 0 else v).values, y['k_' + tf].values

def exit_close9(mk, small, tf, d):
    """tf の終値が9の向こう"""
    F = mk.feat(tf)
    if 'cb' not in F.columns: mk._f[tf] = F.assign(cb=F.c < F.e9, cs=F.c > F.e9)
    c = 'cb' if d > 0 else 'cs'; y = mk.on(small, tf, [c])
    return y[c].fillna(False).astype(bool).values, y['k_' + tf].values

EXITS = {'9割れ': exit_ware, '219': exit_219, '終値9': exit_close9}

# ---- 網(上げるだけ)と利確の高さ(入る足に貼る。どれも閉じた足の値)
def sl_prevday(mk, small, d):
    """前の日の安値(売りは高値)"""
    y = mk.on(small, '1D', ['l', 'h']); return (y.l if d > 0 else y.h).values

def sl_line(mk, small, tf, col='e21', buf=0.05, d=1):
    """tf の線(e9/e21/e200/md)の buf 下(売りは上)"""
    y = mk.on(small, tf, [col]); return (y[col] - buf * d).values

def tp_sigma(mk, small, tf, k=3.5, d=1):
    """tf の帯の ±kσ"""
    y = mk.on(small, tf, ['md', 'sd']); return (y.md + k * y.sd * d).values

def make_sl(mk, small, d, sl):
    if sl is None: return None
    if sl == 'prevday': return _mae1(sl_prevday(mk, small, d))
    tf, col = sl[0], sl[1]; buf = sl[2] if len(sl) > 2 else 0.05     # 例 ('4h','e21') / ('4h','e21',0.20)
    return _mae1(sl_line(mk, small, tf, col, buf, d))

def _mae1(v):
    """足の中で使う線(利確・網)は、その足が始まる前に分かっている値=1本前の足が閉じた時の値を使う(11-07 先読みを見つけて直した:
    いま動いている1時間足が閉じる時に閉じる4時間足の線を、その1時間足の中で使っていた)"""
    v = np.asarray(v, dtype=float); return np.r_[np.nan, v[:-1]]

def make_tp(mk, small, d, tp):
    if tp is None: return None
    tf, k = tp; return _mae1(tp_sigma(mk, small, tf, k, d))

YASUMI = [((12, 20), (12, 31)), ((1, 1), (1, 5)), ((4, 29), (5, 6))]   # 11-07 たくちん「サンタの休み、寝正月、イカの産卵時期ゴールデンウィーク」【置き換え】月日(はじめ, おわり)

def yasumi_mask(idx, ys=None):
    """i の合図が約定する足(i+1)の日付が休みの間なら True。休みの間は新しく入らない(持っている玉はそのまま)"""
    nx = pd.DatetimeIndex(np.r_[idx.values[1:], idx.values[-1:]]); md = nx.month * 100 + nx.day; m = np.zeros(len(idx), bool)
    for (a1, a2), (b1, b2) in (ys or YASUMI): m |= (md >= a1 * 100 + a2) & (md <= b1 * 100 + b2)
    return m

def run_tai(mk, big, mid, small, d, core_exit=('1h', '9割れ'), add_exit=None, maxpos=1, sao=2.0, n8=False, spr=0.003, reenter=False, kawa_chi=True,
            sl=None, tp=None, lock=0.0, lockcore=True, ts=0.0, ts_start=0.0, fine=False, avoid_in=(), avoid_out=(), kai_k9=0, big21_up=False, yasumi=False):
    """鯛・クジラを1回まわす。sl=None/'prevday'/(足,線) tp=None/(足,σ) lock=しあわせセットの pips(0=なし)"""
    E = tai_entry(mk, big, mid, small, d, sao, n8, kawa_chi, kai_k9=kai_k9, big21_up=big21_up)
    XC, KC = EXITS[core_exit[1]](mk, small, core_exit[0], d)
    if add_exit: XA, KA = EXITS[add_exit[1]](mk, small, add_exit[0], d)
    else: XA, KA = XC, KC
    base = mk.feat(small)
    if yasumi: E = np.asarray(E, bool) & ~yasumi_mask(base.index, yasumi if isinstance(yasumi, list) else None)
    if avoid_in or avoid_out:                                   # 0時をずらす(11-06):約定の足の時刻が avoid にある時は、次の足まで待つ
        fh = np.r_[base.index.hour.values[1:], -1]               # i の合図が約定する足(i+1)の時刻
        if avoid_in:
            E = np.asarray(E, bool).copy(); bad = np.isin(fh, avoid_in)
            for i in np.where(E & bad)[0]:
                E[i] = False; k = i + 1
                while k < len(E) - 1 and np.isin(fh[k], avoid_in): k += 1
                E[k] = True
        if avoid_out:
            bad = np.isin(fh, avoid_out); XC = np.asarray(XC, bool) & ~bad; XA = np.asarray(XA, bool) & ~bad   # 降りの合図は続く(219 など)ので、次の足で降りる
    return simulate(base, d, E, XC, KC, XA, KA, make_sl(mk, small, d, sl), maxpos, spr, reenter, make_tp(mk, small, d, tp), lock, lockcore, ts, ts_start, mk.hl_order(small) if fine else None), base

# ---- 小魚(11-06)
def kozakana_ue(mk, d=1, maxpos=5, spr=0.003, lock=0.0):
    """上の小魚(クジラと同じ向き):4h終値が21の向き側の間に、1hの終値が4h21をまたいだ足/1hの921で入る(最大 maxpos 発)。4h終値が21の逆側で全部降り【置き換え】"""
    S = mk.feat('1h'); q = mk.on('1h', '4h', ['c', 'e21'])
    side = (q.c > q.e21) if d > 0 else (q.c < q.e21); side = side.fillna(False)
    over = ((S.c > q.e21) & (S.c.shift() <= q.e21)) if d > 0 else ((S.c < q.e21) & (S.c.shift() >= q.e21))
    up = S.e9 > S.e21; x9 = (up & ~up.shift(1, fill_value=False)) if d > 0 else (~up & up.shift(1, fill_value=False))
    E = (side & (over | x9)).values; X = (~side).values; K = S.k.values   # 降りは 4h が閉じた時に確定するので、1h の閉じた時刻で見てよい
    return simulate(S, d, E, X, K, None, None, None, maxpos, spr, True, None, lock), S

def gyakume_99(mk, tf, d=-1, spr=0.003):
    """逆目は99(11-06 たくちん「逆目は99でいったら?」):tf の9割れが出た最初の足で入り、逆の9割れ(9に戻った)で降りる【置き換え】"""
    F = mk.feat(tf)
    w_in = F.ware_b if d < 0 else F.ware_s; w_out = F.ware_s if d < 0 else F.ware_b
    E = (w_in & ~w_in.shift(1, fill_value=False)).values
    return simulate(F, d, E, w_out.values, F.k.values, None, None, None, 1, spr, False), F

# ---- 引け先取り(11-06 たくちん「びけ先どりは?」)
def run_doten(mk, d, small='1h', ts=550.0, xtf=None, **kw):
    yas = kw.get('yasumi', False)
    """11-07 たくちん「うりの利確からのドテンで差し込み折り返しポイントやから、連鎖できたらなぁ」【置き換え】
    決まった形の -d 向きの玉が利確(4h ±3.5σ)したら構えて、small の足で向きの方の9と21の交わり(買いなら921)が出た次の足で、d 向きにドテン1玉。
    降り:small の足で 9 と 21 の並びが、入った後に向きと逆へ新しく交わった時(買いなら219が新しく出た時。前から続く並びでは降りない)+TS ts pips。
    連鎖:ドテンの玉を降りた後は、決まった形の入りがそのまま続く(この部品はドテンの玉だけを返す)"""
    main, base = run_tai(mk, '1D', '4h', small, -d, ('1D', '219'), **kw)
    idx = base.index; E = np.zeros(len(idx), bool)
    tp = main[main.why == '利確']
    if len(tp): E[np.searchsorted(idx.values, pd.to_datetime(tp.ext).values)] = True   # 利確した足(その足の中で届いた)で構える
    S = mk.feat(small); up = (S.e9 > S.e21).values; up1 = np.r_[up[0], up[:-1]]
    # 後出しじゃんけん:構えた後、small の足で向きの方へ9と21が新しく交わった足(買いなら921)が閉じたら、次の足でドテン(利確の足ですぐドテンは × だったので外した)
    cr = (~up1 & up) if d > 0 else (up1 & ~up); W = np.zeros(len(idx), bool); armed = False
    for i in range(len(idx)):
        if E[i]: armed = True
        if armed and cr[i]: W[i] = True; armed = False
    E = W & ~yasumi_mask(idx, yas if isinstance(yas, list) else None) if yas else W
    X = (up1 & ~up) if d > 0 else (~up1 & up)                                     # 新しく出た219(売りは921)
    K = S.k.values
    if xtf:   # 11-07 降りを xtf の足の新しく出た219(売りは921)にする(1hでは折り返しの胴体を取る前に降ろされた)
        F = mk.feat(xtf); u = F.e9 > F.e21; u1 = u.shift(1, fill_value=False); kc = 'x219' if d > 0 else 'x921'
        if kc not in F.columns: mk._f[xtf] = F.assign(x219=u1 & ~u, x921=~u1 & u)
        y = mk.on(small, xtf, [kc]); X = y[kc].fillna(False).astype(bool).values; K = y['k_' + xtf].values
    t = simulate(base, d, E, X, K, None, None, None, 1, kw.get('spr', 0.003), True, None, 0.0, True, ts, 0.0)
    return t, base
