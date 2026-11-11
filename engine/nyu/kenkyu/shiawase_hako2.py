# 11-11 たくちん「ご」(7回目)→ 5回目の形の箱だけ替える:箱=レンジに入ってからの高値・安値(今続いているレンジの1日目の30日前〜前の日まで。レンジが続く間は広がるだけ)
# 5回目:たくちん「そうばの7割レンジやから」→ 候補1:200のまわり(日足200±日足1σ)では入らない。入りは200から離れた魚道の縁(±2σ)だけ。向きは見ない(3回目の形に1つだけ足す)
# 元:たくちん「レンジは921/219関係なくなるよ、うお道、と 箱の高さがしあわせセットやろ」
# 【置き換え・照らす前に決めた】(日足)
#   レンジ=遅行スパン(今の終値と21本前の終値の上下)が、直近30日のうちに3回以上入れ替わった(紫の線がロウソクを行ったり来たり突き抜ける)
#   箱=直近30日の高値と安値。魚道=±1σ〜±2σの帯
#   買い:レンジの間、値が日足の−2σ(魚道の下の縁・前の日足が閉じた時の線)まで差し込んだら、その値で4単位。売りは+2σで4単位(鏡うつし)。921・219は見ない
#   3単位=反対の±2σ(魚道の上の縁)に触れたら利確/1単位=ため=上飛び待ち:日足±3.5σに触れたら利確
#   網=全単位:日足の終値が箱の底(入った時の30日の安値)の下で閉じたら次の日の1時に降りる(売りは箱の天井の上)。ひげでは切らない(だまし回避の川)
#   次のセットは前のセットの3単位を利確した後だけ/ためは最大5/0時は入らない/スプレッド0.3p。1時間足で値の届き方を見る
import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *
raw=load_cached(sys.argv[1]); mk=Market(raw,'server'); SPR=0.003; P=0.01
Dd=mk.feat('1D'); sg=np.sign(Dd.c-Dd.c.shift(21)); flip=(sg!=sg.shift(1))&sg.shift(1).notna()&(sg!=0)
rng=flip.astype(int).rolling(30).sum()>=3
_r=rng.values; _h=Dd.h.values; _l=Dd.l.values; _bh=np.full(len(Dd),np.nan); _bl=np.full(len(Dd),np.nan); st=None
for k in range(len(Dd)):
    if _r[k]:
        if st is None: st=max(0,k-29)
        _bh[k]=_h[st:k+1].max(); _bl[k]=_l[st:k+1].min()
    else: st=None; _bh[k]=_h[max(0,k-29):k+1].max(); _bl[k]=_l[max(0,k-29):k+1].min()
mk._f['1D']=Dd.assign(rng=rng,bhi=_bh,blo=_bl)
def run(d):
    x=mk.feat('1h'); n=len(x); O,H,L=x.o.values,x.h.values,x.l.values; idx=x.index; hr=idx.hour.values
    y=mk.on('1h','1D',['c','md','sd','rng','bhi','blo','e200']); kd=y['k_1D'].values
    md,sd,dc=y.md.values,y.sd.values,y.c.values; rg=y.rng.fillna(False).values.astype(bool); bhi,blo=y.bhi.values,y.blo.values; e2=y.e200.values
    newday=np.r_[False,kd[1:]!=kd[:-1]]
    pos=[]; out=[]; pair=False; brk=False
    for i in range(1,n-1):
        lv=md[i-1]-2*d*sd[i-1]; tp2=md[i-1]+2*d*sd[i-1]; tp35=md[i-1]+3.5*d*sd[i-1]
        keep=[]
        for p in pos:
            ex=None
            if i>p['j']:
                if p['brk'] and hr[i]!=0: ex=(O[i]+(0 if d>0 else SPR),'箱割れ')
                else:
                    tv=tp2 if p['r']=='刈る' else tp35
                    if not np.isnan(tv) and ((d>0 and tv>p['e'] and H[i]>=tv) or (d<0 and tv<p['e']-SPR and L[i]<=tv)): ex=(max(O[i],tv) if d>0 else min(O[i],tv)+SPR,'利確')
            if ex: out.append(dict(ent=idx[p['j']],e=p['e'],ext=idx[i],x=ex[0],pips=(ex[0]-p['e'])/P*d,why=ex[1],r=p['r'],set=p['s']))
            else: keep.append(p)
        pos=keep
        if newday[i]:                                              # 日足が閉じた:箱割れを見る(閉じた終値で)
            for p in pos:
                if (d>0 and dc[i]<p['bx']) or (d<0 and dc[i]>p['bx']): p['brk']=True
        if pair and not any(p['r']=='刈る' for p in pos): pair=False
        if rg[i-1] and not pair and hr[i]!=0 and sum(1 for p in pos if p['r']=='ため')<5 and not np.isnan(lv) and ((d>0 and L[i]<=lv) or (d<0 and H[i]>=lv)):
            e=(min(O[i],lv)+SPR) if d>0 else max(O[i],lv); bx=blo[i-1] if d>0 else bhi[i-1]
            if ((d>0 and e>bx) or (d<0 and e<bx)) and abs(e-e2[i-1])>sd[i-1]:
                for r in ('刈る','刈る','刈る','ため'): pos.append(dict(j=i,e=e,r=r,s=i,bx=bx,brk=False))
                pair=True
    return pd.DataFrame(out)
t=pd.concat([run(1).assign(d=1),run(-1).assign(d=-1)],ignore_index=True); y=pd.to_datetime(t.ent).dt.year; t['p']=t.pips/4
A=t[t.r=='刈る']; B=t[t.r=='ため']
print(f"レンジに入ってからの箱 しあわせセット:{t.set.nunique()}セット / 全部 {t.p.sum():+,.0f}p(1セット=0.01ロットぶん)/ 選22-24 {t.p[y.between(2022,2024)].sum():+,.0f} / 確かめる年 {t.p[~y.between(2022,2024)].sum():+,.0f}")
print(f"  3単位:利確 {int((A.why=='利確').sum())} 箱割れ {int((A.why=='箱割れ').sum())} 平均 {A.pips.mean():+.1f}p / ため:平均 {B.pips.mean():+.1f}p {B.why.value_counts().to_dict()}")
print('  年ごと',{int(k):round(v) for k,v in t.groupby(y).p.sum().items()},' 買い',round(t.p[t.d==1].sum()),' 売り',round(t.p[t.d==-1].sum()))
lv=mk.feat('1D'); print('  レンジの日',int(lv.rng.sum()),'/',len(lv),' 2017年',int(lv.rng['2017-01-01':'2017-12-31'].sum()),'日')
print('--- 歩き:2017年 ---')
for (s_,d),g in t[(t.ent>='2017-01-01')&(t.ent<'2018-01-01')].groupby(['set','d']):
    a=g[g.r=='刈る']; b=g[g.r=='ため'].iloc[0]
    print(f"  {'買い' if d>0 else '売り'} {g.ent.iloc[0]:%m/%d %H時} {g.e.iloc[0]:.3f} → 3単位 {a.ext.iloc[0]:%m/%d} {a.pips.iloc[0]:+.0f}p {a.why.iloc[0]} / ため {b.ext:%m/%d} {b.pips:+.0f}p {b.why}")
