# ニューぶん回しエンジンの部品:鯛の刺身とクジラ(決まりは engine_tai2・engine_kujira と同じ。数字は【置き換え】)
import numpy as np, pandas as pd
from nyu import Market, simulate

def tai_entry(mk, big, mid, small, d, sao=2.0, n8=False, kawa_chi=True, lag21=True, kai_k9=0, big21_up=False, big_sao=0, k9_max=0, mid_sao=0):
    key = ('tai_entry', big, mid, small, d, sao, n8, kawa_chi, kai_k9, big21_up, big_sao, k9_max, mid_sao)            # 合図のしまい場所(ぶん回しで同じ合図を作り直さない)
    if key in mk._f: return mk._f[key]
    E = _tai_entry(mk, big, mid, small, d, sao, n8, kawa_chi, kai_k9)
    if big21_up:   # 大きい足の21が向きの方へ傾いている時だけ(下向きの21で買わない)
        a = mk.on(small, big, ['ang']).ang.values; E = E & ((a > 0) if d > 0 else (a < 0))
    px = mk.feat(small).c.values                                     # 合図の足の終値(この値段で次の足に入る)
    for tf, k in ((big, big_sao), (mid, mid_sao)):                   # 11-06 A:日足の竿先 / C:4時間の竿先(確定した足の ±kσ の外)では入らない
        if k:
            b = mk.on(small, tf, ['md', 'sd']); hi = (b.md + k * b.sd).values; lo = (b.md - k * b.sd).values
            E = E & ((px <= hi) if d > 0 else (px >= lo)) & ~np.isnan(hi)
    if k9_max:                                                       # 11-06 B:大きい足の終値が9の向こうに k9_max 本より多く続いたら入らない(上げの後半)
        B = mk.feat(big); kc = 'k9b' if d > 0 else 'k9s'
        if kc not in B.columns:
            s9 = (B.c > B.e9) if d > 0 else (B.c < B.e9); mk._f[big] = B.assign(**{kc: s9.groupby((~s9).cumsum()).cumsum()})
        kk = mk.on(small, big, [kc])[kc].fillna(0).values; E = E & (kk <= k9_max)
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
    if sl == 'prevday': return sl_prevday(mk, small, d)
    tf, col = sl[0], sl[1]; buf = sl[2] if len(sl) > 2 else 0.05     # 例 ('4h','e21') / ('4h','e21',0.20)
    return sl_line(mk, small, tf, col, buf, d)

def make_tp(mk, small, d, tp):
    if tp is None: return None
    tf, k = tp; return tp_sigma(mk, small, tf, k, d)

def run_tai(mk, big, mid, small, d, core_exit=('1h', '9割れ'), add_exit=None, maxpos=1, sao=2.0, n8=False, spr=0.003, reenter=False, kawa_chi=True,
            sl=None, tp=None, lock=0.0, lockcore=True, ts=0.0, ts_start=0.0, fine=False, avoid_in=(), avoid_out=(), kai_k9=0, big21_up=False, big_sao=0, k9_max=0, mid_sao=0):
    """鯛・クジラを1回まわす。sl=None/'prevday'/(足,線) tp=None/(足,σ) lock=しあわせセットの pips(0=なし)"""
    E = tai_entry(mk, big, mid, small, d, sao, n8, kawa_chi, kai_k9=kai_k9, big21_up=big21_up, big_sao=big_sao, k9_max=k9_max, mid_sao=mid_sao)
    XC, KC = EXITS[core_exit[1]](mk, small, core_exit[0], d)
    if add_exit: XA, KA = EXITS[add_exit[1]](mk, small, add_exit[0], d)
    else: XA, KA = XC, KC
    base = mk.feat(small)
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
def senbiki_daily(mk, small, h=1):
    """日足が閉じる h 時間前の small の足が閉じた時に、その時の値段を日足の終値とみなして、日足の 9・21・終値>9・9>21 を先取りする【置き換え】。
    ほかの足では、確定した日足の値を使う。返り値:small の足ごとの {c, e9, e21, up921, c_gt_e9}(先取りした足は先取りの値)"""
    S = mk.feat(small); D = mk.feat('1D'); cols = ['c', 'e9', 'e21']
    conf = mk.on(small, '1D', cols)                                           # 確定した日足(閉じた時刻から)
    k9, k21 = 2 / 10, 2 / 22
    # small の足が閉じた時刻が、いま作っている日足の終わりの h 時間前か
    dstart = pd.Series(D.index, index=D.index); dend = D.k
    cur = pd.merge_asof(pd.DataFrame({'kb': S.k.values}), pd.DataFrame({'ds': D.index, 'de': dend.values}), left_on='kb', right_on='ds', direction='backward')
    pre = (cur.de.values - S.k.values) == np.timedelta64(int(h * 3600), 's')
    out = pd.DataFrame({'c': conf.c.values, 'e9': conf.e9.values, 'e21': conf.e21.values}, index=S.index)
    # 先取りの足:前の確定日足の EMA に、いまの値段を1本足したもの
    ce9 = conf.e9.values; ce21 = conf.e21.values; px = S.c.values
    out.loc[pre, 'c'] = px[pre]
    out.loc[pre, 'e9'] = ce9[pre] * (1 - k9) + px[pre] * k9
    out.loc[pre, 'e21'] = ce21[pre] * (1 - k21) + px[pre] * k21
    out['up921'] = out.e9 > out.e21; out['c_gt_e9'] = out.c > out.e9; out['pre'] = pre
    # 日足の形がわかった時刻:先取りの足はその足が閉じた時、ほかは確定した日足が閉じた時(11-06 前から219のままを「いま出た合図」と読んで、入った次の足で降りていたミスを直した)
    out['k'] = np.where(pre, S.k.values, conf['k_1D'].values)
    return out

def run_senbiki(mk, small='1h', d=1, h=1, **kw):
    """決まった形の 日足の219(売りは921)で降りる所と、許し(日足9上)を、引け h 時間前に先取りする。ほかは run_tai と同じ"""
    sd = senbiki_daily(mk, small, h)
    t0, base = None, mk.feat(small)
    # 降り:先取りの足で 219(売りは921)が見えたら、次の足で降りる。その合図の時刻はその足が閉じた時刻
    X = (~sd.up921 if d > 0 else sd.up921).fillna(False).values; K = sd.k.values
    # 入り:日足の許しを先取りの値で作り直す(4h・1h の決まりはそのまま)
    E = tai_entry(mk, '1D', '4h', small, d, kw.get('sao', 2.0), kw.get('n8', False), kw.get('kawa_chi', True), kai_k9=kw.get('kai_k9', 0), big21_up=kw.get('big21_up', False), big_sao=kw.get('big_sao', 0), k9_max=kw.get('k9_max', 0), mid_sao=kw.get('mid_sao', 0))
    okd = (sd.c_gt_e9 if d > 0 else ~sd.c_gt_e9).fillna(False).values
    E = np.asarray(E, bool) & (okd | ~sd.pre.values)                          # 先取りの足では、先取りの日足でも許しが出ている時だけ
    if kw.get('avoid_in') or kw.get('avoid_out'):
        fh = np.r_[base.index.hour.values[1:], -1]
        if kw.get('avoid_in'):
            E = E.copy(); bad = np.isin(fh, kw['avoid_in'])
            for i in np.where(E & bad)[0]:
                E[i] = False; k = i + 1
                while k < len(E) - 1 and np.isin(fh[k], kw['avoid_in']): k += 1
                E[k] = True
        if kw.get('avoid_out'): X = X & ~np.isin(fh, kw['avoid_out'])
    t = simulate(base, d, E, X, K, None, None, make_sl(mk, small, d, kw.get('sl')), kw.get('maxpos', 5), kw.get('spr', 0.003), True,
                 make_tp(mk, small, d, kw.get('tp')), kw.get('lock', 0.0), True, kw.get('ts', 0.0), 0.0)
    return t, base
