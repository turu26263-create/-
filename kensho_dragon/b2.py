import fix1
from fix1 import *
from logger2 import run_log2
m3=with_trend(side_n(3)); m3['f921']=B['f921']
m3['ent']=np.where(m3.f921==m3.trend,m3.trend,0)
lg=run_log2(m3,MAXPOS=20); lg.to_pickle('b2log.pkl')
r=go(m3,XOK='f921'); print('B2 numba',r['pips'],' 素Python',round(lg.pips.sum()),' 戦',r['ikusa'],lg.camp.nunique()); print('年ごと',r['year'])
