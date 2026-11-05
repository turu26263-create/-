import pandas as pd, numpy as np, sys
S=sys.argv[1]
d=pd.read_csv(S+'/data/USDJPY5.csv',header=None,names='d t o h l c v'.split())
d.index=pd.to_datetime(d.d+' '+d.t,format='%Y.%m.%d %H:%M'); d=d[['o','h','l','c']]
def rs(r): 
    x=d.resample(r,label='left',closed='left').agg({'o':'first','h':'max','l':'min','c':'last'}).dropna()
    x['m9']=x.c.rolling(9).mean(); x['m21']=x.c.rolling(21).mean(); return x
h4=rs('4h'); h1=rs('1h')
# 確定足だけ使う: 足の開始+長さ <= 今 の最後の足
def last_closed(x,length):
    end=x.index+pd.Timedelta(length)
    return pd.Series(np.arange(len(x)),index=end)
m=d.copy(); m['m9']=m.c.rolling(9).mean(); m['m21']=m.c.rolling(21).mean()
mid=m.c.rolling(20).mean(); sd=m.c.rolling(20).std(ddof=0); m['bu']=mid+sd; m['bl']=mid-sd
m['end']=m.index+pd.Timedelta('5min')
for x,L,n in((h4,'4h','h4'),(h1,'1h','h1')):
    e=x.copy(); e['end']=e.index+pd.Timedelta(L)
    e=e[['end','c','m9','m21']].rename(columns=lambda k:n+'_'+k if k!='end' else 'end')
    m=pd.merge_asof(m.sort_values('end'),e.sort_values('end'),on='end',direction='backward').set_index(m.index)
cond=(m.h4_c>m.h4_m9)&(m.h1_c>m.h1_m21)
x921=(m.m9>m.m21)&(m.m9.shift()<=m.m21.shift())
x219=(m.m9<m.m21)&(m.m9.shift()>=m.m21.shift())
tr=[];pos=None;idx=m.index
for i in range(30,len(m)-1):
    if pos is None and x921.iloc[i] and cond.iloc[i]:
        pos=(idx[i],idx[i+1],m.o.iloc[i+1])
    elif pos and x219.iloc[i]:
        tr.append(pos+(idx[i+1],m.o.iloc[i+1])); pos=None
t=pd.DataFrame(tr,columns=['sig','in_t','in','out_t','out']); t['pips']=(t.out-t['in'])*100
print('期間',idx[0],'〜',idx[-1],'5分足',len(m))
print('件数',len(t),'勝ち',(t.pips>0).sum(),'合計pips',round(t.pips.sum(),1),'スプ0.3引き',round((t.pips-0.3).sum(),1),'スプ1.0引き',round((t.pips-1.0).sum(),1))
print('平均',round(t.pips.mean(),2),'最大',round(t.pips.max(),1),'最小',round(t.pips.min(),1))
pf=t.pips[t.pips>0].sum()/-t.pips[t.pips<0].sum(); print('PF(素)',round(pf,2))
t.to_csv(S+'/tai_trades.csv',index=False)
print(t.head(5).to_string())
# 1件目の照らし: 合図の足と前後2本
s=t.sig.iloc[0]; j=idx.get_loc(s)
for k in range(j-2,j+3):
    r=m.iloc[k]; lag=m.iloc[k-26]
    kawa='上の外' if r.c>r.bu else ('下の外' if r.c<r.bl else '中')
    chi='上抜け' if r.c>lag.h else ('下抜け' if r.c<lag.l else '絡み')
    print(idx[k],f"O{r.o:.3f} H{r.h:.3f} L{r.l:.3f} C{r.c:.3f}",'陽' if r.c>=r.o else '陰',
      f"上ひげ{(r.h-max(r.o,r.c))*100:.1f}p 下ひげ{(min(r.o,r.c)-r.l)*100:.1f}p",'川1σ',kawa,
      f"9={r.m9:.3f} 21={r.m21:.3f}",'9>21' if r.m9>r.m21 else '9<21','遅行26本前',idx[k-26].strftime('%H:%M'),chi,
      f"| H4 C{r.h4_c:.3f} 9={r.h4_m9:.3f} H1 C{r.h1_c:.3f} 21={r.h1_m21:.3f}")
