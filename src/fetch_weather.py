"""
JMA APIから気象データを取得してJSONファイルに保存するスクリプト
"""
import json
import os
import sys
import time
import requests
from utils import now_jst

# JMA API ベースURL
FORECAST_BASE_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{area_code}.json"
OVERVIEW_BASE_URL = "https://www.jma.go.jp/bosai/forecast/data/overview_forecast/{area_code}.json"

# リクエスト間隔（秒）- JMA APIへの過剰なリクエストを避けるため
REQUEST_INTERVAL = 1.0


def load_config(config_path: str) -> dict:
    """設定ファイルを読み込む"""
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_json(url: str):
    """指定URLからJSONを取得して返す"""
    headers = {
        "User-Agent": "jma_weather_report/1.0 (https://github.com/; educational use)"
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_area_data(area_code: str) -> dict:
    """
    1エリア分の気象データ（予報＋概況）を取得する

    Args:
        area_code: エリアコード（例: "471000"）

    Returns:
        {
            "forecast": [...],      # 短期予報＋週間予報
            "overview": {...}       # 概況テキスト
        }
    """
    forecast_url = FORECAST_BASE_URL.format(area_code=area_code)
    overview_url = OVERVIEW_BASE_URL.format(area_code=area_code)

    print(f"  予報データ取得中: {forecast_url}")
    forecast = fetch_json(forecast_url)
    time.sleep(REQUEST_INTERVAL)

    print(f"  概況テキスト取得中: {overview_url}")
    overview = fetch_json(overview_url)
    time.sleep(REQUEST_INTERVAL)

    return {
        "forecast": forecast,
        "overview": overview,
    }


def save_data(data: dict, output_dir: str, area_code: str, date_str: str) -> str:
    """
    取得データをJSONファイルに保存する

    Args:
        data: 取得した気象データ
        output_dir: 保存先ディレクトリ
        area_code: エリアコード
        date_str: 日付文字列（YYYY-MM-DD）

    Returns:
        保存したファイルパス
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{date_str}_{area_code}.json"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return filepath


def main():
    # スクリプトのディレクトリを基準にパスを解決
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    config_path = os.path.join(project_root, "config.json")
    config = load_config(config_path)

    data_dir = os.path.join(project_root, config["report"]["data_dir"])
    today = now_jst().strftime("%Y-%m-%d")

    print(f"=== 気象データ取得開始 ({today}) ===")

    results = []
    for area in config["areas"]:
        code = area["code"]
        name = area["name"]
        print(f"\n[{name} ({code})]")

        try:
            data = fetch_area_data(code)
            filepath = save_data(data, data_dir, code, today)
            print(f"  保存完了: {filepath}")
            results.append({"area": area, "filepath": filepath, "status": "ok"})
        except requests.exceptions.RequestException as e:
            print(f"  エラー: {e}", file=sys.stderr)
            results.append({"area": area, "filepath": None, "status": "error", "error": str(e)})

    success = sum(1 for r in results if r["status"] == "ok")
    print(f"\n=== 完了: {success}/{len(results)} エリア取得成功 ===")

    if success == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
