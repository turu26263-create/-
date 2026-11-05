# 鯛の刺身エンジン(たくちん 11-05「4時間の9上・1時間の21上・5分で合わして鯛の刺身」「A ご」)
# ロープの編み方:1本ずつ編む。いまは1本目だけ
#  縄1 4時間の9上 = 確定した4時間足の終値が4時間EMA9より上【置き換え:EMA はエンジンに合わせた】(11-05 たくちん「よし」)
#  縄3 5分の921 = 確定した5分足で EMA9 が EMA21 を上抜け(1本前は9<=21)。その時に確定している一番新しい1時間足の「買いの許し」(縄1+縄2)が○なら、次の5分足の始値で入る
#  縄3改 許しが出た時にもう921が済んでいる時 = 買いの許しが×→○に変わった最初の5分足で、5分の EMA9>EMA21 なら次の5分足の始値で入る(11-05 たくちん「ご」)
#  縄4 だまし回避 = 入りの5分足の終値が +1σ の外(川の上の外)で、終値が21本前の5分足の高値を上抜け(遅行21本前)(11-05 たくちん「ご」)
#  縄5 竿先で入らない = 入りの5分足の終値が +2σ の外なら入らない(決まり帳 入2【たくちん】「竿先や根っこでないのにはいるな」。11-05「ご」)
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
def ichi(c,mid,sd):
    return '竿先+' if c>mid+2*sd else '上の魚道' if c>mid+sd else '川' if c>=mid-sd else '下の魚道' if c>=mid-2*sd else '竿先-'
def nawa3(m1,h1,h4):
    m=m1.resample('5min').agg(dict(o='first',h='max',l='min',c='last')).dropna()
    m['e9']=ema(m.c,9); m['e21']=ema(m.c,21); m['mid']=m.c.rolling(20).mean(); m['sd']=m.c.rolling(20).std(ddof=0)
    m['x921']=(m.e9>m.e21)&(m.e9.shift()<=m.e21.shift())
    m['kakutei']=m.index+pd.Timedelta(minutes=5)
    h1=h1.copy(); h1['mid1']=h1.c.rolling(20).mean(); h1['sd1']=h1.c.rolling(20).std(ddof=0); h1['e91']=ema(h1.c,9)
    h4=h4.copy(); h4['e21_4']=ema(h4.c,21); h4['e200_4']=ema(h4.c,200); h4['mid4']=h4.c.rolling(20).mean(); h4['sd4']=h4.c.rolling(20).std(ddof=0)
    a=h1.reset_index()[['t','kakutei','c','e21','e91','mid1','sd1','n2','n1','n12']].rename(columns={'t':'t1','kakutei':'k1','c':'c1','e21':'e211'}).sort_values('k1')
    b=h4.reset_index().rename(columns={'index':'t4'})[['t4','kakutei','c','e9','e21_4','e200_4','mid4','sd4']].rename(columns={'kakutei':'k4b','c':'c4b','e9':'e9_4'}).sort_values('k4b')
    x=m.reset_index().rename(columns={'index':'t'}).sort_values('kakutei')
    x=pd.merge_asof(x,a,left_on='kakutei',right_on='k1',direction='backward')
    x=pd.merge_asof(x,b,left_on='kakutei',right_on='k4b',direction='backward').set_index('t')
    perm=x.n12.fillna(False).astype(bool); x['perm']=perm
    x['ent921']=x.x921&perm
    x['entkai']=perm&~perm.shift(1,fill_value=False)&(x.e9>x.e21)&~x.x921
    x['ent']=x.ent921|x.entkai
    x['kawa']=x.c>x['mid']+x.sd; x['chi']=x.c>x.h.shift(21); x['h21']=x.h.shift(21)
    x['ent4']=x.ent&x.kawa&x.chi
    x['u2']=x['mid']+2*x.sd; x['ent5']=x.ent4&(x.c<=x.u2)
    return x
if __name__=='__main__' and len(sys.argv)>2 and sys.argv[2]=='3':
    m1=load(sys.argv[1]); h4=nawa1(m1); h1=nawa2(m1,h4); x=nawa3(m1,h1,h4)
    y=x.loc['2017-01-02 10:00':'2017-02-04']; idx=x.index
    col='entkai' if len(sys.argv)>3 and sys.argv[3]=='kai' else 'ent'
    if len(sys.argv)>3 and sys.argv[3]=='5':
        for t,r in y[y.ent4].iterrows():
            nx=x.iloc[idx.get_loc(t)+1]
            print(f"{t+JST:%m/%d %H:%M} {'921' if r.ent921 else '改 '} C{r.c:.3f} +2σ={r.u2:.3f} {'竿先+の外→縄5で消える' if r.c>r.u2 else '魚道の中【縄5 入る】'} | 入り{nx.o:.3f}")
        sys.exit()
    if len(sys.argv)>3 and sys.argv[3]=='4':
        for t,r in y[y.ent].iterrows():
            nx=x.iloc[idx.get_loc(t)+1]; ok=r.kawa and r.chi
            print(f"{t+JST:%m/%d %H:%M} {'921' if r.ent921 else '改 '} C{r.c:.3f} +1σ={r['mid']+r.sd:.3f} {'外○' if r.kawa else '中×'} 21本前({t+JST-pd.Timedelta(minutes=105):%H:%M})高値{r.h21:.3f} {'上抜け○' if r.chi else '抜けず×'} 5分位置:{ichi(r.c,r['mid'],r.sd)} | 入り{nx.o:.3f} {'【縄4 入る】' if ok else '縄4で消える'}")
        sys.exit()
    for t,r in y[y[col]].iterrows():
        nx=x.iloc[idx.get_loc(t)+1]
        print(f"{t+JST:%m/%d %H:%M} {'陽' if r.c>=r.o else '陰'} O{r.o:.3f} C{r.c:.3f} 5分9={r.e9:.3f} 21={r.e21:.3f} 5分位置:{ichi(r.c,r['mid'],r.sd)} | 1h({r.t1+JST:%d日%H時}) C{r.c1:.3f} 9={r.e91:.3f} 21={r.e211:.3f} {ichi(r.c1,r.mid1,r.sd1)} | 4h({r.t4+JST:%d日%H時}) C{r.c4b:.3f} 9={r.e9_4:.3f} 21={r.e21_4:.3f} 200={r.e200_4:.3f} {ichi(r.c4b,r.mid4,r.sd4)} | 入り{nx.o:.3f}")
elif __name__=='__main__' and len(sys.argv)>2 and sys.argv[2]=='2':
    m1=load(sys.argv[1]); h1=nawa2(m1,nawa1(m1)); x=h1.loc['2017-01-03':'2017-02-04'].copy(); x.index=x.index+JST
    for t,r in x.iterrows(): print(f"{t:%m/%d %H}時 O{r.o:.3f} H{r.h:.3f} L{r.l:.3f} C{r.c:.3f} 21={r.e21:.3f} {'21上' if r.n2 else '21下'} | 4h({r.k4+JST:%d日%H時}確定) {'9上' if r.n1 else '9下'} | {'買いの許し○' if r.n12 else '-'}")
elif __name__=='__main__':
    h4=nawa1(load(sys.argv[1])); x=h4.loc['2017-01-03':'2017-02-03'].copy(); x.index=x.index+JST
    for t,r in x.iterrows(): print(f"{t:%m/%d %H}時 O{r.o:.3f} H{r.h:.3f} L{r.l:.3f} C{r.c:.3f} 9={r.e9:.3f} {'9上○' if r.n1 else '9下 '}")
