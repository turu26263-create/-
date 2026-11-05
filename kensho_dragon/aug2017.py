import pandas as pd, numpy as np
from sim3 import *
m5,h1=load(); m=prep3(m5,h1,H1='ord'); lg=pd.read_pickle('log_4h1h_20.pkl')
c=m5.c; e5,e9,e21=ema(c,5),ema(c,9),ema(c,21); mid=c.rolling(20).mean(); sd=c.rolling(20).std(ddof=0)
bw=(2*sd); bwavg=bw.rolling(100).mean()
h4=bigbars(h1,'4h'); s1=to_m5(sig(h1,'ord'),'1h',m5.index)
a=lg[(lg.open>='2017-08-01')&(lg.open<'2017-09-01')].copy()
rows=[]
for k,(_,t) in enumerate(a.iterrows(),1):
    j=m5.index.get_loc(t.open)-1; tb=m5.index[j]   # 判断した確定足 = 入った足の1本前
    o,h,l,cl=m5.o.iloc[j],m5.h.iloc[j],m5.l.iloc[j],m5.c.iloc[j]
    up,dn=mid.iloc[j]+sd.iloc[j],mid.iloc[j]-sd.iloc[j]
    kawa='川の上の外' if cl>up else ('川の下の外' if cl<dn else '川の中')
    j26=j-26; ch='上抜け' if cl>m5.h.iloc[j26] else ('下抜け' if cl<m5.l.iloc[j26] else '絡み')
    rng='しぼみ' if bw.iloc[j]<0.7*bwavg.iloc[j] else '開き/並'
    narabi='5<9<21' if e5.iloc[j]<e9.iloc[j]<e21.iloc[j] else ('5>9>21' if e5.iloc[j]>e9.iloc[j]>e21.iloc[j] else 'ばらばら')
    rows.append(dict(札=k,戦=t.camp,種=t.kind,判断足=tb.strftime('%m/%d %H:%M'),始=o,高=h,安=l,終=cl,陰陽='陽' if cl>o else ('陰' if cl<o else '十字'),
        川=kawa,EMA9=round(e9.iloc[j],3),EMA21=round(e21.iloc[j],3),終と9='下' if cl<e9.iloc[j] else '上',終と21='下' if cl<e21.iloc[j] else '上',
        並び=narabi,遅行26=ch,幅=rng,四h=int(m.trend.loc[t.open]),一h=int(s1.loc[t.open]),入値=round(t.entry,3),網=round(t.sl0,3),
        降=t.close.strftime('%m/%d %H:%M'),理由=t.why,pips=round(t.pips,1)))
df=pd.DataFrame(rows); df.to_csv('aug2017_table.csv',index=False)
pd.set_option('display.width',250); print(df.to_string(index=False))
# 照らしの判定: 売りの入りなら 4h=-1・1h=-1・並び5<9<21 であること
ok=(df.四h==-1)&(df.一h==-1)&(df.並び=='5<9<21')
print('決まりどおり(4h下・1h下・5分 5<9<21):',int(ok.sum()),'/',len(df))
print('川の中で入った',int((df.川=='川の中').sum()),' 遅行が絡みで入った',int((df.遅行26=='絡み').sum()),' しぼみで入った',int((df.幅=='しぼみ').sum()))
