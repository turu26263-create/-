# クジラの腹の中の小魚(11-06 たくちん「クジラの450 と日足 クジラの腹の中の小魚取れるとこだけ刺身にする、無限リーチ5発仕込んで」)
# クジラ=大山ひと山の5発(そのまま持つ。hitoyama_*.py の結果)。小魚=1段下の鯛を、クジラの間だけ・買いだけ・鯛の決まりを通った所だけ。小魚も無限リーチ最大5発(どの玉も小魚の9割れで降りる)
#  450hのクジラ(2021/03/26〜2025/04/15)の腹の中:日足版の鯛(日足9上・4h21上・1hで入る・4hの9割れで降りる)。データ MT4 1時間足
#  日足のクジラ(2025/09/19〜2026/01/27)の腹の中:4時間版の鯛(4h9上・1h21上・5分で入る・1hの9割れで降りる)。データ MT4 5分足(2025/10/09から。9/19〜10/08 は5分足が無いので小魚は見ていない)
import sys,warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,__file__.rsplit('/',1)[0])
import engine_tai_g as G
from engine_tai_g import *
from engine_kujira import attach2,run_k,ware
def bars_srv(m1,tf):
    f='1D' if tf=='1D' else tf; b=m1.resample(f).agg(AGG).dropna(); b['k']=b.index+pd.Timedelta(f); return b
G.bars=bars_srv
import engine_kujira as K; K.bars=bars_srv
def kozakana(m1,big,mid,small,ext,a,b):
    x=G.prep(m1,big,mid,small); x=attach2(x,ware(m1,ext,'a_'),'a_'); x['b_k']=x['a_k']; x['b_wb']=False; x['b_ws']=False
    t=run_k(x,1,G.signals(x,1,2.0,True),'tai',5,spr=0.003)
    return t[(t.ent>=a)&(t.ent<=b)]
out=[]
for nm,data,(big,mid,small,ext),(a,b),kj in (
    ('450hのクジラ',sys.argv[1],('1D','4h','1h','4h'),('2021-03-26','2025-04-15 18:00'),16604.3),
    ('日足のクジラ',sys.argv[2],('4h','1h','5min','1h'),('2025-09-19','2026-01-27'),1936.7)):
    m1=load(data); t=kozakana(m1,big,mid,small,ext,pd.Timestamp(a),pd.Timestamp(b))
    w=t.pips>0
    print(f"\n=== {nm} {a}〜{b} ===")
    print(f"クジラ5発(そのまま持つ) {kj:+.1f}p")
    print(f"小魚(1段下の鯛・最大5発):玉{len(t)} 戦{t.camp.nunique()} 勝ち{w.sum()} 負け{(~w).sum()} 合計{t.pips.sum():+.1f}p  勝ちの合計{t.pips[w].sum():+.1f} 負けの合計{t.pips[~w].sum():+.1f}")
    print(f"クジラ+小魚 {kj+t.pips.sum():+.1f}p")
    g=t.groupby(t.ent.dt.to_period('M')).pips.agg(['count','sum']).round(1); print('月ごとの小魚'); print(g.T.to_string())
    t.to_csv(f"engine/kekka_tai/hitoyama/小魚_{nm}.csv",index=False)
