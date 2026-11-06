# 鯛をつないでクジラ(11-06 たくちん「無限リーチ入れて日足もっと取って」「日足の9うえ 四時間の21 9割れがどうたい刺身、鯛を繋いで繋いでクジラになるやろ」)
# 入りの合図は日足の鯛の刺身と同じ(日足の9上・4hの21上・1hで入る・縄4〜5・縄8)
# 無限リーチ=合図が出るたびに玉を足す(最大 MAXPOS 発)【置き換え:20発】。玉ごとに降りを決める:
#   tai    : どの玉も4hの9割れで降りる(鯛の胴体ごとに降りて、次の鯛でまた乗る)
#   kujira : どの玉も日足の9割れで降りる(クジラ1頭を丸ごと持つ)
#   mix    : 最初の1発(クジラの芯)は日足の9割れ、足した玉(鯛)は4hの9割れ
import sys,warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,__file__.rsplit('/',1)[0])
from engine_tai_g import *
def ware(m1,tf,pre):
    b=bars(m1,tf); b['e9']=ema(b.c,9); mid=(b.o+b.c)/2
    b['wb']=(mid<b.e9)&(b.c<b.e9); b['ws']=(mid>b.e9)&(b.c>b.e9); return b[['k','wb','ws']].rename(columns={'k':pre+'k','wb':pre+'wb','ws':pre+'ws'})
def attach2(x,a,pre):
    y=pd.merge_asof(x.reset_index().rename(columns={'index':'t'}).sort_values('kakutei'),a.sort_values(pre+'k'),left_on='kakutei',right_on=pre+'k',direction='backward').set_index('t'); y.index.name=None; return y
def prep_k(m1):
    x=prep(m1,'1D','4h','1h'); x=attach2(x,ware(m1,'4h','a_'),'a_'); x=attach2(x,ware(m1,'1D','b_'),'b_'); return x
def run_k(x,d,ent,mode,MAXPOS=20,spr=0.003):
    E=ent.values; O=x.o.values; T=x.index.values
    A=(x.a_wb if d>0 else x.a_ws).fillna(False).astype(bool).values; AK=x.a_k.values
    B=(x.b_wb if d>0 else x.b_ws).fillna(False).astype(bool).values; BK=x.b_k.values
    pos=[]; tr=[]; camp=0; mx=0
    for i in range(len(x)-1):
        keep=[]
        for p in pos:
            big=(mode=='kujira') or (mode=='mix' and p['n']==1)
            hit=(B[i] and BK[i]>T[p['j']]) if big else (A[i] and AK[i]>T[p['j']])
            if hit:
                ex=O[i+1]-(0 if d>0 else spr); tr.append((p['camp'],p['n'],T[p['j']],p['e'],T[i+1],ex,(ex-p['e'])*100*d,'日足9割れ' if big else '4h9割れ'))
            else: keep.append(p)
        pos=keep
        if E[i] and len(pos)<MAXPOS:
            if not pos: camp+=1
            pos.append(dict(j=i+1,e=O[i+1]+(spr if d>0 else 0),camp=camp,n=len(pos)+1))
            mx=max(mx,len(pos))
    t=pd.DataFrame(tr,columns=['camp','n','ent','e','ext','x','pips','why']); t.attrs['maxpos']=mx; return t
def dd_open(t):  # 降りた順の損益で見た最大ドローダウン(持っている途中の含み損は入れていない)
    t=t.sort_values('ext'); eq=t.pips.cumsum(); return round((eq.cummax()-eq).max(),1)
if __name__=='__main__':
    m1=load(sys.argv[1]); out=sys.argv[2]; x=prep_k(m1); rows=[]
    for d in (1,-1):
        ent=signals(x,d,2.0 if d>0 else 2.5,True)
        for mode in ('tai','kujira','mix'):
            for mp in (1,20):
                t=run_k(x,d,ent,mode,mp); y=pd.to_datetime(t.ent).dt.year
                r=dict(向き='買い' if d>0 else '売り',降り=mode,玉=f'最大{mp}発')
                for k,msk in (('選22-24',y.between(2022,2024)),('確15-21',y.between(2015,2021)),('確25',y==2025),('全',y>0)):
                    s_=stat(t[msk]); r[k+'_p']=s_['sum']; r[k+'_pf']=s_['pf']
                r['玉の数']=len(t); r['戦']=t.camp.nunique(); r['同時最大']=t.attrs['maxpos']; r['DD(降り順)']=dd_open(t); rows.append(r)
                t.to_csv(f"{out}/K_{'buy' if d>0 else 'sell'}_{mode}_{mp}.csv",index=False)
    print(pd.DataFrame(rows).to_string(index=False))
