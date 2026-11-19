# ええやつ帳(11-06 たくちん「ええやつだけぶん回しエンジンに書いて」)。ニューエンジンで良かった形だけを並べて、いつでも同じ数字が出るようにしておく
# 使い方: python3 eeyatsu.py <HistData 1分足の置き場> <MT4 1時間足の置き場>
import sys, warnings; warnings.filterwarnings('ignore')
from nyu import *; from tai_parts import *
H, M = sys.argv[1], sys.argv[2]
est = Market(load_csv_dir(H), 'est'); srv = Market(load_csv_dir(M), 'server')
KUJIRA = {'日足の大山': ('2025-09-19', '2026-01-27'), '450hの大山': ('2021-03-26', '2025-04-15 18:00')}
EEYATSU = [
 # 名前, 何をする, 照らし(期待の数字)
 ('クジラ5発 日足の大山', lambda: hitoyama(run_tai(srv,'1D','4h','1h',1,('1D','219'),maxpos=5,n8=True,reenter=True)[0],*KUJIRA['日足の大山']), '5玉 +1,936.7p'),
 ('クジラ5発 450hの大山', lambda: hitoyama(run_tai(srv,'450h','1D','1h',1,('450h','219'),maxpos=5,n8=True,reenter=True)[0],*KUJIRA['450hの大山']), '5玉 +16,604.3p'),
 ('上の小魚 日足の大山(4h21の上・最大5発)', lambda: hitoyama(kozakana_ue(srv,1,5)[0],*KUJIRA['日足の大山']), '30玉 +217.4p'),
 ('上の小魚 450hの大山(4h21の上・最大5発)', lambda: hitoyama(kozakana_ue(srv,1,5)[0],*KUJIRA['450hの大山']), '534玉 +5,400.2p'),
 ('逆目99 4h 日足の大山(4hの9割れで売り・9に戻ったら降り)【黄:28戦だけ】', lambda: hitoyama(gyakume_99(srv,'4h',-1)[0],*KUJIRA['日足の大山']), '28戦 +702.1p'),
 ('鯛 日足段 買い 玉1 2σ 縄8 spr1.0', lambda: run_tai(est,'1D','4h','1h',1,('4h','9割れ'),n8=True,spr=0.01)[0], '全 +2,855.0p'),
 ('クジラmix 日足段 買い 5発 芯日足9割れ 足し4h9割れ 縄8 spr1.0', lambda: run_tai(est,'1D','4h','1h',1,('1D','9割れ'),('4h','9割れ'),5,n8=True,spr=0.01,reenter=True)[0], '全 +6,051.9p'),
 ('鯛 4h段 売り 玉1 2σ spr1.0', lambda: run_tai(est,'4h','1h','5min',-1,('1h','9割れ'),spr=0.01)[0], '全 +1,957.4p'),
]
for nm, fn, kitai in EEYATSU:
    t = fn(); s = stat(t); print(f"{nm}: {s['n']}玉 {s['sum']:+.1f}p PF{s['pf']} 勝{s['win']}  | 期待 {kitai}")
