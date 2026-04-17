#!/usr/bin/env python3
"""
差分スクレイパー
--mode weekly : 新規追加のみ取得（一覧先頭から既存IDが出るまでスキャン）
--mode monthly: 変更検出（サイトマップlastmod）+ 削除検出（全サイトマップスキャン）
"""
import requests
from bs4 import BeautifulSoup
import json
import time
import sys
import argparse
import re
from pathlib import Path
from datetime import date
import xml.etree.ElementTree as ET

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; FPJudgeBot/1.0)"}
QA_BASE = "https://dm.takaratomy.co.jp/rule/qa/"
SITEMAP_BASE = "https://dm.takaratomy.co.jp/sitemap-pt-qa-{year}-{month:02d}.xml"
MAIN_SITEMAP = "https://dm.takaratomy.co.jp/sitemap.xml"

DATA_DIR = Path(__file__).parent
QA_FILE = DATA_DIR / "qa_data_fixed.json"
CARDS_FILE = DATA_DIR / "card_names.json"
META_FILE = DATA_DIR / "data_meta.json"

CARD_PATTERN = re.compile(r'[《≪]([^》≫\n]{2,30})[》≫]')


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def fetch_qa_detail(url):
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    title_el = soup.select_one("h1, .entry-title")
    title = title_el.get_text(strip=True) if title_el else ""
    content = soup.select_one(".entry-content, article, main") or soup.body
    text = content.get_text("\n", strip=True) if content else ""
    qa_id = url.rstrip("/").split("/")[-1]
    return {"id": qa_id, "url": url, "title": title, "text": text[:2000]}


def collect_new_urls(existing_ids):
    """一覧ページを先頭からスキャンして新規URLを収集（既存IDが出たら停止）"""
    new_urls = []
    seen = set()

    for page in range(1, 400):
        url = QA_BASE if page == 1 else f"{QA_BASE}page/{page}/"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                print(f"  ページ{page}: HTTP {resp.status_code} → 終了", flush=True)
                break
        except Exception as e:
            print(f"  ページ{page}: エラー {e}", flush=True)
            time.sleep(2)
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        links = soup.select("a[href*='/rule/qa/']")

        stop = False
        for link in links:
            href = link.get("href", "")
            if "/rule/qa/" not in href or href == "/rule/qa/" or "page" in href:
                continue
            full_url = href if href.startswith("http") else f"https://dm.takaratomy.co.jp{href}"
            qa_id = full_url.rstrip("/").split("/")[-1]
            if qa_id in existing_ids:
                stop = True
                break
            if qa_id not in seen:
                seen.add(qa_id)
                new_urls.append(full_url)

        print(f"  ページ{page}: 新規{len(new_urls)}件累計", flush=True)
        if stop:
            print("  既存IDを検出 → スキャン終了", flush=True)
            break
        time.sleep(0.4)

    return new_urls


def detect_changes_via_sitemap(existing_ids, since_date):
    """サイトマップのlastmodが since_date 以降のQAページを検出"""
    changed_urls = []
    today = date.today()

    months_to_check = [(today.year, today.month)]
    if today.month == 1:
        months_to_check.append((today.year - 1, 12))
    else:
        months_to_check.append((today.year, today.month - 1))

    ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    for year, month in months_to_check:
        sitemap_url = SITEMAP_BASE.format(year=year, month=month)
        print(f"  サイトマップ: {sitemap_url}", flush=True)
        try:
            resp = requests.get(sitemap_url, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                print(f"  → {resp.status_code}", flush=True)
                continue
            root = ET.fromstring(resp.content)
            count = 0
            for url_el in root.findall('sm:url', ns):
                loc = url_el.findtext('sm:loc', namespaces=ns) or ""
                lastmod = url_el.findtext('sm:lastmod', namespaces=ns) or ""
                if '/rule/qa/' not in loc:
                    continue
                qa_id = loc.rstrip('/').split('/')[-1]
                if qa_id not in existing_ids:
                    continue
                if lastmod[:10] >= since_date:
                    changed_urls.append(loc)
                    count += 1
            print(f"  → 変更候補 {count}件", flush=True)
        except Exception as e:
            print(f"  エラー: {e}", flush=True)
        time.sleep(0.3)

    return changed_urls


def collect_all_site_ids():
    """全サイトマップから全QA IDを収集（削除検出用）"""
    all_ids = set()
    ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

    try:
        resp = requests.get(MAIN_SITEMAP, headers=HEADERS, timeout=15)
        root = ET.fromstring(resp.content)
        qa_sitemaps = [
            el.findtext('sm:loc', namespaces=ns)
            for el in root.findall('sm:sitemap', ns)
            if 'sitemap-pt-qa-' in (el.findtext('sm:loc', namespaces=ns) or '')
        ]
    except Exception as e:
        print(f"メインサイトマップエラー: {e}", flush=True)
        return all_ids

    print(f"  QAサイトマップ: {len(qa_sitemaps)}件", flush=True)
    for sitemap_url in qa_sitemaps:
        try:
            resp = requests.get(sitemap_url, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                continue
            root = ET.fromstring(resp.content)
            for url_el in root.findall('sm:url', ns):
                loc = url_el.findtext('sm:loc', namespaces=ns) or ""
                if '/rule/qa/' in loc:
                    all_ids.add(loc.rstrip('/').split('/')[-1])
            time.sleep(0.2)
        except Exception:
            continue

    return all_ids


def update_card_names(qa_data):
    """QAデータからカード名を抽出してcard_names.jsonを更新"""
    names = set()
    for item in qa_data:
        for text in [item.get('title', ''), item.get('text', '')]:
            for m in CARD_PATTERN.findall(text):
                if len(m.strip()) >= 2:
                    names.add(m.strip())

    existing = set(load_json(CARDS_FILE)) if CARDS_FILE.exists() else set()
    merged = sorted(existing | names)
    save_json(CARDS_FILE, merged)
    return len(merged)


def run_weekly():
    print("=== 週次差分更新 ===", flush=True)
    qa_data = load_json(QA_FILE)
    existing_ids = {item["id"] for item in qa_data}
    print(f"既存: {len(qa_data)}件")

    print("\n【新規URL収集】", flush=True)
    new_urls = collect_new_urls(existing_ids)
    print(f"新規URL: {len(new_urls)}件", flush=True)

    if not new_urls:
        print("新規QAなし → 終了")
        return False

    print(f"\n【詳細取得】 {len(new_urls)}件", flush=True)
    new_items = []
    errors = 0
    for i, url in enumerate(new_urls):
        try:
            item = fetch_qa_detail(url)
            new_items.append(item)
            print(f"  [{i+1}/{len(new_urls)}] #{item['id']}", flush=True)
        except Exception as e:
            errors += 1
            print(f"  [{i+1}/{len(new_urls)}] エラー: {e}", flush=True)
        time.sleep(0.3)

    # 新しいものを先頭に追加
    qa_data = new_items + qa_data
    save_json(QA_FILE, qa_data)

    card_count = update_card_names(qa_data)
    print(f"\n完了: {len(qa_data)}件 (+{len(new_items)}件, エラー:{errors}件)", flush=True)
    print(f"カード名: {card_count}件", flush=True)
    return True


def run_monthly():
    print("=== 月次更新（変更・削除検出） ===", flush=True)
    qa_data = load_json(QA_FILE)
    existing_ids = {item["id"] for item in qa_data}
    id_to_item = {item["id"]: item for item in qa_data}

    meta = load_json(META_FILE) if META_FILE.exists() else {}
    since_date = meta.get("last_monthly", "2020-01-01")
    print(f"既存: {len(qa_data)}件 / 前回月次実行: {since_date}", flush=True)

    # 変更検出
    print(f"\n【変更検出】since {since_date}", flush=True)
    changed_urls = detect_changes_via_sitemap(existing_ids, since_date)
    changed_count = 0
    for url in changed_urls:
        try:
            item = fetch_qa_detail(url)
            old = id_to_item.get(item["id"], {})
            if old.get("title") != item["title"] or old.get("text") != item["text"]:
                id_to_item[item["id"]] = item
                changed_count += 1
                print(f"  更新: #{item['id']}", flush=True)
            time.sleep(0.3)
        except Exception as e:
            print(f"  エラー ({url}): {e}", flush=True)

    # 削除検出
    print("\n【削除検出】（全サイトマップスキャン）", flush=True)
    site_ids = collect_all_site_ids()
    deleted_ids = existing_ids - site_ids
    if deleted_ids:
        print(f"削除: {deleted_ids}", flush=True)
    else:
        print("削除なし", flush=True)

    # 保存
    qa_data = [id_to_item[i] for i in id_to_item if i not in deleted_ids]
    save_json(QA_FILE, qa_data)

    # メタデータ更新
    meta["last_monthly"] = date.today().isoformat()
    save_json(META_FILE, meta)

    card_count = update_card_names(qa_data)
    print(f"\n完了: {len(qa_data)}件 (変更:{changed_count}件, 削除:{len(deleted_ids)}件)", flush=True)
    print(f"カード名: {card_count}件", flush=True)
    return changed_count > 0 or len(deleted_ids) > 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="デュエルマスターズQA差分スクレイパー")
    parser.add_argument("--mode", choices=["weekly", "monthly"], default="weekly")
    args = parser.parse_args()

    if args.mode == "monthly":
        run_monthly()
    else:
        run_weekly()
