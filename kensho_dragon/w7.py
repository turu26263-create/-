from sim5 import *
m5,h1=load(); m=base(m5,h1)
print('=== 合体(数字は動かさない・入/切だけ)')
for sa in (False,True):
    for w in (1.0,0.5):
        for rg in (None,(0.7,'200',3)):
            f=row5(f"竿先{'○' if sa else '×'} 斥候{'○' if w<1 else '×'} レンジ{'○' if rg else '×'}",m,SAOSAKI=sa,W1=w,RANGE=rg)
f=go(m,SAOSAKI=True,W1=0.5); print('竿先+斥候 年ごと',f['year'])
f=go(m,SAOSAKI=True,W1=0.5,spr=1.0); print('竿先+斥候 spr1.0',f['pips'],f['PF'],f['DD'])
