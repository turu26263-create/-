// 画像の日本語を文字にする(tesseract.js 5.1.1 と @tesseract.js-data/jpn を手元から読む。ネット不要)
// 使い方: node ocr_jpn.js 画像.png [画像2.jpg ...]
const path = require('path');
const { createWorker } = require('tesseract.js');
(async () => {
  const langPath = path.dirname(require.resolve('@tesseract.js-data/jpn/package.json')) + '/4.0.0_best_int';
  const w = await createWorker('jpn', 1, { langPath, gzip: true, cacheMethod: 'none' });
  await w.setParameters({ preserve_interword_spaces: '1' });
  for (const f of process.argv.slice(2)) {
    const { data } = await w.recognize(f);
    console.log('==== ' + f + ' (確からしさ ' + Math.round(data.confidence) + ')\n' + data.text);
  }
  await w.terminate();
})();
