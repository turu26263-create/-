import pandas as pd, numpy as np
from sim4 import *
from logger import run_log
m5,h1=load(); m=prep4(m5,h1,'4h',LOC='m5',NET=('4h',3))
lg=run_log(m,MAXPOS=20); lg.to_pickle('blog.pkl'); print('B 全期間',round(lg.pips.sum()),'戦',lg.camp.nunique())
c=m5.c; e5,e9,e21=ema(c,5),ema(c,9),ema(c,21); mid=c.rolling(20).mean(); sd=c.rolling(20).std(ddof=0); bw=2*sd; bwavg=bw.rolling(100).mean()
b4=bigbars(h1,'4h'); e200=to_m5(ema(b4.c,200),'4h',m5.index); c4=to_m5(b4.c,'4h',m5.index)
a=lg[(lg.open>='2017-01-01')&(lg.open<'2019-01-01')].reset_index(drop=True); idx=m5.index; rows=[]
for k,t in a.iterrows():
    j=idx.get_loc(t.open)-1; d=1 if t.dir=='買' else -1
    o,h,l,cl=m5.o.iloc[j],m5.h.iloc[j],m5.l.iloc[j],m5.c.iloc[j]
    up,dn=mid.iloc[j]+sd.iloc[j],mid.iloc[j]-sd.iloc[j]
    nar=1 if e5.iloc[j]>e9.iloc[j]>e21.iloc[j] else (-1 if e5.iloc[j]<e9.iloc[j]<e21.iloc[j] else 0)
    prev=a.iloc[k-1] if k>0 and a.camp.iloc[k-1]==t.camp else None
    rows.append(dict(札=k+1,戦=t.camp,向き=t.dir,種=t.kind,判断足=idx[j],始=o,高=h,安=l,終=cl,陰陽='陽' if cl>o else ('陰' if cl<o else '十字'),
      川='上の外' if cl>up else ('下の外' if cl<dn else '中'),EMA5=round(e5.iloc[j],3),EMA9=round(e9.iloc[j],3),EMA21=round(e21.iloc[j],3),
      終と9='上' if cl>e9.iloc[j] else '下',終と21='上' if cl>e21.iloc[j] else '下',並び5分=nar,
      遅行26='上抜け' if cl>m5.h.iloc[j-26] else ('下抜け' if cl<m5.l.iloc[j-26] else '絡み'),幅='しぼみ' if bw.iloc[j]<0.7*bwavg.iloc[j] else '開き/並',
      四h終値=round(c4.loc[t.open],3),四h200=round(e200.loc[t.open],3),四h向き=int(m.trend.loc[t.open]),
      前の玉から=None if prev is None else round(d*(t.entry-prev.entry)/PIP,1),入値=round(t.entry,3),網=round(t.sl0,3),降=t.close,理由=t.why,pips=round(t.pips,1)))
df=pd.DataFrame(rows); df.to_csv('b1718_table.csv',index=False,encoding='utf-8-sig')
d=np.where(df.向き=='買',1,-1); first=df.種.str.startswith('一番槍')
ok1=first&(df.四h向き==d)&(df.並び5分==d)&(np.sign(df.四h終値-df.四h200)==d); ok2=(~first)&(df.並び5分==d)&(df.前の玉から>=20)
print('入った玉',len(df),' 一番槍',int(first.sum()),'(うちドテン',int((df.種=='一番槍(ドテン)').sum()),') 足し',int((~first).sum()))
print('一番槍 決まりどおり(4h終値が200の向き側・5分並び)',int(ok1.sum()),'/',int(first.sum()),'  足し 決まりどおり',int(ok2.sum()),'/',int((~first).sum()))
bad=df[~(ok1|ok2)]; print('外れ', 'なし' if bad.empty else bad[['札','種','判断足','四h向き','並び5分','前の玉から']].to_string(index=False))
side=((d==1)&(df.終と9=='上')&(df.終と21=='上'))|((d==-1)&(df.終と9=='下')&(df.終と21=='下')); print('参考 終値が9・21の向き側',int(side.sum()),'/',len(df))
w=np.where(d==1,'上抜け','下抜け'); print('参考 遅行26 向きどおり',int((df.遅行26==w).sum()),'絡み',int((df.遅行26=='絡み').sum()),'逆',int(((df.遅行26!=w)&(df.遅行26!='絡み')).sum()))
print('参考 川の外(向き側)',int((df.川==np.where(d==1,'上の外','下の外')).sum()),' 中',int((df.川=='中').sum()),' しぼみ',int((df.幅=='しぼみ').sum()))
cp=lg[(lg.close>='2017-01-01')&(lg.close<'2019-01-01')]
print('--- 月ごと'); print(cp.groupby([cp.close.dt.year,cp.close.dt.month]).pips.sum().round().unstack(0).to_string())
print('年計',cp.groupby(cp.close.dt.year).pips.sum().round().to_dict(),' 買/売',cp.groupby('dir').pips.sum().round().to_dict())
cc=cp.groupby('camp').agg(p=('pips','sum'),n=('n','max'),dir=('dir','first'),k=('kind','first'),open=('open','min'),close=('close','max'),why=('why','last'))
print('戦',len(cc),' 勝ち',int((cc.p>0).sum()),' 終わり方',cc.groupby('why').p.agg(['size','sum']).round().to_dict())
print('ドテンで始まった戦',int((cc.k=='一番槍(ドテン)').sum()),round(cc[cc.k=='一番槍(ドテン)'].p.sum()))
print('上位5'); print(cc.nlargest(5,'p').round(0).to_string()); print('下位5'); print(cc.nsmallest(5,'p').round(0).to_string())
g=cc.groupby(pd.cut(cc.n,[0,1,4,8,20],labels=['1発','2-4発','5-8発','9発以上'])).p.agg(['size','sum']).round(); print('発数ごと'); print(g.T.to_string())
