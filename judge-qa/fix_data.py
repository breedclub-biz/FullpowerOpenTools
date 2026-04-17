import requests
from bs4 import BeautifulSoup
import json
import time
import sys

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

# 既存データからURLを取得
with open("qa_data.json", "r") as f:
    old_data = json.load(f)

urls = [q["url"] for q in old_data]
print(f"既存 {len(urls)} 件のURLからQA本文を再取得します\n", flush=True)

qa_data = []
errors = 0

for i, url in enumerate(urls):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            errors += 1
            continue

        soup = BeautifulSoup(resp.text, "html.parser")

        # mainContent内を取得
        main = soup.select_one("#mainContent")
        if not main:
            main = soup

        # Q&Aテキストを抽出（qabox01やsection内）
        qa_section = main.select_one(".qabox01, section, .qa-content")
        if not qa_section:
            qa_section = main

        # 質問（h2）と回答（p）を個別に取得
        q_text = ""
        a_text = ""

        # h2タグから質問を探す
        h2s = qa_section.select("h2")
        for h2 in h2s:
            text = h2.get_text(strip=True)
            if text and len(text) > 5 and "よくある質問" not in text:
                q_text = text
                break

        # h2が空の場合、最初の長いテキストブロックを使う
        if not q_text:
            for el in qa_section.select("p, div"):
                text = el.get_text(strip=True)
                if len(text) > 20 and "検索" not in text and "メニュー" not in text:
                    q_text = text
                    break

        # 全体テキスト（ナビ除外）
        # ナビやフッターを除外
        for nav in main.select("nav, header, footer, .gnav, .header, .footer"):
            nav.decompose()

        full_text = main.get_text("\n", strip=True)

        # 「Q」「A」パターンで分割を試みる
        lines = full_text.split("\n")
        clean_lines = [l for l in lines if l.strip() and
                       "検索" not in l and "メニュー" not in l and
                       "キーワード" not in l and "English" not in l and
                       "おもちゃ" not in l and "ブランド" not in l and
                       "ジャンル" not in l and "トップページ" not in l and
                       "商品情報" not in l and len(l.strip()) > 2]

        qa_id = url.rstrip("/").split("/")[-1]
        clean_text = "\n".join(clean_lines[:30])  # 最大30行

        qa_data.append({
            "id": qa_id,
            "url": url,
            "title": q_text[:200],
            "text": clean_text[:2000],
        })

    except Exception as e:
        errors += 1

    if (i + 1) % 50 == 0:
        print(f"  {i+1}/{len(urls)} (OK:{len(qa_data)} NG:{errors})", flush=True)
        with open("qa_data_fixed.json", "w", encoding="utf-8") as f:
            json.dump(qa_data, f, ensure_ascii=False, indent=2)

    time.sleep(0.3)

with open("qa_data_fixed.json", "w", encoding="utf-8") as f:
    json.dump(qa_data, f, ensure_ascii=False, indent=2)

print(f"\n完了: {len(qa_data)}件 (エラー:{errors}件)", flush=True)
print(f"保存完了: qa_data_fixed.json", flush=True)

# サンプル表示
if qa_data:
    print(f"\n--- サンプル ---", flush=True)
    print(f"ID: {qa_data[0]['id']}", flush=True)
    print(f"Title: {qa_data[0]['title'][:100]}", flush=True)
    print(f"Text: {qa_data[0]['text'][:300]}", flush=True)
