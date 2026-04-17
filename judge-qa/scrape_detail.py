import requests
from bs4 import BeautifulSoup
import json
import time
import re

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}

# scrape_log.txtから取得済みURLを抽出
print("=== Step 2: QA詳細取得 ===\n")

# ログからURLを再構築（一覧ページから再取得せず、ID範囲で生成）
# まず既にログにあるURL数を確認
with open("scrape_log.txt", "r") as f:
    log = f.read()
match = re.findall(r"累計 (\d+)件", log)
total_from_log = int(match[-1]) if match else 0
print(f"一覧ページから {total_from_log} 件のURLを検出済み\n")

# 一覧ページを再取得してURLを集める（キャッシュ的に高速）
BASE_URL = "https://dm.takaratomy.co.jp/rule/qa/"
urls = []

for page in range(1, 349):  # 取得済み348ページまで
    if page == 1:
        url = BASE_URL
    else:
        url = f"{BASE_URL}page/{page}/"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            continue
        soup = BeautifulSoup(resp.text, "html.parser")
        links = soup.select("a[href*='/rule/qa/']")
        for link in links:
            href = link.get("href", "")
            if "/rule/qa/" in href and href != "/rule/qa/" and "page" not in href:
                full_url = href if href.startswith("http") else f"https://dm.takaratomy.co.jp{href}"
                if full_url not in urls:
                    urls.append(full_url)
    except:
        continue

    if page % 50 == 0:
        print(f"  URL再収集: {page}/348ページ ({len(urls)}件)")
    time.sleep(0.3)

print(f"\nURL収集完了: {len(urls)} 件\n")

# 詳細取得
print("各QAの詳細を取得中...\n")
qa_data = []
errors = 0

for i, url in enumerate(urls):
    if (i + 1) % 100 == 0:
        print(f"  {i+1}/{len(urls)} 件処理中... (エラー: {errors}件)")

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            errors += 1
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        title_el = soup.select_one("h1, .qa-title, .entry-title")
        title = title_el.get_text(strip=True) if title_el else ""
        content = soup.select_one(".entry-content, .qa-content, article, .post-content, main")
        if not content:
            content = soup.body
        full_text = content.get_text("\n", strip=True) if content else ""
        qa_id = url.rstrip("/").split("/")[-1]

        qa_data.append({
            "id": qa_id,
            "url": url,
            "title": title,
            "text": full_text[:2000],
        })
    except:
        errors += 1

    time.sleep(0.3)

print(f"\n取得完了: {len(qa_data)} 件 (エラー: {errors}件)\n")

with open("qa_data.json", "w", encoding="utf-8") as f:
    json.dump(qa_data, f, ensure_ascii=False, indent=2)

print(f"保存完了: qa_data.json ({len(qa_data)} 件)")
