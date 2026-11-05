from sim4 import *
m5,h1=load()
for tf in ('1h','4h'):
    print(f'=== {tf} 200ドテン + 5分合図 + 網(4hATR) の倍率')
    for k in (3,4,5,6,8): row(f'{tf} 網×{k}',prep4(m5,h1,tf,LOC='m5',NET=('4h',k)),MAXPOS=20,ADDSTEP=20)
m=prep4(m5,h1,'1h',LOC='m5',NET=('4h',4))
print('=== 1h 網×4 で 足し・最大')
for ad in (15,20,30): row(f'1h 網×4 足し{ad}',m,MAXPOS=20,ADDSTEP=ad)
for mx in (14,28): row(f'1h 網×4 最大{mx}',m,MAXPOS=mx,ADDSTEP=20)
print('=== 1h 200の離れ(網×4)')
for bf in (10,20): row(f'1h 網×4 離れ{bf}',prep4(m5,h1,'1h',BUF=bf,LOC='m5',NET=('4h',4)),MAXPOS=20)
print('=== スプレッド1.0'); row('1h 網×4 spr1.0',m,1.0,MAXPOS=20)
