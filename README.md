# jma_weather_report

気象庁（JMA）APIから気象データを取得し、GitHub上にレポートとして自動公開するプロジェクト。

## 概要

- 気象庁の公開APIから各地の天気・気温・降水量などのデータを取得
- Markdownレポートを自動生成
- GitHub Actions により定期実行し、`reports/` ディレクトリにコミット
- GitHub Pages または README への埋め込みで閲覧可能

## ディレクトリ構成

```
jma_weather_report/
├── src/                    # Pythonスクリプト群
│   ├── fetch_weather.py    # JMA APIからデータ取得
│   ├── generate_report.py  # Markdownレポート生成
│   └── utils.py            # 共通ユーティリティ
├── data/                   # 取得した生データ（JSON）
│   └── .gitkeep
├── reports/                # 生成されたMarkdownレポート
│   └── .gitkeep
├── .github/
│   └── workflows/
│       └── daily_report.yml  # GitHub Actions 定期実行設定
├── config.json             # 対象地域・項目の設定
├── requirements.txt        # Python依存パッケージ
└── README.md
```

## セットアップ

### 必要環境

- Python 3.x
- pip パッケージ（`requirements.txt` 参照）

### インストール

```bash
pip install -r requirements.txt
```

### 手動実行

```bash
# データ取得
python src/fetch_weather.py

# レポート生成
python src/generate_report.py
```

## 自動実行（GitHub Actions）

`.github/workflows/daily_report.yml` により、毎朝 6:00 JST に自動実行。

- 気象データ取得 → レポート生成 → `reports/` へコミット

## データソース

- [気象庁 天気予報 API](https://www.jma.go.jp/bosai/forecast/)
- 利用規約: [気象庁ウェブサイト利用規約](https://www.jma.go.jp/jma/kishou/info/coment.html)

## レポート内容（予定）

| 項目 | 内容 |
|---|---|
| 天気予報 | 各地の3日間予報 |
| 気温 | 最高・最低気温 |
| 降水確率 | 時間帯別降水確率 |
| 週間予報 | 1週間の概況 |

## 注意事項

- 気象庁APIの利用規約を遵守する
- データは気象庁の著作物。加工・二次利用の際は出典を明記すること
- APIへの過剰なリクエストを避けるため、取得間隔は適切に設定する
