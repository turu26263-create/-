# 鯛の刺身エンジン(たくちん 11-05「4時間の9上・1時間の21上・5分で合わして鯛の刺身」「A ご」)
# ロープの編み方:1本ずつ編む。いまは1本目だけ
#  縄1 4時間の9上 = 確定した4時間足の終値が4時間EMA9より上【置き換え:EMA はエンジンに合わせた】(11-05 たくちん「よし」)
#  縄2 1時間の21上 = 確定した1時間足の終値が1時間EMA21より上。縄1は、その1時間足が閉じた時に確定している一番新しい4時間足を使う
# データ:HistData 1分足(EST)。表示は日本時間=EST+14時間(印の高安と合うのを照らし済み)
import sys,glob,pandas as pd
sys.path.insert(0,__file__.rsplit('/',1)[0]); from engine_ichi import ema
JST=pd.Timedelta(hours=14)
def load(m1dir):
    fs=sorted(glob.glob(m1dir+'/*.csv'))
    m=pd.concat([pd.read_csv(f,header=None,names='d t o h l c v'.split()) for f in fs]); m.index=pd.to_datetime(m.d+' '+m.t,format='%Y.%m.%d %H:%M')
    return m[['o','h','l','c']].sort_index()
def nawa1(m1):
    h4=m1.resample('4h').agg(dict(o='first',h='max',l='min',c='last')).dropna()
    h4['e9']=ema(h4.c,9); h4['n1']=h4.c>h4.e9
    h4['kakutei']=h4.index+pd.Timedelta(hours=4)   # この時刻から使える(確定足)
    return h4
def nawa2(m1,h4):
    h1=m1.resample('1h').agg(dict(o='first',h='max',l='min',c='last')).dropna()
    h1['e21']=ema(h1.c,21); h1['n2']=h1.c>h1.e21
    h1['kakutei']=h1.index+pd.Timedelta(hours=1)
    a=h4[['kakutei','n1','c','e9']].rename(columns={'kakutei':'k4','c':'c4'}).sort_values('k4')
    h1=pd.merge_asof(h1.reset_index().rename(columns={'index':'t'}).sort_values('kakutei'),a,left_on='kakutei',right_on='k4',direction='backward').set_index('t')
    h1['n12']=h1.n1.fillna(False).astype(bool)&h1.n2
    return h1
if __name__=='__main__' and len(sys.argv)>2 and sys.argv[2]=='2':
    m1=load(sys.argv[1]); h1=nawa2(m1,nawa1(m1)); x=h1.loc['2017-01-03':'2017-02-04'].copy(); x.index=x.index+JST
    for t,r in x.iterrows(): print(f"{t:%m/%d %H}時 O{r.o:.3f} H{r.h:.3f} L{r.l:.3f} C{r.c:.3f} 21={r.e21:.3f} {'21上' if r.n2 else '21下'} | 4h({r.k4+JST:%d日%H時}確定) {'9上' if r.n1 else '9下'} | {'買いの許し○' if r.n12 else '-'}")
elif __name__=='__main__':
    h4=nawa1(load(sys.argv[1])); x=h4.loc['2017-01-03':'2017-02-03'].copy(); x.index=x.index+JST
    for t,r in x.iterrows(): print(f"{t:%m/%d %H}時 O{r.o:.3f} H{r.h:.3f} L{r.l:.3f} C{r.c:.3f} 9={r.e9:.3f} {'9上○' if r.n1 else '9下 '}")
