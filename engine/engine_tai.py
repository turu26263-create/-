# 鯛の刺身エンジン(たくちん 11-05「4時間の9上・1時間の21上・5分で合わして鯛の刺身」「A ご」)
# ロープの編み方:1本ずつ編む。いまは1本目だけ
#  縄1 4時間の9上 = 確定した4時間足の終値が4時間EMA9より上【置き換え:EMA はエンジンに合わせた】
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
if __name__=='__main__':
    h4=nawa1(load(sys.argv[1])); x=h4.loc['2017-01-03':'2017-02-03'].copy(); x.index=x.index+JST
    for t,r in x.iterrows(): print(f"{t:%m/%d %H}時 O{r.o:.3f} H{r.h:.3f} L{r.l:.3f} C{r.c:.3f} 9={r.e9:.3f} {'9上○' if r.n1 else '9下 '}")
