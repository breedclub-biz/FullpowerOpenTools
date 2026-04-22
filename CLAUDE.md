# FullpowerOpenTools

FULLPOWER秋葉原店の**公開向け**コンテンツとツールを管理する Public リポジトリ。

関連する非公開業務ツール・ドキュメントは `breedclub-biz/fullpower`（Private）側に分離している。

- **リポジトリ分離方針・GitHubプラン運用**：`~/dev/claude-config/memory/policy_repos_and_publication.md`（横断memory）
- **judge-qa の公開継続判断・DMCA撤退プラン**：`memory/judge_qa_publication.md`（本リポジトリ内）

---

## 構成

### `judge-qa/` - 判定QAツール

デュエル・マスターズの裁定Q&Aを検索・表示する静的Webツール。

- **公開URL**: https://breedclub-biz.github.io/FullpowerOpenTools/judge-qa/
- **旧URL（失効）**: https://breedclub-biz.github.io/fullpower/tools/judge-qa/（2026-04-17 移行前）
- **データ更新**: GitHub Actions で週次（日曜夜）と月次（月初）に Takara Tomy 公式サイトから自動スクレイピング
  - ワークフロー: `.github/workflows/update-judge-qa.yml`
  - 週次：追加のみ取り込み
  - 月次：変更・削除も反映
- **スタッフ向けガイド**: https://docs.google.com/document/d/1CXycye42qYNYhrDzhduQw3IrilcRwT1fBDrqBbxy6AQ/edit

### `kaitori/` - 買取LP

デュエマカードの買取受付ランディングページ。

- **公開URL**: https://breedclub-biz.github.io/FullpowerOpenTools/kaitori/
- **旧パス（失効）**: `fullpower/lp/kaitori/`（2026-04-17 移行前）

#### 未完了タスク

1. **ドメイン取得後の公開マッピング**: `fullpower.tokyo`（または取得ドメイン）を本リポジトリの GitHub Pages にマップし、ルート or `/kaitori/` パスで公開する
2. **残りのカード画像を用意** して `kaitori/images/` フォルダに追加・push
3. **ヘッダー画像の差し替え**: 現在テキスト「WANTED」表示。デザイナーに正式なヘッダー画像を依頼して差し替える
4. **フッター更新**: 店舗情報・SNSリンク（LINE、X）・免責文を正式なものに更新する
5. **トップページへの戻りリンクを追加**

いずれもドメイン取得・画像素材・デザイン外注が未完了のため保留中。

---

## 作業履歴について

作業履歴はこのファイルには記録しない。`git log` を正とする。
CLAUDE.md にはプロジェクト構成・仕様・方針など、コードや git 履歴から読み取りにくい情報のみ記載する。
