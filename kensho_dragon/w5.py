from sim5 import *
m5,h1=load(); m=base(m5,h1)
print('=== 照らし: わざなし = B(+39,223 PF1.21 DD15,872 戦1277) になるか'); row5('B(わざなし)',m)
print('=== わざを1つずつ')
row5('竿先注意(1h+2σの外で入らない)',m,SAOSAKI=True)
for k in (12,36): row5(f'押し目(直近{k}本で1h21に触れた)',m,OSHIME=k)
row5('斥候(1発目は半分)',m,W1=0.5)
print('=== レンジ打ちだけ足す(4h帯幅 しぼみ倍率 / 向き / 網=1hATR×k)')
for sq in (0.7,0.85,1.0):
    for side in ('both','200'):
        row5(f'レンジ しぼみ<{sq} {side} 網1.5',m,RANGE=(sq,side,1.5))
