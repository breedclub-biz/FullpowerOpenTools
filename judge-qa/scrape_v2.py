import requests
from bs4 import BeautifulSoup
import json
import time
import sys

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
BASE_URL = "https://dm.takaratomy.co.jp/rule/qa/"

# stdout即時出力
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

print("=== QAデータ収集 v2 ===", flush=True)

# Step 1: URL収集
print("\n【Step 1】URL収集中...", flush=True)
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
            print("  → 新規QAなし、終了", flush=True)
            break
        time.sleep(0.4)
    except Exception as e:
        print(f"  ページ {page}: エラー {e}", flush=True)
        time.sleep(2)
        continue

print(f"\nURL収集完了: {len(urls)}件\n", flush=True)

# Step 2: 詳細取得
print("【Step 2】詳細取得中...", flush=True)
qa_data = []
errors = 0

for i, url in enumerate(urls):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            errors += 1
            if (i+1) % 50 == 0:
                print(f"  {i+1}/{len(urls)} (OK:{len(qa_data)} NG:{errors})", flush=True)
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
    except Exception as e:
        errors += 1

    if (i+1) % 50 == 0:
        print(f"  {i+1}/{len(urls)} (OK:{len(qa_data)} NG:{errors})", flush=True)
    time.sleep(0.3)

print(f"\n取得完了: {len(qa_data)}件 (エラー:{errors}件)", flush=True)

with open("qa_data.json", "w", encoding="utf-8") as f:
    json.dump(qa_data, f, ensure_ascii=False, indent=2)

print(f"保存完了: qa_data.json ({len(qa_data)}件)", flush=True)
