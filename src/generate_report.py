"""
取得済み気象データからMarkdownレポートを生成するスクリプト
"""
import json
import os
import sys
from datetime import datetime
from utils import (
    now_jst,
    parse_jst,
    format_date_jp,
    format_time_jp,
    weather_code_to_text,
    weather_code_to_emoji,
    JST,
)


def load_config(config_path: str) -> dict:
    """設定ファイルを読み込む"""
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_area_data(data_dir: str, area_code: str, date_str: str) -> dict:
    """指定日のエリアデータを読み込む"""
    filename = f"{date_str}_{area_code}.json"
    filepath = os.path.join(data_dir, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


# ──────────────────────────────────────────────
# 短期予報パーサー（3日間）
# ──────────────────────────────────────────────

def parse_short_forecast(forecast_data: list) -> dict:
    """
    data[0]（短期予報）を解析して構造化データを返す

    Returns:
        {
            "publish_time": str,
            "office": str,
            "weather_days": [
                {
                    "date": datetime,
                    "weather_code": str,
                    "weather_text": str,
                    "emoji": str,
                    "wind": str,
                    "wave": str,
                }
            ],
            "pop_slots": [
                {"time_start": datetime, "pop": str}
            ],
            "temp_slots": [
                {"time": datetime, "temp": str}
            ],
        }
    """
    short = forecast_data[0]
    result = {
        "publish_time": short.get("reportDatetime", ""),
        "office": short.get("publishingOffice", ""),
        "weather_days": [],
        "pop_slots": [],
        "temp_slots": [],
    }

    time_series = short.get("timeSeries", [])

    # ── 天気・風・波（timeSeries[0]）
    if len(time_series) > 0:
        ts0 = time_series[0]
        defines = ts0.get("timeDefines", [])
        for area in ts0.get("areas", []):
            weathers = area.get("weathers", [])
            codes = area.get("weatherCodes", [])
            winds = area.get("winds", [])
            waves = area.get("waves", [])
            for i, t in enumerate(defines):
                dt = parse_jst(t)
                code = str(codes[i]) if i < len(codes) else ""
                result["weather_days"].append({
                    "date": dt,
                    "weather_code": code,
                    "weather_text": weather_code_to_text(code),
                    "emoji": weather_code_to_emoji(code),
                    "wind": winds[i] if i < len(winds) else "",
                    "wave": waves[i] if i < len(waves) else "",
                })
            break  # 最初のエリアのみ使用

    # ── 降水確率（timeSeries[1]）
    if len(time_series) > 1:
        ts1 = time_series[1]
        defines = ts1.get("timeDefines", [])
        for area in ts1.get("areas", []):
            pops = area.get("pops", [])
            for i, t in enumerate(defines):
                dt = parse_jst(t)
                result["pop_slots"].append({
                    "time_start": dt,
                    "pop": pops[i] if i < len(pops) else "--",
                })
            break

    # ── 気温（timeSeries[2]）
    if len(time_series) > 2:
        ts2 = time_series[2]
        defines = ts2.get("timeDefines", [])
        for area in ts2.get("areas", []):
            temps = area.get("temps", [])
            for i, t in enumerate(defines):
                dt = parse_jst(t)
                result["temp_slots"].append({
                    "time": dt,
                    "temp": temps[i] if i < len(temps) else "--",
                })
            break

    return result


# ──────────────────────────────────────────────
# 週間予報パーサー
# ──────────────────────────────────────────────

def parse_weekly_forecast(forecast_data: list) -> dict:
    """
    data[1]（週間予報）を解析して構造化データを返す

    Returns:
        {
            "weekly_days": [
                {
                    "date": datetime,
                    "weather_code": str,
                    "weather_text": str,
                    "emoji": str,
                    "pop": str,
                    "temp_min": str,
                    "temp_max": str,
                }
            ]
        }
    """
    result = {"weekly_days": []}
    if len(forecast_data) < 2:
        return result

    weekly = forecast_data[1]
    time_series = weekly.get("timeSeries", [])

    # ── 天気コード・降水確率（timeSeries[0]）
    weather_by_date: dict[str, dict] = {}
    if len(time_series) > 0:
        ts0 = time_series[0]
        defines = ts0.get("timeDefines", [])
        for area in ts0.get("areas", []):
            codes = area.get("weatherCodes", [])
            pops = area.get("pops", [])
            for i, t in enumerate(defines):
                dt = parse_jst(t)
                key = dt.strftime("%Y-%m-%d")
                code = str(codes[i]) if i < len(codes) else ""
                weather_by_date[key] = {
                    "date": dt,
                    "weather_code": code,
                    "weather_text": weather_code_to_text(code),
                    "emoji": weather_code_to_emoji(code),
                    "pop": pops[i] if i < len(pops) else "--",
                    "temp_min": "--",
                    "temp_max": "--",
                }
            break

    # ── 気温（timeSeries[1]）
    if len(time_series) > 1:
        ts1 = time_series[1]
        defines = ts1.get("timeDefines", [])
        for area in ts1.get("areas", []):
            temps_min = area.get("tempsMin", [])
            temps_max = area.get("tempsMax", [])
            for i, t in enumerate(defines):
                dt = parse_jst(t)
                key = dt.strftime("%Y-%m-%d")
                if key in weather_by_date:
                    weather_by_date[key]["temp_min"] = temps_min[i] if i < len(temps_min) else "--"
                    weather_by_date[key]["temp_max"] = temps_max[i] if i < len(temps_max) else "--"
            break

    result["weekly_days"] = sorted(weather_by_date.values(), key=lambda d: d["date"])
    return result


# ──────────────────────────────────────────────
# Markdownレポート生成
# ──────────────────────────────────────────────

def build_markdown(
    area_name: str,
    generated_at: datetime,
    short: dict,
    weekly: dict,
    overview_text: str,
) -> str:
    """
    パース済みデータからMarkdown文字列を生成する
    """
    lines = []

    # ── ヘッダー
    pub_dt = parse_jst(short["publish_time"]) if short["publish_time"] else generated_at
    lines.append(f"# {area_name} 天気予報レポート")
    lines.append("")
    lines.append(f"**発表日時**: {format_date_jp(pub_dt)} {format_time_jp(pub_dt)}  ")
    lines.append(f"**発表官庁**: {short['office']}  ")
    lines.append(f"**レポート生成**: {generated_at.strftime('%Y-%m-%d %H:%M')} JST  ")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── 概況テキスト
    if overview_text:
        lines.append("## 概況")
        lines.append("")
        lines.append(overview_text)
        lines.append("")
        lines.append("---")
        lines.append("")

    # ── 3日間予報
    lines.append("## 3日間の天気予報")
    lines.append("")
    if short["weather_days"]:
        lines.append("| 日付 | 天気 | 風 | 波 |")
        lines.append("|---|---|---|---|")
        for day in short["weather_days"]:
            date_str = format_date_jp(day["date"])
            weather = f"{day['emoji']} {day['weather_text']}"
            wind = day["wind"] or "--"
            wave = day["wave"] or "--"
            lines.append(f"| {date_str} | {weather} | {wind} | {wave} |")
    else:
        lines.append("※ データなし")
    lines.append("")

    # ── 降水確率（6時間ごと）
    lines.append("## 降水確率（6時間ごと）")
    lines.append("")
    if short["pop_slots"]:
        # 日付ごとにグループ化して表示
        by_date: dict[str, list] = {}
        for slot in short["pop_slots"]:
            date_key = slot["time_start"].strftime("%Y-%m-%d")
            by_date.setdefault(date_key, []).append(slot)

        for date_key, slots in by_date.items():
            dt0 = slots[0]["time_start"]
            lines.append(f"**{format_date_jp(dt0)}**")
            lines.append("")
            header = "| " + " | ".join(format_time_jp(s["time_start"]) for s in slots) + " |"
            separator = "| " + " | ".join("---" for _ in slots) + " |"
            values = "| " + " | ".join(f"{s['pop']}%" for s in slots) + " |"
            lines.append(header)
            lines.append(separator)
            lines.append(values)
            lines.append("")
    else:
        lines.append("※ データなし")
        lines.append("")

    # ── 気温
    lines.append("## 気温")
    lines.append("")
    if short["temp_slots"]:
        lines.append("| 日時 | 気温 |")
        lines.append("|---|---|")
        for slot in short["temp_slots"]:
            dt_str = f"{format_date_jp(slot['time'])} {format_time_jp(slot['time'])}"
            temp = slot["temp"]
            temp_str = f"{temp}°C" if temp not in ("--", "") else "--"
            lines.append(f"| {dt_str} | {temp_str} |")
    else:
        lines.append("※ データなし")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── 週間予報
    lines.append("## 週間天気予報")
    lines.append("")
    if weekly["weekly_days"]:
        lines.append("| 日付 | 天気 | 降水確率 | 最低気温 | 最高気温 |")
        lines.append("|---|---|---|---|---|")
        for day in weekly["weekly_days"]:
            date_str = format_date_jp(day["date"])
            weather = f"{day['emoji']} {day['weather_text']}"
            pop = f"{day['pop']}%" if day["pop"] not in ("--", "") else "--"
            temp_min = f"{day['temp_min']}°C" if day["temp_min"] not in ("--", "") else "--"
            temp_max = f"{day['temp_max']}°C" if day["temp_max"] not in ("--", "") else "--"
            lines.append(f"| {date_str} | {weather} | {pop} | {temp_min} | {temp_max} |")
    else:
        lines.append("※ データなし")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── フッター
    lines.append("*データソース: [気象庁](https://www.jma.go.jp/) / 利用規約に基づき出典を明記*")
    lines.append("")

    return "\n".join(lines)


def update_readme(content: str, readme_path: str) -> None:
    """
    README.md のマーカー間に最新レポートを埋め込む
    <!-- WEATHER_REPORT_START --> と <!-- WEATHER_REPORT_END --> の間を置き換える
    """
    start_marker = "<!-- WEATHER_REPORT_START -->"
    end_marker = "<!-- WEATHER_REPORT_END -->"

    with open(readme_path, "r", encoding="utf-8") as f:
        readme = f.read()

    start_idx = readme.find(start_marker)
    end_idx = readme.find(end_marker)
    if start_idx == -1 or end_idx == -1:
        print("  README.md にマーカーが見つかりません。スキップします。")
        return

    new_section = f"{start_marker}\n{content}\n{end_marker}"
    updated = readme[: start_idx] + new_section + readme[end_idx + len(end_marker) :]

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(updated)


def save_report(content: str, output_dir: str, date_str: str, latest_filename: str) -> tuple[str, str]:
    """
    Markdownレポートを保存する（日付ファイル＋latest）

    Returns:
        (日付ファイルパス, latestファイルパス)
    """
    os.makedirs(output_dir, exist_ok=True)

    dated_path = os.path.join(output_dir, f"{date_str}.md")
    latest_path = os.path.join(output_dir, latest_filename)

    with open(dated_path, "w", encoding="utf-8") as f:
        f.write(content)
    with open(latest_path, "w", encoding="utf-8") as f:
        f.write(content)

    return dated_path, latest_path


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    config_path = os.path.join(project_root, "config.json")
    config = load_config(config_path)

    data_dir = os.path.join(project_root, config["report"]["data_dir"])
    report_dir = os.path.join(project_root, config["report"]["output_dir"])
    latest_filename = config["report"]["latest_filename"]

    now = now_jst()
    today = now.strftime("%Y-%m-%d")

    print(f"=== レポート生成開始 ({today}) ===")

    for area in config["areas"]:
        code = area["code"]
        name = area["name"]
        print(f"\n[{name} ({code})]")

        try:
            raw = load_area_data(data_dir, code, today)
        except FileNotFoundError:
            print(f"  データファイルが見つかりません。先に fetch_weather.py を実行してください。", file=sys.stderr)
            sys.exit(1)

        forecast_data = raw["forecast"]
        overview_text = raw["overview"].get("text", "")

        short = parse_short_forecast(forecast_data)
        weekly = parse_weekly_forecast(forecast_data)

        md = build_markdown(name, now, short, weekly, overview_text)

        dated_path, latest_path = save_report(md, report_dir, today, latest_filename)
        print(f"  保存完了: {dated_path}")
        print(f"  最新版:   {latest_path}")

        readme_path = os.path.join(project_root, "README.md")
        if os.path.exists(readme_path):
            update_readme(md, readme_path)
            print(f"  README更新: {readme_path}")

    print(f"\n=== レポート生成完了 ===")


if __name__ == "__main__":
    main()
