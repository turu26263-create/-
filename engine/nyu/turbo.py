# ぶん回しターボエンジンの入口:設計図(JSON)を渡すと、回して表を出す(11-06)
# 使い方: python3 turbo.py 設計図.json
# 設計図の中身(例 engine/nyu/sekkeizu/kujira_nichi.json)
#   data:{dir, clock:'est'|'server'}  形:{big,mid,small,d}  space:回す物の並び(core_exit・add_exit・maxpos・sao・n8・spr・lock・tp・sl)
#   split:{名前:[年,年]}  hitoyama:[[始,終],...](大山ひと山だけも出す)  sort:並べる列  out:書き出し先
import sys, json, warnings; warnings.filterwarnings('ignore')
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from nyu import *; from tai_parts import *
cfg = json.load(open(sys.argv[1])); mk = Market(load_cached(cfg['data']['dir']), cfg['data'].get('clock', 'est'))
fx = cfg['形']; split = {k: tuple(v) for k, v in cfg.get('split', SPLIT).items()}; yamas = cfg.get('hitoyama', [])
def tup(v): return tuple(v) if isinstance(v, list) else v
def fn(**p):
    kw = dict(core_exit=tup(p.get('core_exit', ['1h', '9割れ'])), add_exit=tup(p.get('add_exit')), maxpos=p.get('maxpos', 1), sao=p.get('sao', 2.0),
              n8=p.get('n8', False), spr=p.get('spr', 0.003), reenter=p.get('maxpos', 1) > 1, sl=tup(p.get('sl')), tp=tup(p.get('tp')), lock=p.get('lock', 0))
    t, base = run_tai(mk, fx['big'], fx['mid'], fx['small'], fx['d'], **kw); r = report(t, base, fx['d'], split)
    g = t.groupby('camp').pips.sum(); r.update(山=len(g), 勝った山=int((g > 0).sum()))
    for a, b in yamas: r[f'山{a[:7]}'] = round(hitoyama(t, a, b).pips.sum(), 1)
    return r
space = {k: v for k, v in cfg['space'].items()}
df = grid_turbo(fn, space)
for k in space: df[k] = df[k].astype(str)
os.makedirs(cfg['out'], exist_ok=True); df.to_csv(os.path.join(cfg['out'], '表.csv'), index=False)
show = [c for c in df.columns if c in space] + [c for c in ['全_p', '全_pf'] + [f'{k}_p' for k in split] + ['含み損込みDD', '山', '勝った山', '取れた割合%', '伸びてから負けた玉', '降り_建値', '降り_利確', '降り_網'] + [c for c in df.columns if c.startswith('山20')] if c in df.columns]
print(f"{len(df)}通り {df.attrs['秒']}秒(CPU {os.cpu_count()})")
print(df.sort_values(cfg.get('sort', '全_p'), ascending=False)[show].head(cfg.get('top', 15)).to_string(index=False))
