# 回帰の照らし:ニューエンジンで、これまでの結果が同じ数字で出るか(11-06)
import sys, time, warnings; warnings.filterwarnings('ignore')
from nyu import *; from tai_parts import *
H, M = sys.argv[1], sys.argv[2]   # HistData 1分足の置き場 / MT4 1時間足の置き場
t0=time.time(); est=Market(load_csv_dir(H),'est'); print('HistData 読み込み',round(time.time()-t0,1),'秒')
t0=time.time(); t,_=run_tai(est,'4h','1h','5min',1,('1h','9割れ'),n8=True); print('① 4時間版の鯛 買い縄8 :',stat(t),' 期待 1969戦 +3910.8  ',round(time.time()-t0,1),'秒')
t0=time.time(); t,_=run_tai(est,'4h','1h','5min',-1,('1h','9割れ'),n8=False); print('② 4時間版の鯛 売り   :',stat(t),' 期待 1820戦 +683.4  ',round(time.time()-t0,1),'秒')
t0=time.time(); t,_=run_tai(est,'1D','4h','1h',1,('4h','9割れ'),n8=True); print('③ 日足版の鯛 買い縄8 :',stat(t),' 期待 265戦 +3040.5  ',round(time.time()-t0,1),'秒')
t0=time.time(); t,_=run_tai(est,'1D','4h','1h',1,('1D','9割れ'),maxpos=20,n8=True,reenter=True); print('④ 日足クジラ20発    :',stat(t),' 期待 284玉 +7942.2 ',round(time.time()-t0,1),'秒')
srv=Market(load_csv_dir(M),'server')
t,_=run_tai(srv,'1D','4h','1h',1,('1D','219'),maxpos=5,n8=True,reenter=True); y=hitoyama(t,'2025-09-19','2026-01-27')
print('⑤ 大山ひと山 5発 219 :',stat(y),' 期待 5玉 +1936.7')
