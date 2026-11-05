import sys
from sim2 import *
m5,h1=load()
TTF=sys.argv[1]
def row(tag,m,spr=0.3,**kw):
    a=sim(m,spr,start='2022',end='2024',**kw); b=sim(m,spr,start='2015',end='2021',**kw); c=sim(m,spr,start='2025',**kw)
    print(f"{tag:24s} 調整 {a['pips']:+7d} PF{a['PF']:.2f} 戦{a['ikusa']:5d} DD{a['DD']:5d} | 確15-21 {b['pips']:+7d} PF{b['PF']:.2f} 戦{b['ikusa']:5d} DD{b['DD']:5d} | 確25 {c['pips']:+6d} PF{c['PF']:.2f} 戦{c['ikusa']:4d}",flush=True)
    return a,b,c
print('=== 大きい足',TTF)
print('--- 200の入れ方(ほか: 入り5分・網=大足ATR×3)')
for f in ('none','close','order'): row(f'200={f}',prep2(m5,h1,TTF,F200=f))
print('--- 入りの足')
for e in ('5min','1h'): row(f'入り={e}',prep2(m5,h1,TTF,ETF=e))
print('--- 網の倍率 CHK(大足ATR)')
for k in (0.5,1,1.5,2,3,4): row(f'CHK={k}',prep2(m5,h1,TTF,CHK=k))
