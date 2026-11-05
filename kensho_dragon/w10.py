from sim6 import *
m5,h1=load(); m=build(m5,h1)
print('=== 9割れ利確 + 9の向こう側では入らない(川に戻るまで待つ)')
row6('B2 + 9割れ利確・待つ',m,EXIT=('9',),WAIT9=True)
row6('B2 + 9割れ・待つ + 川戻り',m,EXIT=('9','kawa'),WAIT9=True)
row6('B2 + 待つだけ(利確なし)',m,WAIT9=True)
row6('魚を追う + 9割れ・待つ',m,DIRMODE='921',EXIT=('9',),WAIT9=True)
row6('魚を追う + 待つだけ',m,DIRMODE='921',WAIT9=True)
row6('魚を追う + 川戻り + 待つ',m,DIRMODE='921',EXIT=('kawa',),WAIT9=True)
