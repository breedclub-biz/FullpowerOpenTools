import requests
from bs4 import BeautifulSoup
import json
import time
import sys

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

with open("remaining_urls.json", "r") as f:
    urls = json.load(f)
with open("qa_data_fixed.json", "r") as f:
    qa_data = json.load(f)

print(f"既存: {len(qa_data)}件, 残り: {len(urls)}件\n", flush=True)

errors = 0
for i, url in enumerate(urls):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            errors += 1
            continue
        soup = BeautifulSoup(resp.text, "html.parser")
        main = soup.select_one("#mainContent") or soup
        for nav in main.select("nav, header, footer, .gnav, .header, .footer"):
            nav.decompose()

        q_text = ""
        h2s = main.select("h2")
        for h2 in h2s:
            text = h2.get_text(strip=True)
            if text and len(text) > 5 and "よくある質問" not in text:
                q_text = text
                break
        if not q_text:
            for el in main.select("p, div"):
                text = el.get_text(strip=True)
                if len(text) > 20 and "検索" not in text and "メニュー" not in text:
                    q_text = text
                    break

        full_text = main.get_text("\n", strip=True)
        lines = full_text.split("\n")
        clean_lines = [l for l in lines if l.strip() and
                       "検索" not in l and "メニュー" not in l and
                       "キーワード" not in l and "English" not in l and
                       "おもちゃ" not in l and "ブランド" not in l and
                       "ジャンル" not in l and "トップページ" not in l and
                       "商品情報" not in l and len(l.strip()) > 2]

        qa_id = url.rstrip("/").split("/")[-1]
        qa_data.append({
            "id": qa_id, "url": url,
            "title": q_text[:200],
            "text": "\n".join(clean_lines[:30])[:2000],
        })
    except:
        errors += 1

    if (i + 1) % 50 == 0:
        print(f"  {i+1}/{len(urls)} (累計OK:{len(qa_data)} NG:{errors})", flush=True)
        with open("qa_data_fixed.json", "w", encoding="utf-8") as f:
            json.dump(qa_data, f, ensure_ascii=False, indent=2)

    time.sleep(0.3)

with open("qa_data_fixed.json", "w", encoding="utf-8") as f:
    json.dump(qa_data, f, ensure_ascii=False, indent=2)

print(f"\n完了: {len(qa_data)}件 (エラー:{errors}件)", flush=True)
print(f"保存完了: qa_data_fixed.json", flush=True)
