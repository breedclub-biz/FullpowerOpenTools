---
name: judge-qa 公開方針・DMCA撤退プラン
description: judge-qa ツールを Public 公開継続する判断の理由・許容リスク・権利者通知時の撤退手順
type: project
---

## 判定QAツール公開継続の判断

`FullpowerOpenTools/judge-qa/` にタカラトミー公式QAのスクレイプデータ（`qa_data_fixed.json` 10MB等）・スクレイプスクリプトを Public で公開継続中。

**Why:**
- 店内ジャッジ支援という明確な業務価値
- 現実的リスクは訴訟ではなく DMCA takedown（通知 → 対応で完結する想定）
- 運用必要性がリスクを上回るため **意識的に許容** する判断

**How to apply:**
- この方針を前提に判定QA関連作業を進めてよい
- 新たな著作物（PDF等）を追加する場合は公開可否を都度判断
- `dm_rule.pdf` は例外的に Private 側（`fullpower/reference/`）へ退避済み（公式PDFの丸ごと転載となるため）

## DMCA／権利者通知が来た場合の撤退プラン

1. **即座に `FullpowerOpenTools/judge-qa/` を削除 または リポジトリを Private 化**
2. スタッフに判定ツール一時停止を連絡
3. ツール本体＋データを `fullpower`（Private）に退避
4. Team プラン有効なら `fullpower/docs/judge-qa/` で再公開
5. Free維持で再公開する場合は、データ要約化・attribution追加・transformative化を検討

**Why:** 発見時に即応できるよう手順を事前コード化。運用停止時間を最小化する。

**How to apply:** 通知受領時は手順を上から順に即実行。迷ったら「まず非公開化」を最優先。
