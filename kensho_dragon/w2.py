from sim4 import *
m5,h1=load()
for tf in ('1h','4h'):
    print(f'=== {tf} 200ドテン + 無限リーチ(網なし・ドテンだけで降りる)')
    m=prep4(m5,h1,tf)
    for mx in (5,10,20): row(f'{tf} 足し20p 最大{mx}',m,MAXPOS=mx,ADDSTEP=20)
    for ad in (10,40,80): row(f'{tf} 足し{ad}p 最大20',m,MAXPOS=20,ADDSTEP=ad)
    print(f'--- {tf} 入り・足しを 5分 5>9>21 がそろった時だけ')
    row(f'{tf} 5分合図 足し20 最大20',prep4(m5,h1,tf,LOC='m5'),MAXPOS=20,ADDSTEP=20)
    print(f'--- {tf} 網を足す(網に掛かったら休み、200の向きに5分がそろえばまた入る)')
    for k in (2,3,5): row(f'{tf} 5分合図 網4hATR×{k}',prep4(m5,h1,tf,LOC='m5',NET=('4h',k)),MAXPOS=20,ADDSTEP=20)
