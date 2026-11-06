# 逆目は99 と 上の小魚を、クジラの間だけで見る(MT4 1時間足)
import sys, warnings; warnings.filterwarnings('ignore')
from nyu import *; from tai_parts import *
mk=Market(load_csv_dir(sys.argv[1]),'server')
KUJIRA={'日足のクジラ':('2025-09-19','2026-01-27',1936.7),'450hのクジラ':('2021-03-26','2025-04-15 18:00',16604.3)}
up,_=kozakana_ue(mk,1,5)
for nm,(a,b,kj) in KUJIRA.items():
    print(f'\n=== {nm} {a}〜{b}(クジラ5発 {kj:+.1f}p)===')
    u=hitoyama(up,a,b); print(f"上の小魚(4h21の上・買い・最大5発):{stat(u)}")
    for tf in ('1h','4h'):
        g,_=gyakume_99(mk,tf,-1); g=hitoyama(g,a,b); s=stat(g)
        print(f"逆目 99({tf}の9割れで売り・9に戻ったら降り):{s}  平均{(s['sum']/max(s['n'],1)):+.1f}p")
        g.to_csv(f"engine/kekka_tai/hitoyama/逆目99_{nm}_{tf}.csv",index=False)
