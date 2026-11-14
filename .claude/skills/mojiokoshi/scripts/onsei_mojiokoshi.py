# 音声・動画の文字起こし(パソコンで回す。初回だけネットでモデルを取る)
# 入れ方: pip install faster-whisper   (動画は ffmpeg も要る)
# 使い方: python onsei_mojiokoshi.py 録音.m4a [--model small] [--wakeru]
#   出る物: 録音.txt([分:秒] つきの文) と 録音.srt(字幕)
import sys, argparse
from faster_whisper import WhisperModel
def ts(s): m, s = divmod(int(s), 60); h, m = divmod(m, 60); return f'{h:02d}:{m:02d}:{s:02d}'
def srt(s): ms = int((s - int(s)) * 1000); return ts(s) + f',{ms:03d}'
ap = argparse.ArgumentParser(); ap.add_argument('file'); ap.add_argument('--model', default='small'); ap.add_argument('--wakeru', action='store_true', help='間が2秒以上あいたら段落を分ける')
a = ap.parse_args()
model = WhisperModel(a.model, device='auto', compute_type='int8')
segs, info = model.transcribe(a.file, language='ja', vad_filter=True, beam_size=5)
base = a.file.rsplit('.', 1)[0]; prev = None; n = 0
with open(base + '.txt', 'w', encoding='utf-8') as t, open(base + '.srt', 'w', encoding='utf-8') as s:
    for g in segs:
        n += 1
        if a.wakeru and prev is not None and g.start - prev >= 2: t.write('\n')
        t.write(f'[{ts(g.start)}] {g.text.strip()}\n'); prev = g.end
        s.write(f'{n}\n{srt(g.start)} --> {srt(g.end)}\n{g.text.strip()}\n\n')
print(f'{n} 区切り・長さ {ts(info.duration)} → {base}.txt / {base}.srt')
