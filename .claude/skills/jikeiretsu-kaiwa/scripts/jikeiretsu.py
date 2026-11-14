# いろいろな形の会話の記録(LINEの書き出し・[日時] 名前: 本文・チャットの写し)を、1本の時系列に並べる。
# 同じ発言の重複は1つにまとめ、間が空いた所(既定 6時間)に区切りを入れる。時刻は書いてあるまま(日本時間)として扱う。
# 使い方: python3 jikeiretsu.py 記録1.txt 記録2.txt ... [--gap 6] > 時系列.md
import re, sys, unicodedata
from datetime import datetime, timedelta
def norm(s): return unicodedata.normalize('NFKC', s).rstrip('\n')
def parse(path):
    out, day, last = [], None, None
    for raw in open(path, encoding='utf-8-sig'):
        l = norm(raw)
        m = re.match(r'^(20\d\d)[/.-](\d{1,2})[/.-](\d{1,2})\s*(\(.\))?\s*$', l)          # LINE の日付の行
        if m: day = datetime(*map(int, m.groups()[:3])); continue
        m = re.match(r'^(\d{1,2}):(\d{2})\t([^\t]*)\t(.*)$', l)                         # LINE: 時刻<tab>名前<tab>本文
        if m and day:
            last = {'t': day.replace(hour=int(m[1]), minute=int(m[2])), '誰': m[3], '本文': m[4], '元': path}; out.append(last); continue
        m = re.match(r'^\[?(20\d\d)[/.-](\d{1,2})[/.-](\d{1,2})[ T](\d{1,2}):(\d{2})(?::\d{2})?\]?\s*([^:：]+?)\s*[:：]\s*(.*)$', l)  # [日時] 名前: 本文
        if m:
            g = list(map(int, m.groups()[:5])); last = {'t': datetime(*g), '誰': m[6], '本文': m[7], '元': path}; out.append(last); continue
        if last and l.strip(): last['本文'] += '\n' + l                                   # 続きの行
    return out
def main(args):
    gap = 6.0
    if '--gap' in args: i = args.index('--gap'); gap = float(args[i + 1]); del args[i:i + 2]
    allm, seen = [], set()
    for p in args:
        for x in parse(p):
            k = (x['t'], x['誰'].strip(), re.sub(r'\s+', '', x['本文']))
            if k in seen: continue
            seen.add(k); allm.append(x)
    allm.sort(key=lambda x: x['t'])                                                          # 同じ時刻は読んだ順のまま(安定)
    prev, day = None, None
    for x in allm:
        if prev and x['t'] - prev > timedelta(hours=gap): print(f'\n---- ここで {round((x["t"]-prev).total_seconds()/3600,1)} 時間あいた ----')
        if x['t'].date() != day: day = x['t'].date(); print(f'\n## {day:%Y年%m月%d日}({"月火水木金土日"[day.weekday()]})')
        print(f'- {x["t"]:%H:%M} **{x["誰"]}**: ' + x['本文'].replace('\n', '\n  '))
        prev = x['t']
    print(f'\n(合計 {len(allm)} 件・重複を除いた数。元のファイル {len(args)} 個)')
if __name__ == '__main__': main(sys.argv[1:])
