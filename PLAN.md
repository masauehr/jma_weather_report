# PLAN.md — jma_weather_report 実装計画

最終更新: 2026-03-26（フェーズ1〜4 実装完了）

## プロジェクト目標

気象庁APIから気象データを定期取得し、GitHub上にMarkdownレポートとして自動公開する仕組みを構築する。

---

## フェーズ1：環境構築・データ取得（優先）

### タスク1-1: プロジェクト初期化
- [x] ディレクトリ構成作成
- [x] README.md / PLAN.md 作成
- [x] `requirements.txt` 作成（requests）
- [x] `config.json` 作成（沖縄本島地方: 471000）
- [x] `.gitignore` 作成

### タスク1-2: JMA APIデータ取得スクリプト
- [x] `src/fetch_weather.py` 実装
  - 対象: 沖縄本島地方（471000）
  - エンドポイント: forecast + overview_forecast
  - 出力: `data/YYYY-MM-DD_471000.json`

### タスク1-3: ユーティリティ整備
- [x] `src/utils.py` 実装
  - 日付フォーマット変換（日本語曜日付き）
  - 天気コード → テキスト変換（TELOPS完全マッピング）
  - 天気コード → 絵文字変換

---

## フェーズ2：レポート生成

### タスク2-1: Markdownレポート生成スクリプト
- [x] `src/generate_report.py` 実装
  - `data/` の最新JSONを読み込む
  - Markdown生成
  - 出力: `reports/YYYY-MM-DD.md`

### タスク2-2: レポートテンプレート設計
- [x] 日次レポートの構成を決定
  - ヘッダー（発表日時・官庁・生成時刻）
  - 概況テキスト
  - 3日間天気予報テーブル（天気・風・波）
  - 降水確率（6時間ごと・日付別）
  - 気温テーブル
  - 週間予報テーブル（最低・最高気温）
- [x] `reports/latest.md` として最新を常に上書き保存

---

## フェーズ3：GitHub Actions 自動化

### タスク3-1: ワークフロー設定
- [x] `.github/workflows/daily_report.yml` 実装
  - スケジュール: 毎日 20:30 UTC（翌朝 5:30 JST）
  - ステップ: checkout → Python 3.11 セットアップ → fetch → generate → commit & push
  - `workflow_dispatch` で手動実行にも対応

### タスク3-2: GitHub リポジトリ設定
- [ ] リポジトリ作成（`jma_weather_report`）
- [ ] Actions の write 権限設定（contents: write）
- [ ] Secrets 設定（今回は不要 / GITHUB_TOKEN のみ）

---

## フェーズ4：拡張（後回し）

- [ ] 対象地域の追加（全国主要都市）
- [ ] グラフ画像の生成（matplotlib）
- [ ] GitHub Pages でのレポート公開
- [ ] 異常気象アラートの検知・通知
- [ ] 週次・月次サマリーレポート

---

## 技術スタック

| 項目 | 採用技術 | 理由 |
|---|---|---|
| 言語 | Python 3.x | 既存プロジェクトとの統一 |
| HTTPクライアント | requests | シンプル・実績あり |
| テンプレート | Jinja2 または f-string | 軽量構成優先 |
| CI/CD | GitHub Actions | 無料・設定容易 |
| データ保存 | JSON（生データ）+ Markdown（レポート） | バージョン管理しやすい |

---

## 参考: JMA APIエンドポイント

| API | URL |
|---|---|
| 天気予報 | `https://www.jma.go.jp/bosai/forecast/data/forecast/{area_code}.json` |
| エリア一覧 | `https://www.jma.go.jp/bosai/common/const/area.json` |
| 概況テキスト | `https://www.jma.go.jp/bosai/forecast/data/overview_forecast/{area_code}.json` |
| 観測データ | `https://www.jma.go.jp/bosai/amedas/data/latest_time.txt` |
