from sim5 import *
m5,h1=load(); B=base(m5,h1); idx=B.index
b4=bigbars(h1,'4h'); c4=b4.c; e200=ema(c4,200); a4=atr14(b4)
def side_n(n):      # 4h 終値が 200 の同じ側に n 本続いたら向きを変える
    s=np.sign(c4-e200); out=s.copy()*0; cur=0; run=0; prev=0
    vals=s.values; res=np.zeros(len(vals))
    for i,v in enumerate(vals):
        run = run+1 if v==prev else 1; prev=v
        if run>=n and v!=0: cur=v
        res[i]=cur
    r=pd.Series(res,index=c4.index); r[:c4.index[200]]=0; return r
def side_atr(k):    # 200 から ATR×k 離れたら向きを変える
    s=pd.Series(np.where(c4>e200+k*a4,1,np.where(c4<e200-k*a4,-1,np.nan)),index=c4.index).ffill().fillna(0); s[:c4.index[200]]=0; return s
def with_trend(tr):
    m=B.copy(); m['trend']=to_m5(tr,'4h',idx).values; m['loc']=B['loc']; return m
def row(tag,m,**kw):
    j=go(m,start='2017-01',end='2017-01',**kw); y7=go(m,start='2017',end='2017',**kw); y8=go(m,start='2018',end='2018',**kw)
    a=go(m,start='2022',end='2024',**kw); b=go(m,start='2015',end='2021',**kw); c=go(m,start='2025',**kw); f=go(m,**kw)
    print(f"{tag:30s} 17年1月 {j['pips']:+6d} | 2017 {y7['pips']:+6d} | 2018 {y8['pips']:+6d} | 決 {a['pips']:+7d} 確15-21 {b['pips']:+7d} 確25 {c['pips']:+6d} | 全 {f['pips']:+7d} PF{f['PF']:.2f} DD{f['DD']}",flush=True)
print('=== 土台'); row('B',B)
print('=== 直し1: ドテンを遅らせる(4h終値が200の同じ側に n本続いたら)')
for n in (2,3,4,6): row(f'{n}本続いたら',with_trend(side_n(n)))
print('=== 直し2: 200から 4hATR×k 離れたら向きを変える')
for k in (0.5,1,2): row(f'ATR×{k}離れ',with_trend(side_atr(k)))
print('=== 直し3: 入り・足しは 4h の 9と21 も同じ向きの時だけ(前半の下げ途中の買い止め)')
B['f921']=to_m5(pd.Series(np.sign(ema(c4,9)-ema(c4,21)).values,index=c4.index),'4h',idx).values
row('4h 9>21 も合わせる',B,XOK='f921')
B['f21s']=to_m5(pd.Series(np.sign(ema(c4,21).diff()).values,index=c4.index),'4h',idx).values
row('4h 21の傾きも合わせる',B,XOK='f21s')
B['f200s']=to_m5(pd.Series(np.sign(e200.diff(6)).values,index=c4.index),'4h',idx).values
row('4h 200の傾き(6本)も合わせる',B,XOK='f200s')
