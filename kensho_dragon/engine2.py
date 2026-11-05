import numpy as np, numba as nb
PIP = 0.01
@nb.njit(cache=True)
def run2(O, H, L, C, LOC, TRD, ENT, CHL, CHS, spr, MAXPOS, ADDSTEP, COOL, YEAR):
    # COOL: 0=なし(v3) / >0=損切りで玉が0になったら N本休む / -1=5分の並びが一度崩れるまで待つ
    n = len(O)
    pd_ = np.zeros(64); pe = np.zeros(64); ps = np.zeros(64); np_ = 0
    eqc = 0.0; peak = 0.0; dd = 0.0
    gain = 0.0; loss = 0.0; ntr = 0; ncamp = 0; nwin_camp = 0; camp_p = 0.0
    nsl = 0; ndoten = 0; nkuzure = 0
    yp = np.zeros(20); bs = np.zeros(2)
    wait = 0; need_break = False
    for i in range(n):
        trend = int(TRD[i]); loc = int(LOC[i])
        if wait > 0: wait -= 1
        if need_break and loc != trend: need_break = False
        if np_ > 0:
            d = pd_[0]
            if trend == -d or trend == 0:
                for k in range(np_):
                    ex = O[i] if d > 0 else O[i] + spr
                    p = (ex - pe[k]) / PIP * d
                    eqc += p; camp_p += p; ntr += 1; yp[YEAR[i]] += p; bs[0 if d > 0 else 1] += p
                    if p > 0: gain += p
                    else: loss -= p
                np_ = 0
                if camp_p > 0: nwin_camp += 1
                camp_p = 0.0
                if trend == -d:
                    ndoten += 1
                    if loc == trend and int(ENT[i]) == trend:
                        px = O[i] + spr if trend > 0 else O[i]
                        sl = CHL[i] if trend > 0 else CHS[i]
                        if trend > 0 and sl > px: sl = px - 10 * PIP
                        if trend < 0 and sl < px: sl = px + 10 * PIP
                        pd_[0] = trend; pe[0] = px; ps[0] = sl; np_ = 1; ncamp += 1
                else:
                    nkuzure += 1
            else:
                bid = O[i]
                for k in range(np_):
                    sl = CHL[i] if d > 0 else CHS[i]
                    if d > 0 and sl > ps[k] + 0.001 and sl < bid: ps[k] = sl
                    if d < 0 and sl < ps[k] - 0.001 and sl > bid + spr: ps[k] = sl
                if np_ < MAXPOS and loc == d:
                    px = O[i] if d > 0 else O[i] + spr
                    if d * (px - pe[np_ - 1]) >= ADDSTEP * PIP:
                        px2 = O[i] + spr if d > 0 else O[i]
                        sl = CHL[i] if d > 0 else CHS[i]
                        if d > 0 and sl > px2: sl = px2 - 10 * PIP
                        if d < 0 and sl < px2: sl = px2 + 10 * PIP
                        pd_[np_] = d; pe[np_] = px2; ps[np_] = sl; np_ += 1
        elif trend != 0 and loc == trend and int(ENT[i]) == trend and wait == 0 and not need_break:
            px = O[i] + spr if trend > 0 else O[i]
            sl = CHL[i] if trend > 0 else CHS[i]
            if trend > 0 and sl > px: sl = px - 10 * PIP
            if trend < 0 and sl < px: sl = px + 10 * PIP
            pd_[0] = trend; pe[0] = px; ps[0] = sl; np_ = 1; ncamp += 1
        # 足の途中:損切り
        had = np_
        j = 0
        for k in range(np_):
            d = pd_[k]; e = pe[k]; sl = ps[k]
            hit = False
            if d > 0 and L[i] <= sl:
                ex = O[i] if O[i] <= sl else sl
                p = (ex - e) / PIP; hit = True
            elif d < 0 and H[i] + spr >= sl:
                ex = O[i] + spr if O[i] + spr >= sl else sl
                p = (e - ex) / PIP; hit = True
            if hit:
                eqc += p; camp_p += p; ntr += 1; nsl += 1; yp[YEAR[i]] += p; bs[0 if d > 0 else 1] += p
                if p > 0: gain += p
                else: loss -= p
            else:
                pd_[j] = d; pe[j] = e; ps[j] = sl; j += 1
        np_ = j
        if had > 0 and np_ == 0:
            if camp_p > 0: nwin_camp += 1
            camp_p = 0.0
            if COOL > 0: wait = COOL
            elif COOL == -1: need_break = True
        fl = 0.0
        for k in range(np_):
            fl += ((C[i] - pe[k]) if pd_[k] > 0 else (pe[k] - C[i] - spr)) / PIP
        eq = eqc + fl
        if eq > peak: peak = eq
        if peak - eq > dd: dd = peak - eq
    return eqc, gain, loss, ntr, ncamp, nwin_camp, dd, nsl, ndoten, nkuzure, yp, bs

