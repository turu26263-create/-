from sim import *
m5,h1=load()
def row(tag,m,**kw):
    a=sim(m,0.3,start='2022',end='2024',**kw); b=sim(m,0.3,start='2015',end='2021',**kw); c=sim(m,0.3,start='2025',**kw)
    print(f"{tag:18s} 調整22-24 {a['pips']:+7d} PF{a['PF']:.2f} 戦{a['ikusa']:6d} DD{a['DD']:5d} | 確15-21 {b['pips']:+7d} PF{b['PF']:.2f} DD{b['DD']:5d} | 確25 {c['pips']:+6d} PF{c['PF']:.2f}",flush=True)
base=prep(m5,h1)
print('--- 打ち直しの間 COOL(本) 5分足')
for c in (0,3,6,12,24,48,96,288,-1): row(f'COOL={c}',base,COOL=c)
print('--- シャンデリアの本数 CHB')
for b in (11,22,44,66,100,150): row(f'CHB={b}',prep(m5,h1,CHB=b))
print('--- ATRの倍率 CHK')
for k in (1.5,3,4.5,6,8,10): row(f'CHK={k}',prep(m5,h1,CHK=k))
print('--- 1時間足ATR 倍率')
for k in (0.5,1,1.5,2,3,4): row(f'H1ATR CHK={k}',prep(m5,h1,CHK=k,ATRTF='H1'))
