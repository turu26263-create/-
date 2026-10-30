import sys, numpy as np, pandas as pd
sys.path.insert(0,'/home/user/-/.claude/skills/kaiseki-kousoku')
d=pd.read_csv(__import__('os').environ.get('M5','data/r/forex/usdjpy/USDJPY_M5.csv'),sep='\t',parse_dates=['Time']).set_index('Time')
d=d[~d.index.duplicated()]; d.columns=[c.lower() for c in d.columns]
d=d.rename(columns={'open':'o','high':'h','low':'l','close':'c'})[['o','h','l','c']]
def rs(tf): return d.resample(tf,label='left',closed='left').agg({'o':'first','h':'max','l':'min','c':'last'}).dropna()
def prep(x,n=21):
    x=x.copy(); m=x.c.rolling(n).mean(); s=x.c.rolling(n).std(ddof=0)
    x['m']=m; x['s']=s; x['z']=(x.c-m)/s
    x['wid']=s/m; x['wpct']=x.wid.rolling(100).rank(pct=True)
    x['slope']=(m-m.shift(3))/s   # 21の傾き(σ単位/3本)
    return x.dropna()
FR={'5分':rs('5min'),'15分':rs('15min'),'1時間':rs('1h')}
if __name__=='__main__':
  print('本数',{k:len(v) for k,v in FR.items()}, '重複', d.index.duplicated().sum(), '高安の矛盾', int((d.h<d.l).sum()))
  for k,x in FR.items():
    x=prep(x); x=x[x.index<'2023-01-01']
    z=x.z.values
    print(f'\n== {k}(2021〜22)  ±1σの内 {np.mean(abs(z)<1):.0%} / ±2σの内 {np.mean(abs(z)<2):.0%} / 外 {np.mean(abs(z)>=2):.1%}')
    # +2σの外で確定した足(初回)の後、どっちへ行くか(上下対称に向きをそろえる)
    for H in (6,12,24):
      res=[]
      zz=x.z.values; c=x.c.values; m=x.m.values; s=x.s.values; hi=x.h.values; lo=x.l.values; wp=x.wpct.values; sl=x.slope.values
      for i in range(1,len(x)-H):
        for sg in (1,-1):
          if sg*zz[i]>=2 and sg*zz[i-1]<2:
            fut_h=hi[i+1:i+1+H] if sg>0 else -lo[i+1:i+1+H]
            fut_l=lo[i+1:i+1+H] if sg>0 else -hi[i+1:i+1+H]
            base=sg*c[i]
            ext=(fut_h.max()-base)/s[i]       # さらに外へ伸びた幅(σ)
            back=(base-fut_l.min())/s[i]      # 戻った幅(σ)
            toM=back>=sg*(c[i]-m[i])/s[i]     # 真ん中まで戻ったか
            res.append((ext,back,toM,wp[i],sg*sl[i]))
      r=pd.DataFrame(res,columns=['ext','back','toM','wp','sl'])
      def line(q,lab):
        return f'{lab}:{len(q)}回 真ん中まで戻る{q.toM.mean():.0%} 伸び中央{q.ext.median():.2f}σ 戻り中央{q.back.median():.2f}σ'
      print(f' {H}本先  '+line(r,'全部'))
      if H==12:
        print('   '+line(r[r.wp<0.3],'しぼみ(幅下3割)'))
        print('   '+line(r[r.wp>0.7],'広がり(幅上3割)'))
        print('   '+line(r[r.sl>0.5],'21が同じ向きに起きている'))
        print('   '+line(r[r.sl<-0.0],'21が逆向き・寝ている'))
