import sys
from sim2 import *
m5,h1=load()
TTF=sys.argv[1]
def row(tag,m,spr=0.3,**kw):
    a=sim(m,spr,start='2022',end='2024',**kw); b=sim(m,spr,start='2015',end='2021',**kw); c=sim(m,spr,start='2025',**kw)
    print(f"{tag:24s} 調整 {a['pips']:+7d} PF{a['PF']:.2f} 戦{a['ikusa']:5d} DD{a['DD']:5d} | 確15-21 {b['pips']:+7d} PF{b['PF']:.2f} 戦{b['ikusa']:5d} DD{b['DD']:5d} | 確25 {c['pips']:+6d} PF{c['PF']:.2f} 戦{c['ikusa']:4d}",flush=True)
print('=== 大きい足',TTF,'(土台: 200=order 入り5分 CHK3 CHB22 ADD20 MAX14)')
print('--- CHK 細かく')
for k in (2.5,3,3.5): row(f'CHK={k}',prep2(m5,h1,TTF,CHK=k))
m=prep2(m5,h1,TTF)
print('--- 足しの間 ADDSTEP')
for a in (10,20,40,60,100): row(f'ADD={a}',m,ADDSTEP=a)
print('--- 最大発数 MAXPOS')
for p in (1,4,8,14,20): row(f'MAX={p}',m,MAXPOS=p)
print('--- シャンデリア本数 CHB(5分足)')
for b in (11,22,66,150): row(f'CHB={b}',prep2(m5,h1,TTF,CHB=b))
print('--- 打ち直しの間 COOL')
for c in (0,12,48,-1): row(f'COOL={c}',m,COOL=c)
