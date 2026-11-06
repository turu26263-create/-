# クジラ2:日足の無限リーチ(11-06 たくちん「無限リーチ日足の9上で5発 そんぎり前の日に合わして上げていく 九のってからロウソク3本目まで竿先、差し込んできたら買う」)
# 【たくちん】日足の9上の間だけ・最大5発/損切り=前の日の安値、日ごとに上げていく(下げない)/9に乗ってからロウソク3本目までは竿先(入らない)/差し込んできたら買う
# 【置き換え】
#  - 9に乗った:確定日足の終値が日足EMA9の上。乗ってから続いている本数 k。k<=3 の間は竿先(入らない)、k>=4 で入ってよい
#  - 差し込み:直近6本の1時間足のどれかの安値が 4時間EMA21 の5p以内(以下)まで来た。そのあと「離れ」=入りの合図(下)
#  - 入りの合図 trig:'921'=1hの9が21を上抜けた確定足/'ware'=1hの終値が1hの9を下から上へ戻した確定足。どちらも終値が4h21の上・1hの+2σの内(竿先で入らない)
#  - 損切りは1時間足の安値で見る(届いたらその値、窓で飛んだら始値)。日足の9割れ(実体の真ん中と終値が9の下)でも全部降りる
#  - tai4h=True なら、2発目からの玉は4hの9割れでも降りる(鯛)
import sys,warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,__file__.rsplit('/',1)[0])
from engine_tai_g import *
from engine_kujira import ware,attach2
def prep2(m1):
    h=bars(m1,'1h'); h['kakutei']=h.k; h['e9']=ema(h.c,9); h['e21']=ema(h.c,21); h['md']=h.c.rolling(20).mean(); h['sd']=h.c.rolling(20).std(ddof=0)
    D=bars(m1,'1D'); D['e9']=ema(D.c,9); D['up']=D.c>D.e9; D['dn']=D.c<D.e9
    D['ku']=D.up.groupby((~D.up).cumsum()).cumsum(); D['kd']=D.dn.groupby((~D.dn).cumsum()).cumsum()
    H4=bars(m1,'4h'); H4['e21']=ema(H4.c,21)
    x=attach2(h,D[['k','c','e9','l','h','ku','kd']].rename(columns=lambda c:'D_'+c),'D_')
    x=attach2(x,H4[['k','c','e21']].rename(columns=lambda c:'F_'+c),'F_')
    x=attach2(x,ware(m1,'4h','a_'),'a_'); x=attach2(x,ware(m1,'1D','b_'),'b_')
    return x.drop(columns=['k'])
def signals2(x,d,trig,tgt='F'):   # tgt='F'=差し込み先は4hのEMA21 / 'D'=日足のEMA9
    up=x.e9>x.e21; up1=x.e9.shift()>x.e21.shift()
    if d>0:
        zone=(x.D_c>x.D_e9)&(x.D_ku>=4)
        lvl=x.F_e21 if tgt=='F' else x.D_e9
        touch=(x.l<=lvl+0.05).rolling(6).max()>0
        t=(up&~up1) if trig=='921' else ((x.c>x.e9)&(x.c.shift()<=x.e9.shift()))
        return zone&touch&t&(x.c>x.F_e21)&(x.c<=x.md+2*x.sd)
    zone=(x.D_c<x.D_e9)&(x.D_kd>=4)
    lvl=x.F_e21 if tgt=='F' else x.D_e9
    touch=(x.h>=lvl-0.05).rolling(6).max()>0
    t=(~up&up1) if trig=='921' else ((x.c<x.e9)&(x.c.shift()>=x.e9.shift()))
    return zone&touch&t&(x.c<x.F_e21)&(x.c>=x.md-2*x.sd)
def run2(x,d,ent,MAXPOS=5,tai4h=False,spr=0.003):
    E=ent.values; O=x.o.values; H=x.h.values; L=x.l.values; T=x.index.values
    DL=x.D_l.values if d>0 else x.D_h.values; DK=x.D_k.values
    A=(x.a_wb if d>0 else x.a_ws).fillna(False).astype(bool).values; AK=x.a_k.values
    B=(x.b_wb if d>0 else x.b_ws).fillna(False).astype(bool).values; BK=x.b_k.values
    zone=((x.D_c>x.D_e9) if d>0 else (x.D_c<x.D_e9)).values
    pos=[]; tr=[]; camp=0
    for i in range(1,len(x)-1):
        keep=[]
        for p in pos:
            # 損切りは前の日の安値(高値)へ、日ごとに上げる(売りは下げる)。入った日の前の日から
            if DK[i]>T[p['j']] or True:
                nsl=DL[i]
                if not np.isnan(nsl): p['sl']=max(p['sl'],nsl) if d>0 else min(p['sl'],nsl)
            ex=None; why=''
            if i>p['j']:
                if d>0 and L[i]<=p['sl']: ex=min(O[i],p['sl']); why='網(前の日の安値)'
                if d<0 and H[i]>=p['sl']: ex=max(O[i],p['sl'])+spr; why='網(前の日の高値)'
            if ex is None and B[i] and BK[i]>T[p['j']]: ex=O[i+1]-(0 if d>0 else spr); why='日足9割れ'
            if ex is None and tai4h and p['n']>1 and A[i] and AK[i]>T[p['j']]: ex=O[i+1]-(0 if d>0 else spr); why='4h9割れ'
            if ex is not None: tr.append((p['camp'],p['n'],T[p['j']],p['e'],T[i],ex,(ex-p['e'])*100*d,why))
            else: keep.append(p)
        pos=keep
        if E[i] and zone[i] and len(pos)<MAXPOS:
            if not pos: camp+=1
            e=O[i+1]+(spr if d>0 else 0); sl=DL[i]
            if np.isnan(sl) or (d>0 and sl>=e) or (d<0 and sl<=e): continue   # 損切りが入り値の向こうなら入らない
            pos.append(dict(j=i+1,e=e,sl=sl,camp=camp,n=len(pos)+1))
    return pd.DataFrame(tr,columns=['camp','n','ent','e','ext','x','pips','why'])
if __name__=='__main__':
    from engine_kujira import dd_open
    m1=load(sys.argv[1]); out=sys.argv[2]; x=prep2(m1); rows=[]
    h1c=x.c
    for d in (1,-1):
        for trig,tgt in (('921','F'),('ware','F'),('921','D'),('ware','D')):
            for tai4h in (False,True):
                t=run2(x,d,signals2(x,d,trig,tgt),5,tai4h); y=pd.to_datetime(t.ent).dt.year
                r=dict(向き='買い' if d>0 else '売り',差し込み先='4h21' if tgt=='F' else '日足9',合図=trig,鯛の降り='4h9割れ' if tai4h else 'なし')
                for k,msk in (('選22-24',y.between(2022,2024)),('確15-21',y.between(2015,2021)),('確25',y==2025),('全',y>0)):
                    s_=stat(t[msk]); r[k+'_p']=s_['sum']; r[k+'_pf']=s_['pf']
                r['玉']=len(t); r['戦']=t.camp.nunique(); r['DD(降り順)']=dd_open(t)
                r['網%']=round(100*t.why.str.startswith('網').mean(),1); rows.append(r)
                t.to_csv(f"{out}/K2_{'buy' if d>0 else 'sell'}_{tgt}_{trig}_{'tai' if tai4h else 'nashi'}.csv",index=False)
    print(pd.DataFrame(rows).to_string(index=False))
