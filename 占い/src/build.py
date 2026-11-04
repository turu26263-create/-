# 入力画面の計算(engine.js)を page.html に埋め込んで 鑑定書_ひな形.html を作る
import pathlib
d = pathlib.Path(__file__).parent
page = (d / "page.html").read_text(encoding="utf-8")
eng = (d / "engine.js").read_text(encoding="utf-8")
assert "/*ENGINE*/" in page
(d.parent / "鑑定書_ひな形.html").write_text(page.replace("/*ENGINE*/", eng), encoding="utf-8")
print("ok")
