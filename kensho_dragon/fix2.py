import fix1
from fix1 import *
b4a=to_m5(a4,'4h',idx)/PIP
print('=== 直し4: 足しの間を 4hATR×k にする(荒れた時は間を広く)')
for k in (0.3,0.5,0.75,1.0):
    B[f'add{k}']=(k*b4a).values; row(f'足し=4hATR×{k}',B,ADD=f'add{k}')
print('参考 4hATR(pips) 中央値',round(float(np.nanmedian(b4a))),' 2017年1月の中央値',round(float(np.nanmedian(b4a.loc['2017-01']))))
