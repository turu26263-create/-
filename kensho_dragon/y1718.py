import pandas as pd, numpy as np
from sim3 import *
m5,h1=load(); m=prep3(m5,h1,H1='ord'); lg=pd.read_pickle('log_4h1h_20.pkl')
c=m5.c; e5,e9,e21=ema(c,5),ema(c,9),ema(c,21); mid=c.rolling(20).mean(); sd=c.rolling(20).std(ddof=0)
bw=2*sd; bwavg=bw.rolling(100).mean(); s1=to_m5(sig(h1,'ord'),'1h',m5.index)
a=lg[(lg.open>='2017-01-01')&(lg.open<'2019-01-01')].copy().reset_index(drop=True)
idx=m5.index; rows=[]
for k,t in a.iterrows():
    j=idx.get_loc(t.open)-1; d=1 if t.dir=='買' else -1
    o,h,l,cl=m5.o.iloc[j],m5.h.iloc[j],m5.l.iloc[j],m5.c.iloc[j]
    up,dn=mid.iloc[j]+sd.iloc[j],mid.iloc[j]-sd.iloc[j]
    kawa='上の外' if cl>up else ('下の外' if cl<dn else '中')
    ch='上抜け' if cl>m5.h.iloc[j-26] else ('下抜け' if cl<m5.l.iloc[j-26] else '絡み')
    nar=1 if e5.iloc[j]>e9.iloc[j]>e21.iloc[j] else (-1 if e5.iloc[j]<e9.iloc[j]<e21.iloc[j] else 0)
    prev=a.iloc[k-1] if k>0 and a.camp.iloc[k-1]==t.camp else None
    step=None if prev is None else round(d*(t.entry-prev.entry)/PIP,1)
    rows.append(dict(札=k+1,戦=t.camp,向き=t.dir,種=t.kind,判断足=idx[j],始=o,高=h,安=l,終=cl,陰陽='陽' if cl>o else ('陰' if cl<o else '十字'),
      川=kawa,EMA5=round(e5.iloc[j],3),EMA9=round(e9.iloc[j],3),EMA21=round(e21.iloc[j],3),終と9='上' if cl>e9.iloc[j] else '下',終と21='上' if cl>e21.iloc[j] else '下',
      並び5分=nar,遅行26=ch,幅='しぼみ' if bw.iloc[j]<0.7*bwavg.iloc[j] else '開き/並',四h=int(m.trend.loc[t.open]),一h=int(s1.loc[t.open]),
      前の玉から=step,入値=round(t.entry,3),網=round(t.sl0,3),降=t.close,理由=t.why,pips=round(t.pips,1)))
df=pd.DataFrame(rows); df.to_csv('y1718_table.csv',index=False,encoding='utf-8-sig')
d=np.where(df.向き=='買',1,-1); first=df.種.str.startswith('一番槍')
ok1=first & (df.四h==d)&(df.一h==d)&(df.並び5分==d)
ok2=(~first)&(df.並び5分==d)&(df.前の玉から>=20)
print('入った玉',len(df),' 一番槍',int(first.sum()),' 足し',int((~first).sum()))
print('一番槍 決まりどおり',int(ok1.sum()),'/',int(first.sum()),'  足し 決まりどおり',int(ok2.sum()),'/',int((~first).sum()))
bad=df[~(ok1|ok2)]; print('決まりから外れた札', bad[['札','種','判断足','四h','一h','並び5分','前の玉から']].to_string(index=False) if len(bad) else 'なし')
side_ok=((d==1)&(df.終と9=='上')&(df.終と21=='上'))|((d==-1)&(df.終と9=='下')&(df.終と21=='下'))
print('終値が9・21の向き側',int(side_ok.sum()),'/',len(df))
want=np.where(d==1,'上抜け','下抜け'); print('遅行26 向きどおり',int((df.遅行26==want).sum()),' 絡み',int((df.遅行26=='絡み').sum()),' 逆',int(((df.遅行26!=want)&(df.遅行26!='絡み')).sum()))
outside=np.where(d==1,'上の外','下の外'); print('川の外(向き側)で入った',int((df.川==outside).sum()),' 川の中',int((df.川=='中').sum()))
print('しぼみで入った',int((df.幅=='しぼみ').sum()))
print('--- 年・月ごと(戦の閉じた月)')
cp=lg[(lg.close>='2017-01-01')&(lg.close<'2019-01-01')]
mm=cp.groupby([cp.close.dt.year,cp.close.dt.month]).agg(pips=('pips','sum'),玉=('pips','size'),戦=('camp','nunique'))
print(mm.pips.round().unstack(0).to_string()); print('年計', cp.groupby(cp.close.dt.year).pips.sum().round().to_dict())
cc=cp.groupby('camp').agg(pips=('pips','sum'),n=('n','max'),dir=('dir','first'),open=('open','min'),close=('close','max'),why=('why','last'))
print('戦',len(cc),' 勝ち',int((cc.pips>0).sum()),' 上位3戦'); print(cc.sort_values('pips',ascending=False).head(3).to_string()); print('下位3戦'); print(cc.sort_values('pips').head(3).to_string())
print('買い/売り', cp.groupby('dir').pips.sum().round().to_dict())
print('発数ごとの戦の損益(戦の最大発数)'); print(cc.groupby('n').pips.agg(['size','sum']).round().T.to_string())
