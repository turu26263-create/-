import fix1
from fix1 import *
m3=with_trend(side_n(3)); 
for c in ('f921','f200s'): m3[c]=B[c]
print('=== 合体(入/切だけ)')
row('3本続いたら',m3)
row('3本+200傾き',m3,XOK='f200s')
row('3本+4h 9>21',m3,XOK='f921')
m3['both']=np.where((m3.f921==m3.f200s),m3.f921,0); row('3本+200傾き+9>21',m3,XOK='both')
B['both']=np.where((B.f921==B.f200s),B.f921,0); row('200傾き+9>21',B,XOK='both')
