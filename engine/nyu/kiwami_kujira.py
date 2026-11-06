# 日足のクジラ5発 入口・出口の極み検証(11-06 たくちん「入口 出口 極み検証して」)。データ MT4 1時間足(2016/03〜2026/09)
# 選ぶ年 2022-24/確かめる年 2016-21・2025-26/スプレッド 0.3p・1.0p/含み損込みDD/山ごとの勝ち/暴走チェック
import sys, warnings; warnings.filterwarnings('ignore')
from nyu import *; from tai_parts import *
raw=load_csv_dir(sys.argv[1]); mk=Market(raw,'server')
SPL={'選22-24':(2022,2024),'確16-21':(2016,2021),'確25-26':(2025,2026)}
D=mk.feat('1D').copy(); up9=D.c>D.e9; D['k9']=up9.groupby((~up9).cumsum()).cumsum()     # 日足の終値が9の上に続いている本数
mk._f['1D']=D
def entry(kawa_chi=True,sao=2.0,n8=True,k9min=0,first_only=False):
    E=tai_entry(mk,'1D','4h','1h',1,sao,n8,kawa_chi)
    if k9min: E=E&(mk.on('1h','1D',['k9']).k9.fillna(0).values>=k9min)
    return E
def run(E,exit_=('1D','219'),maxpos=5,spr=0.003,add=None):
    XC,KC=EXITS[exit_[1]](mk,'1h',exit_[0],1)
    if add: XA,KA=EXITS[add[1]](mk,'1h',add[0],1)
    else: XA,KA=XC,KC
    base=mk.feat('1h'); return simulate(base,1,E,XC,KC,XA,KA,None,maxpos,spr,True),base
def row(t,base,**lab):
    r=report(t,base,1,SPL); g=t.groupby('camp').pips.sum()
    r.update(山=len(g),勝った山=int((g>0).sum()),一番悪い山=round(g.min(),0) if len(g) else 0); r.update(lab); return r
COL=['全_p','全_pf','選22-24_p','確16-21_p','確16-21_pf','確25-26_p','含み損込みDD','山','勝った山','一番悪い山','玉']
print('=== 1. 暴走チェック ===')
res,full=bousou(lambda r: run_tai(Market(r,'server'),'1D','4h','1h',1,('1D','219'),maxpos=5,n8=True,reenter=True)[0], raw, ['2018-06-01','2021-06-01','2024-01-10'])
print(' '.join(f"{c} {n}玉 {'同じ' if s else '違う!!'}" for c,n,s in res),'| 同時最大',full.attrs['maxheld'],'| データの終わりで持ったまま',full.attrs['held_at_end'])
E0=entry()
print('\n=== 2. 出口(入口は固定:日足9上・4h21上・1h・縄4〜5・縄8、最大5発)===')
rows=[]
for nm,ex,add in (('日足の219(今)',('1D','219'),None),('日足の9割れ',('1D','9割れ'),None),('日足の終値が9の下',('1D','終値9'),None),('4hの219',('4h','219'),None),
                  ('芯は日足219・足しは4h9割れ',('1D','219'),('4h','9割れ')),('芯は日足219・足しは日足9割れ',('1D','219'),('1D','9割れ'))):
    for spr in (0.003,0.01):
        t,b=run(E0,ex,5,spr,add); rows.append(row(t,b,出口=nm,spr=spr))
df=pd.DataFrame(rows); print(df[['出口','spr']+COL].to_string(index=False)); df.to_csv('engine/kekka_tai/kiwami/出口.csv',index=False)
print('\n=== 3. 入口(出口は固定:日足の219、spr0.3)===')
rows=[]
for kc in (True,False):
    for sao in (2.0,2.5):
        for n8 in (True,False):
            for k9 in (0,4):
                for mp in (1,3,5,10):
                    t,b=run(entry(kc,sao,n8,k9),('1D','219'),mp); rows.append(row(t,b,だまし回避=kc,竿先=sao,縄8=n8,日足9上何本目から=k9 or 1,最大=mp))
df=pd.DataFrame(rows); df=daichi(df,['竿先','最大'],'確16-21_p')
cols=['だまし回避','竿先','縄8','日足9上何本目から','最大']+COL+['台地']
print(df.sort_values('確16-21_p',ascending=False)[cols].head(12).to_string(index=False))
print('...今の形(だまし回避・2σ・縄8・1本目から・5発):'); print(df[(df.だまし回避)&(df.竿先==2.0)&(df.縄8)&(df.日足9上何本目から==1)&(df.最大==5)][cols].to_string(index=False))
df.to_csv('engine/kekka_tai/kiwami/入口.csv',index=False)
print('\n=== 4. 1玉ずつの中身(今の形)===')
t,b=run(E0); C=b.c.values; H=b.h.values; L=b.l.values; idx=b.index.values
A=np.searchsorted(idx,t.ent.values); B=np.searchsorted(idx,t.ext.values)
t['逆に行った最大']=[(L[a:bb].min()-e)*100 if bb>a else 0 for a,bb,e in zip(A,B,t.e)]
t['伸びた最大']=[(H[a:bb].max()-e)*100 if bb>a else 0 for a,bb,e in zip(A,B,t.e)]
t['天井から戻した']=t['伸びた最大']-t.pips
w=t.pips>0
print(f"玉{len(t)} 勝{w.sum()} 負{(~w).sum()}")
print(f"勝ち玉:逆に行った最大の平均 {t['逆に行った最大'][w].mean():.0f}p(一番深い {t['逆に行った最大'][w].min():.0f}p)/伸びた最大の平均 {t['伸びた最大'][w].mean():.0f}p/天井から戻した平均 {t['天井から戻した'][w].mean():.0f}p")
print(f"負け玉:逆に行った最大の平均 {t['逆に行った最大'][~w].mean():.0f}p/伸びた最大の平均 {t['伸びた最大'][~w].mean():.0f}p(伸びてから負けた玉 {(t['伸びた最大'][~w]>50).sum()}個)")
print(f"取れた割合(勝ち玉の 取った÷伸びた最大):{(t.pips[w].sum()/t['伸びた最大'][w].sum()*100):.0f}%")
g=t.groupby('camp').agg(玉=('pips','size'),合計=('pips','sum'),入り=('ent','min'),降り=('ext','max'))
g['日数']=(pd.to_datetime(g.降り)-pd.to_datetime(g.入り)).dt.days
print(f"山 {len(g)}:勝った山 {(g.合計>0).sum()}(平均 {g.日数[g.合計>0].mean():.0f}日)/負けた山 {(g.合計<=0).sum()}(平均 {g.日数[g.合計<=0].mean():.0f}日、玉1つの山 {((g.合計<=0)&(g.玉==1)).sum()})")
# 負けた山の入口の特徴(1発目の合図の足の 日足9上の本数・4h21の角度・日足21の角度)
q=mk.on('1h','1D',['k9','ang']).rename(columns={'ang':'日足21角度'}).join(mk.on('1h','4h',['ang']).rename(columns={'ang':'4h21角度'}))
f=t[t.n==1].copy(); j=np.searchsorted(idx,f.ent.values)-1
f['日足9上の本数']=q.k9.values[j]; f['日足21角度']=q['日足21角度'].values[j]; f['4h21角度']=q['4h21角度'].values[j]
f['山の合計']=f.camp.map(g.合計); f['勝ち負け']=np.where(f.山の合計>0,'勝った山','負けた山')
print('\n1発目の入口の特徴(中央値)'); print(f.groupby('勝ち負け')[['日足9上の本数','日足21角度','4h21角度']].median().round(1).to_string())
t.to_csv('engine/kekka_tai/kiwami/1玉ずつ.csv',index=False); f.to_csv('engine/kekka_tai/kiwami/1発目の入口.csv',index=False)
