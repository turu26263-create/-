# 11-11 たくちん「しあわせセットもわかってない 遅刻スパンロウソクがらみでしあわせセット」
# しあわせセット=レンジ(遅行スパンがロウソクに絡んでいる所)でやる鏡打ち(かがみ無限 決まり帳 鏡1・鏡2・出1、たくちん「bb-2で買う4 bb2でさんりかく ためて、うえとびまち」)
# 【置き換え・照らす前に決めた】
#   レンジ=日足の遅行スパンが直近12日のうち8日以上ロウソクに絡む。12日のうち8日は押し目エンジン押1・ポンの貯めと同じ数
#     絡む:1回目は5分の押1と同じ「終値が21本前の1本の安値〜高値の中」にしたが、日足では10年で41日しかレンジにならず、2017年の箱も拾えず0セットだった
#     → 2回目(これ):遅行スパンの線がロウソクの群れに重なっている=終値が21本前の前後2本(19〜23本前の5本)の安値〜高値の中
#   入り(鏡1):レンジの間、閉じた日足が−2σに触れて帯の中へ戻した(安値<=−2σ・終値>−2σ)→ 次の日の1時に買い4単位(+2σに触れて戻したら売り4単位)
#   日足の219(921)は「入った後に新しく出た」時だけ降りる(レンジでは日足が219の並びのままの事が多いので、前から続く並びでは降りない・入りも並びは問わない)
#   3単位=日足の反対の±2σ(前の日足が閉じた時の線)に触れたら利確(鏡2)/1単位=ため=上飛び待ち:日足±3.5σに触れたら利確・日足219(売りは921)で降り(出1)。3単位も日足219で一緒に降りる
#   次のセットは前のセットの3単位を利確した後だけ(差し込んだら買う→上がったら売る→差し込んだら買う)。ためは最大5。0時の入り降りは1時へ。スプレッド0.3p。網は無し(鏡1・鏡2・出1 に網は無い)
import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *
raw=load_cached(sys.argv[1]); mk=Market(raw,'server'); SPR=0.003; P=0.01
Dd=mk.feat('1D'); lo5=Dd.l.shift(19).rolling(5).min(); hi5=Dd.h.shift(19).rolling(5).max()   # 21本前の前後2本(19〜23本前)の5本の安値〜高値
ent=((Dd.c>=lo5)&(Dd.c<=hi5)).astype(int); rng=(ent.rolling(12).sum()>=8)
mk._f['1D']=Dd.assign(rng=rng)
def hoimi(d):
    x=mk.feat('1h'); n=len(x); O,H,L=x.o.values,x.h.values,x.l.values; idx=x.index; hr=idx.hour.values
    y=mk.on('1h','1D',['h','l','c','md','sd','rng','up921']); kd=y['k_1D'].values
    md,sd=y.md.values,y.sd.values; dh,dl,dc=y.h.values,y.l.values,y.c.values; rg=y.rng.fillna(False).values.astype(bool)
    u=y.up921.fillna(True).values.astype(bool); x219=(~u) if d>0 else u
    newday=np.r_[False,kd[1:]!=kd[:-1]]
    pos=[]; out=[]; pair=False; armed=False; xp=False; prevx=None
    for i in range(1,n-1):
        lo=md[i-1]-2*d*sd[i-1]; hi2=md[i-1]+2*d*sd[i-1]; hi35=md[i-1]+3.5*d*sd[i-1]   # 前の1時間足までに閉じた日足の線
        keep=[]
        for p in pos:
            ex=None
            if i>p['j']:
                tv=hi2 if p['r']=='刈る' else hi35
                if not np.isnan(tv) and ((d>0 and tv>p['e'] and H[i]>=tv) or (d<0 and tv<p['e']-SPR and L[i]<=tv)): ex=(max(O[i],tv) if d>0 else min(O[i],tv)+SPR,'利確',i)
                elif xp and hr[i]!=0: ex=(O[i]+(0 if d>0 else SPR),'日足219',i)
            if ex: out.append(dict(ent=idx[p['j']],e=p['e'],ext=idx[ex[2]],x=ex[0],pips=(ex[0]-p['e'])/P*d,why=ex[1],r=p['r'],set=p['s']))
            else: keep.append(p)
        pos=keep
        if not pos: xp=False
        if pair and not any(p['r']=='刈る' for p in pos): pair=False
        if newday[i]:                                                     # 日足が閉じた(この1時間足から新しい日足の線)
            if prevx is not None and x219[i] and not prevx and pos: xp=True   # 新しく出た日足219 → 次の1時で全部降り
            prevx=x219[i]
            touch=(dl[i]<=md[i]-2*sd[i] and dc[i]>md[i]-2*sd[i]) if d>0 else (dh[i]>=md[i]+2*sd[i] and dc[i]<md[i]+2*sd[i])
            armed = bool(rg[i] and touch)
        if armed and hr[i]==1 and not pair and sum(1 for p in pos if p['r']=='ため')<5:
            e=O[i]+(SPR if d>0 else 0)
            for r in ('刈る','刈る','刈る','ため'): pos.append(dict(j=i,e=e,r=r,s=i))
            pair=True; armed=False
        elif armed and hr[i]>1: armed=False
    return pd.DataFrame(out)
t=pd.concat([hoimi(1).assign(d=1),hoimi(-1).assign(d=-1)],ignore_index=True); y=pd.to_datetime(t.ent).dt.year
t['p']=t.pips/4                                                          # 1セット(4単位)=0.01ロットぶん
A=t[t.r=='刈る']; B=t[t.r=='ため']
print(f"レンジ(遅行スパン12日中8日絡み)のしあわせセット:{t.set.nunique()}セット / 全部 {t.p.sum():+,.0f}p(1セット=0.01ロットぶん)/ 選22-24 {t.p[y.between(2022,2024)].sum():+,.0f} / 確かめる年 {t.p[~y.between(2022,2024)].sum():+,.0f}")
print(f"  3単位:{len(A)}単位 利確 {int((A.why=='利確').sum())} 平均 {A.pips.mean():+.1f}p / ため:{len(B)}単位 平均 {B.pips.mean():+.1f}p {B.why.value_counts().to_dict()}")
print('  年ごと',{int(k):round(v) for k,v in t.groupby(y).p.sum().items()})
print('  買い',round(t.p[t.d==1].sum()),' 売り',round(t.p[t.d==-1].sum()))
print('--- 歩き:2017年(箱 108〜114円)---')
for (s_,d),g in t[(t.ent>='2017-01-01')&(t.ent<'2018-01-01')].groupby(['set','d']):
    a=g[g.r=='刈る']; b=g[g.r=='ため'].iloc[0]
    print(f"  {'買い' if d>0 else '売り'} {g.ent.iloc[0]:%m/%d %H時} {g.e.iloc[0]:.3f} → 3単位 {a.ext.iloc[0]:%m/%d} {a.pips.iloc[0]:+.0f}p {a.why.iloc[0]} / ため {b.ext:%m/%d} {b.pips:+.0f}p {b.why}")
