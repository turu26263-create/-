from sim3 import *
m5,h1=load()
print('=== 照らし: 部品なし=前回の4h土台と同じになるか'); r=sim3(prep3(m5,h1)); print(r['pips'],r['PF'],r['DD'],r['ikusa'],' (前回 +18710 PF1.19 DD14963 戦878)')
print('=== 合体: 主=4時間 5>9>21>200 に、日足・1時間の向きを足す(数字は動かさない)')
for D1 in ('none','ord','po'):
    for H1 in ('none','ord'):
        row(f'日足={D1:4s} 1時間={H1:4s} 出=主', prep3(m5,h1,D1=D1,H1=H1))
print('=== 出口も全部そろいで見る(崩れたら降りる)')
for D1,H1 in (('ord','none'),('none','ord'),('ord','ord')):
    row(f'日足={D1:4s} 1時間={H1:4s} 出=全部', prep3(m5,h1,D1=D1,H1=H1,EXIT='all'))
print('=== 主の足を替える(ほかの足の向きを合わせる)')
row('主=日足po 4h=ord 1h=ord', prep3(m5,h1,MAIN=('1D','po'),H4='ord',H1='ord'))
row('主=1時間po 日足=ord 4h=ord', prep3(m5,h1,MAIN=('1h','po'),D1='ord',H4='ord'))
