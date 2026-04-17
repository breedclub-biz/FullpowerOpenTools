import requests
from bs4 import BeautifulSoup
import json
import time
import sys
import os

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
BASE_URL = "https://dm.takaratomy.co.jp/rule/qa/"
URLS_FILE = "qa_urls.json"
DATA_FILE = "qa_data.json"

sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

# === Step 1: URL収集（キャッシュあれば再利用） ===
if os.path.exists(URLS_FILE):
    with open(URLS_FILE, "r") as f:
        urls = json.load(f)
    print(f"URL一覧をキャッシュから読み込み: {len(urls)}件", flush=True)
else:
    print("【Step 1】URL収集中...", flush=True)
    urls = []
    for page in range(1, 400):
        url = BASE_URL if page == 1 else f"{BASE_URL}page/{page}/"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                print(f"  ページ {page}: status {resp.status_code} → 終了", flush=True)
                break
            soup = BeautifulSoup(resp.text, "html.parser")
            links = soup.select("a[href*='/rule/qa/']")
            count = 0
            for link in links:
                href = link.get("href", "")
                if "/rule/qa/" in href and href != "/rule/qa/" and "page" not in href:
                    full_url = href if href.startswith("http") else f"https://dm.takaratomy.co.jp{href}"
                    if full_url not in urls:
                        urls.append(full_url)
                        count += 1
            print(f"  ページ {page}: +{count}件 (累計{len(urls)}件)", flush=True)
            if count == 0:
                break
            time.sleep(0.4)
        except Exception as e:
            print(f"  ページ {page}: エラー {e}", flush=True)
            time.sleep(2)
            continue

    with open(URLS_FILE, "w") as f:
        json.dump(urls, f, ensure_ascii=False)
    print(f"URL収集完了・保存: {len(urls)}件\n", flush=True)

# === Step 2: 詳細取得（取得済みはスキップ） ===
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        qa_data = json.load(f)
    done_urls = {q["url"] for q in qa_data}
    print(f"既存データ読み込み: {len(qa_data)}件取得済み", flush=True)
else:
    qa_data = []
    done_urls = set()

remaining = [u for u in urls if u not in done_urls]
print(f"残り: {len(remaining)}件\n", flush=True)

if not remaining:
    print("全件取得済みです!", flush=True)
    sys.exit(0)

errors = 0
for i, url in enumerate(remaining):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            errors += 1
            continue
        soup = BeautifulSoup(resp.text, "html.parser")
        title_el = soup.select_one("h1, .entry-title")
        title = title_el.get_text(strip=True) if title_el else ""
        content = soup.select_one(".entry-content, article, main")
        if not content:
            content = soup.body
        full_text = content.get_text("\n", strip=True) if content else ""
        qa_id = url.rstrip("/").split("/")[-1]
        qa_data.append({"id": qa_id, "url": url, "title": title, "text": full_text[:2000]})
    except:
        errors += 1

    # 50件ごとに進捗表示＆中間保存
    if (i + 1) % 50 == 0:
        print(f"  {i+1}/{len(remaining)} (累計OK:{len(qa_data)} NG:{errors})", flush=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(qa_data, f, ensure_ascii=False, indent=2)

    time.sleep(0.3)

# 最終保存
with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(qa_data, f, ensure_ascii=False, indent=2)

print(f"\n完了: {len(qa_data)}件 (エラー:{errors}件)", flush=True)
print(f"保存完了: {DATA_FILE}", flush=True)
