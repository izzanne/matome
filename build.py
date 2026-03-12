#!/usr/bin/env python3
import urllib.request
import urllib.parse
import gzip
import re
import os
import concurrent.futures
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))

SITES = [
    {"name": "痛いニュース",           "url": "https://itainews.com/",                "rss": "https://itainews.com/index.rdf",                   "cat": "ニュース"},
    {"name": "ニュー速クオリティ",     "url": "https://news4vip.livedoor.biz/",       "rss": "https://news4vip.livedoor.biz/index.rdf",          "cat": "VIP"},
    {"name": "カナ速",                 "url": "http://kanasoku.info/",                "rss": "http://kanasoku.info/index.rdf",                    "cat": "VIP"},
    {"name": "VIPPERな俺",             "url": "http://blog.livedoor.jp/news23vip/",   "rss": "http://blog.livedoor.jp/news23vip/index.rdf",       "cat": "VIP"},
    {"name": "BIPブログ",              "url": "http://bipblog.com/",                  "rss": "http://bipblog.com/index.rdf",                      "cat": "VIP"},
    {"name": "ハムスター速報",         "url": "https://hamusoku.com/",                "rss": "https://hamusoku.com/index.rdf",                    "cat": "ニュース"},
    {"name": "アルファルファモザイク", "url": "https://alfalfalfa.com/",              "rss": "https://alfalfalfa.com/index.rdf",                  "cat": "ニュース"},
    {"name": "ぶる速-VIP",             "url": "http://burusoku-vip.com/",            "rss": "http://burusoku-vip.com/index.rdf",                 "cat": "VIP"},
    {"name": "もみあげチャ～シュ～",   "url": "https://michaelsan.livedoor.biz/",     "rss": "https://michaelsan.livedoor.biz/index.rdf",         "cat": "スポーツ"},
    {"name": "まとめたニュース",       "url": "http://matometanews.com/",             "rss": "http://matometanews.com/index.rdf",                 "cat": "ニュース"},
    {"name": "マジキチ速報",           "url": "https://majikichi.com/",               "rss": "https://majikichi.com/index.rdf",                   "cat": "ニュース"},
    {"name": "キニ速",                 "url": "http://blog.livedoor.jp/kinisoku/",    "rss": "http://blog.livedoor.jp/kinisoku/index.rdf",        "cat": "VIP"},
    {"name": "カオスちゃんねる",       "url": "http://chaos2ch.com/",                 "rss": "http://chaos2ch.com/index.rdf",                     "cat": "VIP"},
    {"name": "watch@２ちゃんねる",     "url": "http://www.watch2chan.com",            "rss": "http://www.watch2chan.com/index.rdf",               "cat": "ニュース"},
    {"name": "なんだかおもしろい",     "url": "https://zakuzaku911.com/",             "rss": "https://zakuzaku911.com/index.rdf",                 "cat": "マンガ"},
    {"name": "デジタルニューススレ",   "url": "http://digital-thread.com/",           "rss": "http://digital-thread.com/index.rdf",               "cat": "VIP"},
    {"name": "黒マッチョニュース",     "url": "https://kuromacyo.livedoor.biz/",      "rss": "https://kuromacyo.livedoor.biz/index.rdf",         "cat": "ニュース"},
    {"name": "ガジェット2ch",     "url": "http://www.gadget2ch.com/",           "rss": "http://www.gadget2ch.com/index.rdf",              "cat": "ガジェット"},
    {"name": "いたしん！",         "url": "http://blog.livedoor.jp/itsoku/",     "rss": "http://blog.livedoor.jp/itsoku/index.rdf",        "cat": "VIP"},
    {"name": "デイトレ速報",       "url": "https://daytrader.ldblog.jp/",        "rss": "https://daytrader.ldblog.jp/index.rdf",           "cat": "株・経済"},
    {"name": "GIZMODO",            "url": "https://www.gizmodo.jp/",             "rss": "https://www.gizmodo.jp/index.xml",                "cat": "ガジェット"},
]

ITEMS_PER_SITE = 7

def decode_entities(s):
    s = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), s)
    s = re.sub(r'&#x([0-9a-fA-F]+);', lambda m: chr(int(m.group(1), 16)), s)
    return s.replace('&amp;','&').replace('&lt;','<').replace('&gt;','>').replace('&quot;','"').replace('&apos;',"'")

def extract_tag(text, tag):
    """タグ名（名前空間なし）の中身を取得"""
    # <xxx:tag> or <tag> 両方対応
    m = re.search(r'<(?:[^:>\s]+:)?' + tag + r'(?:\s[^>]*)?>([^<]*(?:<!\[CDATA\[.*?\]\]>[^<]*)*)</(?:[^:>]+:)?' + tag + r'>', text, re.DOTALL)
    if m:
        val = m.group(1)
        val = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', val, flags=re.DOTALL)
        return val.strip()
    return ''

def fetch_rss(site):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "ja,en;q=0.9",
    }
    req = urllib.request.Request(site["rss"], headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read()
        if resp.info().get("Content-Encoding") == "gzip" or raw[:2] == b'\x1f\x8b':
            raw = gzip.decompress(raw)

    for enc in ("utf-8", "shift_jis", "euc-jp", "utf-8-sig"):
        try:
            text = raw.decode(enc)
            break
        except Exception:
            continue
    else:
        text = raw.decode("utf-8", errors="replace")

    # <item> ブロックを正規表現で抽出（名前空間付きも対応）
    item_blocks = re.findall(r'<(?:[^:>\s]+:)?item[\s>].*?</(?:[^:>]+:)?item>', text, re.DOTALL)

    items = []
    for block in item_blocks:
        title = decode_entities(extract_tag(block, 'title'))
        link  = decode_entities(extract_tag(block, 'link'))
        if not link:
            link = decode_entities(extract_tag(block, 'guid'))
        # タグを除去
        title = re.sub(r'<[^>]+>', '', title).strip()
        link  = re.sub(r'<[^>]+>', '', link).strip()

        if title and link and link.startswith('http'):
            items.append({"title": title, "link": link})
        if len(items) >= ITEMS_PER_SITE:
            break

    return items

def h(s):
    return str(s).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')

def build_html(results):
    now = datetime.now(JST).strftime("%Y/%m/%d %H:%M")
    cats = list(dict.fromkeys(s["cat"] for s in SITES))
    cat_tabs = "\n".join(
        f'<button class="fb" data-c="{h(c)}" onclick="sf(\'{h(c)}\',this)">{h(c)}</button>'
        for c in cats
    )
    blocks = []
    for site in SITES:
        items = results.get(site["name"], [])
        favicon = f"https://www.google.com/s2/favicons?sz=32&domain_url={urllib.parse.quote(site['url'])}"
        if items:
            lis = "\n".join(
                f'<li><a href="{h(i["link"])}" target="_blank" rel="noopener">{h(i["title"])}</a></li>'
                for i in items
            )
            body = f'<ul class="al">{lis}</ul>'
        else:
            body = '<div class="em">⚠ 取得できませんでした</div>'
        blocks.append(f'''<div class="sb" data-c="{h(site['cat'])}">
<div class="sh"><img class="fv" src="{favicon}" onerror="this.style.display=\'none\'">
<a class="sn" href="{h(site['url'])}" target="_blank">{h(site['name'])}</a>
<span class="sm">{len(items)}件</span></div>{body}</div>''')

    return f'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>まとめ速報</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&family=Bebas+Neue&display=swap" rel="stylesheet">
<style>
:root{{--bg:#0f0f13;--sf:#18181f;--s2:#22222c;--ac:#ff4040;--tx:#e8e8f0;--mu:#888899;--bd:#2a2a38;}}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:var(--bg);color:var(--tx);font-family:'Noto Sans JP',sans-serif;font-size:13px;}}
header{{background:linear-gradient(135deg,#1a0005,#0f0f13 50%,#001a0f);border-bottom:2px solid var(--ac);padding:11px 14px;position:sticky;top:0;z-index:100;display:flex;align-items:center;gap:10px;flex-wrap:wrap;}}
.logo{{font-family:'Bebas Neue',sans-serif;font-size:24px;letter-spacing:2px;color:var(--ac);}}
.logo span{{color:var(--tx);}}
.lu{{color:var(--mu);font-size:11px;flex:1;}}
.fb-bar{{background:var(--sf);border-bottom:1px solid var(--bd);padding:0 10px;display:flex;gap:1px;overflow-x:auto;scrollbar-width:none;-webkit-overflow-scrolling:touch;}}
.fb-bar::-webkit-scrollbar{{display:none;}}
.fb{{background:none;border:none;color:var(--mu);padding:10px 14px;cursor:pointer;font-family:'Noto Sans JP',sans-serif;font-size:12px;white-space:nowrap;border-bottom:2px solid transparent;transition:.15s;}}
.fb:hover{{color:var(--tx);}}
.fb.act{{color:var(--ac);border-bottom-color:var(--ac);}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:1px;background:var(--bd);padding:1px;}}
.sb{{background:var(--sf);}}
.sh{{display:flex;align-items:center;gap:7px;padding:8px 11px;border-bottom:1px solid var(--bd);background:var(--s2);}}
.fv{{width:16px;height:16px;border-radius:2px;flex-shrink:0;}}
.sn{{font-weight:700;font-size:12px;color:var(--tx);flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;text-decoration:none;}}
.sn:hover{{color:var(--ac);}}
.sm{{font-size:10px;color:var(--mu);}}
.al{{list-style:none;}}
.al li{{border-bottom:1px solid var(--bd);}}
.al li:last-child{{border-bottom:none;}}
.al a{{display:block;padding:6px 11px;color:var(--tx);text-decoration:none;line-height:1.55;font-size:12.5px;-webkit-tap-highlight-color:transparent;}}
.al a:hover,.al a:active{{background:var(--s2);color:#fff;}}
.al a:visited{{color:#7a7a9a;}}
.em{{padding:13px;font-size:11px;color:#ff7070;text-align:center;}}
#top{{position:fixed;bottom:18px;right:16px;background:var(--ac);color:#fff;border:none;width:38px;height:38px;border-radius:50%;font-size:18px;cursor:pointer;opacity:0;transition:.3s;z-index:50;}}
#top.show{{opacity:1;}}
@media(max-width:480px){{.grid{{grid-template-columns:1fr;}}}}
</style>
</head>
<body>
<header>
  <div class="logo">まとめ<span>速報</span></div>
  <span class="lu">更新: {now}</span>
</header>
<div class="fb-bar">
  <button class="fb act" data-c="all" onclick="sf('all',this)">すべて</button>
  {cat_tabs}
</div>
<div class="grid">{"".join(blocks)}</div>
<button id="top" onclick="window.scrollTo({{top:0,behavior:'smooth'}})">↑</button>
<script>
function sf(c,btn){{
  document.querySelectorAll('.fb').forEach(b=>b.classList.remove('act'));
  btn.classList.add('act');
  document.querySelectorAll('.sb').forEach(b=>b.style.display=(c==='all'||b.dataset.c===c)?'':'none');
}}
window.addEventListener('scroll',()=>document.getElementById('top').classList.toggle('show',scrollY>300));
</script>
</body>
</html>'''

def main():
    print(f"RSS取得開始: {len(SITES)}サイト")
    results = {}
    def fetch_one(site):
        try:
            items = fetch_rss(site)
            print(f"  ✓ {site['name']} ({len(items)}件)")
            return site["name"], items
        except Exception as e:
            print(f"  ✗ {site['name']}: {e}")
            return site["name"], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        for name, items in ex.map(fetch_one, SITES):
            results[name] = items
    os.makedirs("docs", exist_ok=True)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(build_html(results))
    ok = sum(1 for v in results.values() if v)
    print(f"\n完了: {ok}/{len(SITES)}サイト取得成功")

if __name__ == "__main__":
    main()
