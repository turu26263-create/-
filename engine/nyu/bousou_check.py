# 暴走チェック(ニューエンジン):先読み・玉の上限・降りていない玉
import sys, warnings; warnings.filterwarnings('ignore')
from nyu import *; from tai_parts import *
raw=load_csv_dir(sys.argv[1])
cases={'4時間版の鯛 買い':dict(big='4h',mid='1h',small='5min',d=1,core_exit=('1h','9割れ'),n8=True),
       '日足クジラ20発 買い':dict(big='1D',mid='4h',small='1h',d=1,core_exit=('1D','9割れ'),maxpos=20,n8=True,reenter=True),
       '日足 mix 20発 買い':dict(big='1D',mid='4h',small='1h',d=1,core_exit=('1D','9割れ'),add_exit=('4h','9割れ'),maxpos=20,n8=True,reenter=True)}
for nm,kw in cases.items():
    mp=kw.get('maxpos',1)
    res,full=bousou(lambda r: run_tai(Market(r,'est'),**kw)[0], raw, ['2017-06-01','2020-03-15','2023-01-10'])
    print(nm,'| 先読み:',' '.join(f"{c} {n}戦 {'同じ' if s else '違う!!'}" for c,n,s in res),'| 同時最大',full.attrs['maxheld'],'/上限',mp,'| データの終わりで持ったまま',full.attrs['held_at_end'])
