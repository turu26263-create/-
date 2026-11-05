from sim5 import *
m5,h1=load(); m=base(m5,h1)
def rg(tag,sq,side,k,start=None,end=None,spr=0.3):
    mm=m.loc[start:end] if (start or end) else m
    rng=(mm.sq4.values<sq)&mm.newh.values; buy=rng&(mm.c1.values<mm.dn2.values); sell=rng&(mm.c1.values>mm.up2.values)
    if side=='200': ab=mm.c1.values>mm.e200_4.values; buy&=ab; sell&=~ab
    sig=np.where(buy,1,np.where(sell,-1,0)).astype(np.float64); yr=(mm.index.year-2015).values.astype(np.int64)
    eq,g,l,yp,bs,n=run_rg(mm.o.values,mm.h.values,mm.l.values,mm.c.values,sig,mm.mid1.values,(k*mm.atr1).values,spr*PIP,yr)
    return round(eq[-1]),round(g/l,2) if l else 99,n
print('=== レンジ打ちだけ(トレンド側なし)')
for side in ('both','200'):
    for sq in (0.7,1.0,9.9):
        for k in (1,2,3):
            a=rg('',sq,side,k,'2022','2024'); b=rg('',sq,side,k,'2015','2021'); c=rg('',sq,side,k,'2025'); f=rg('',sq,side,k)
            print(f"{side:4s} しぼみ<{sq:<4} 網1hATR×{k}  決{a[0]:+6d} PF{a[1]} | 確15-21 {b[0]:+6d} PF{b[1]} | 確25 {c[0]:+5d} | 全 {f[0]:+6d} PF{f[1]} 回{f[2]}")
