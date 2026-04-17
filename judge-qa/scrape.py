import requests
from bs4 import BeautifulSoup
import json
import time
import sys

BASE_URL = "https://dm.takaratomy.co.jp/rule/qa/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}

def get_qa_list_urls():
    """全ページからQA個別ページのURLを収集"""
    urls = []
    page = 1
    while True:
        if page == 1:
            url = BASE_URL
        else:
            url = f"{BASE_URL}page/{page}/"

        print(f"一覧ページ {page} を取得中...", end=" ", flush=True)
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                print(f"終了 (status {resp.status_code})")
                break

            soup = BeautifulSoup(resp.text, "html.parser")
            links = soup.select("a[href*='/rule/qa/']")

            page_urls = []
            for link in links:
                href = link.get("href", "")
                if "/rule/qa/" in href and href != "/rule/qa/" and "page" not in href:
                    full_url = href if href.startswith("http") else f"https://dm.takaratomy.co.jp{href}"
                    if full_url not in urls and full_url not in page_urls:
                        page_urls.append(full_url)

            if not page_urls:
                print("QAリンクなし、終了")
                break

            urls.extend(page_urls)
            print(f"{len(page_urls)}件発見 (累計 {len(urls)}件)")

            page += 1
            time.sleep(0.5)

        except Exception as e:
            print(f"エラー: {e}")
            break

    return urls

def get_qa_detail(url):
    """個別QAページから質問・回答を抽出"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        # タイトル/質問
        title_el = soup.select_one("h1, .qa-title, .entry-title")
        title = title_el.get_text(strip=True) if title_el else ""

        # 本文からQ&Aを抽出
        content = soup.select_one(".entry-content, .qa-content, article, .post-content, main")
        if not content:
            content = soup.body

        full_text = content.get_text("\n", strip=True) if content else ""

        # QA IDを抽出
        qa_id = url.rstrip("/").split("/")[-1]

        return {
            "id": qa_id,
            "url": url,
            "title": title,
            "text": full_text[:2000],  # 長すぎる場合は切り詰め
        }
    except Exception as e:
        return None

def main():
    print("=== FULLPOWER ジャッジAI - QAデータ収集 ===\n")

    # Step 1: URL収集
    print("【Step 1】QA一覧からURLを収集中...\n")
    urls = get_qa_list_urls()
    print(f"\n合計 {len(urls)} 件のQAを発見\n")

    if not urls:
        print("URLが取得できませんでした")
        sys.exit(1)

    # Step 2: 各QAの詳細を取得
    print("【Step 2】各QAの詳細を取得中...\n")
    qa_data = []
    for i, url in enumerate(urls):
        if (i + 1) % 50 == 0 or i == 0:
            print(f"  {i+1}/{len(urls)} 件処理中...")

        detail = get_qa_detail(url)
        if detail:
            qa_data.append(detail)

        time.sleep(0.3)  # サーバー負荷軽減

    print(f"\n合計 {len(qa_data)} 件のQAを取得完了\n")

    # Step 3: JSON保存
    output_path = "qa_data.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(qa_data, f, ensure_ascii=False, indent=2)

    print(f"保存完了: {output_path} ({len(qa_data)} 件)")

if __name__ == "__main__":
    main()
