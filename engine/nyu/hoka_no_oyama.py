# ほかの大山でも ええやつ が効くか(11-06 たくちん「b」)。データ MT4 1時間足(サーバー時刻)
# 山=その足の9が21を上抜け(921)〜下抜け(219)。日足は上の山の大きい順に8つ、450h は終わった山を全部
# 1山ずつ:クジラ5発(損切りなし・その足の219で全部降り)/上の小魚(4h21の上・最大5発)/逆目99 4h(4hの9割れで売り・9に戻ったら降り)
import sys, warnings; warnings.filterwarnings('ignore')
from nyu import *; from tai_parts import *
mk=Market(load_csv_dir(sys.argv[1]),'server')
def yama(tf,top):
    F=mk.feat(tf); up=F.e9>F.e21; seg=(up!=up.shift()).cumsum(); rows=[]
    for _,g in F[up].groupby(seg[up]):
        nxt=F.index.searchsorted(g.index[-1])+1
        if nxt>=len(F): continue                                  # まだ終わっていない山は入れない
        rows.append((g.index[0],F.k.iloc[nxt],g.l.min(),g.h.max(),(g.h.max()-g.l.min())*100))
    return pd.DataFrame(rows,columns=['始','終','安値','高値','幅']).sort_values('幅',ascending=False).head(top)
up_all,_=kozakana_ue(mk,1,5); gy,_=gyakume_99(mk,'4h',-1)
K={'1D':run_tai(mk,'1D','4h','1h',1,('1D','219'),maxpos=5,n8=True,reenter=True)[0],
   '450h':run_tai(mk,'450h','1D','1h',1,('450h','219'),maxpos=5,n8=True,reenter=True)[0]}
rows=[]
for tf,top in (('1D',8),('450h',10)):
    for _,y in yama(tf,top).iterrows():
        a,b=y.始,y.終
        k=hitoyama(K[tf],a,b); u=hitoyama(up_all,a,b); g=hitoyama(gy,a,b)
        rows.append(dict(足=tf,山=f"{a:%Y/%m/%d}〜{b:%Y/%m/%d}",幅p=round(y.幅),
            クジラ玉=len(k),クジラ勝=int((k.pips>0).sum()),クジラp=round(k.pips.sum(),1),
            上の小魚玉=len(u),上の小魚p=round(u.pips.sum(),1),逆目99戦=len(g),逆目99p=round(g.pips.sum(),1),
            合計p=round(k.pips.sum()+u.pips.sum()+g.pips.sum(),1)))
df=pd.DataFrame(rows); print(df.to_string(index=False))
for tf in ('1D','450h'):
    z=df[df.足==tf]; print(f"\n{tf}の山 {len(z)}山:クジラ プラスの山 {(z.クジラp>0).sum()}/上の小魚 プラス {(z.上の小魚p>0).sum()}/逆目99 プラス {(z.逆目99p>0).sum()}/合計 プラス {(z.合計p>0).sum()}")
df.to_csv('engine/kekka_tai/hitoyama/ほかの大山.csv',index=False)
