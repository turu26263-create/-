# 伝票(レシート・請求書・領収書)の文字から、日付・登録番号・明細・税率ごとの金額を取り出し、計算で突き合わせる。
# 読み違いは直さずに「要確認」に出す(勝手に数字を作らない)。
# 使い方: python3 denpyo_yomi.py 文字.txt  → JSON を出す
import re, sys, json, unicodedata
def norm(s):
    s = unicodedata.normalize('NFKC', s)
    s = re.sub(r'(?<=\d)[,，]\s*(?=\d{3})', '', s)      # 1, 304 → 1304
    s = s.replace('¥', '').replace('\\', '')
    return s
def yen(t):
    m = re.findall(r'(\d[\d]*)\s*円', t) or re.findall(r'(\d+)\s*$', t)
    return int(m[-1]) if m else None
def main(txt):
    lines = [norm(l).strip() for l in txt.splitlines() if l.strip()]
    r = {'店': None, '登録番号': None, '日付': None, '時刻': None, '明細': [], '小計': None, '税率別': {}, '合計': None, '預り': None, '釣り': None, '要確認': []}
    for l in lines:
        if l.startswith('===='): continue
        if r['店'] is None and not re.search(r'\d', l): r['店'] = l; continue
        m = re.search(r'登録番号\s*\S?\s*(\d{13})', l)
        if m:
            head = re.search(r'登録番号\s*(\S?)\s*\d{13}', l).group(1)
            r['登録番号'] = 'T' + m.group(1)
            if head != 'T': r['要確認'].append(f'登録番号の頭が「{head}」と読めた。Tとして扱った(紙で確かめる)')
            continue
        m = re.search(r'(20\d\d)\s*[年/.-]\s*(\d{1,2})\s*[月/.-]\s*(\d{1,2})', l)
        if m and not r['日付']:
            y, mo, d = map(int, m.groups()); r['日付'] = f'{y:04d}-{mo:02d}-{d:02d}'
            if not (1 <= mo <= 12 and 1 <= d <= 31): r['要確認'].append('日付があり得ない数字')
            t = re.search(r'(\d{1,3})\s*[:：]\s*(\d{2})', l[m.end():])
            if t:
                h, mi = int(t.group(1)), int(t.group(2))
                if h > 23: r['要確認'].append(f'時刻が「{t.group(0)}」と読めた(あり得ない時刻。紙で確かめる)')
                else: r['時刻'] = f'{h:02d}:{mi:02d}'
            continue
        m = re.search(r'(\d+)\s*%\s*対象\D*?(\d+)\s*円.*?消費税\D*?(\d+)\s*円', l)
        if m: r['税率別'][m.group(1) + '%'] = {'対象額': int(m.group(2)), '消費税': int(m.group(3))}; continue
        for key in ['小計', '合計', '預り', '釣り']:
            if re.match(r'^(お)?' + key[0] + r'.?' + (key[1:] if len(key) > 1 else ''), l) and yen(l) is not None:
                r[key] = yen(l); break
        else:
            if '対象' in l or '軽減' in l: continue
            m = re.match(r'^(.+?)\s+(\d+)\s*円\s*(※)?', l)
            if m: r['明細'].append({'品名': m.group(1).strip('_ '), '金額': int(m.group(2)), '軽減8%': bool(m.group(3))})
    # 突き合わせ
    s = sum(x['金額'] for x in r['明細'])
    if r['小計'] is not None and s != r['小計']: r['要確認'].append(f'明細の足し算 {s} と小計 {r["小計"]} が合わない')
    if r['税率別']:
        t = sum(v['対象額'] for v in r['税率別'].values())
        if r['合計'] is not None and t != r['合計']: r['要確認'].append(f'税率別の合計 {t} と合計 {r["合計"]} が合わない')
        for k, v in r['税率別'].items():
            p = int(k[:-1]); exact = v['対象額'] * p / (100 + p)
            if abs(v['消費税'] - exact) >= 1: r['要確認'].append(f'{k}の消費税 {v["消費税"]} が計算 {exact:.1f} と合わない')
        a8 = sum(x['金額'] for x in r['明細'] if x['軽減8%'])
        if '8%' in r['税率別'] and a8 != r['税率別']['8%']['対象額']: r['要確認'].append(f'※の明細の足し算 {a8} と8%対象 {r["税率別"]["8%"]["対象額"]} が合わない')
    if None not in (r['預り'], r['釣り'], r['合計']) and r['預り'] - r['釣り'] != r['合計']:
        r['要確認'].append(f'預り {r["預り"]} − 釣り {r["釣り"]} = {r["預り"]-r["釣り"]} が合計 {r["合計"]} と合わない(預り {r["合計"]+r["釣り"]} の読み違いかも)')
    if r['登録番号'] is None: r['要確認'].append('登録番号が見つからない(適格請求書でないかも。仕入税額控除に注意)')
    return r
if __name__ == '__main__':
    print(json.dumps(main(open(sys.argv[1], encoding='utf-8').read()), ensure_ascii=False, indent=1))
