#!/usr/bin/env python3
"""Check Google Trends for interest trajectory related to a product idea.

Uses trendspy to pull interest-over-time data and compute trend slopes.
Returns structured JSON with current interest level and trend direction.
"""

import argparse
import json
import sys
import time

try:
    from trendspy import Trends
except ImportError:
    print(
        json.dumps(
            {
                "error": "trendspy not installed. Run: uv add trendspy",
                "results": None,
            }
        )
    )
    sys.exit(1)


def compute_slope(values):
    if len(values) < 2:
        return 0.0
    n = len(values)
    x_mean = (n - 1) / 2
    y_mean = sum(values) / n
    numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    if denominator == 0:
        return 0.0
    return numerator / denominator


def classify_slope(slope):
    if slope > 0.5:
        return "positive"
    elif slope < -0.5:
        return "negative"
    return "flat"


def get_trends(keywords):
    tr = Trends()
    all_results = {}

    for keyword in keywords:
        keyword = keyword.strip()
        if not keyword:
            continue
        time.sleep(1.5)
        try:
            df_12m = tr.interest_over_time([keyword], timeframe="today 12-m")
            slope_12m_raw = 0.0
            avg_12m = 0.0
            data_points_12m = 0

            if df_12m is not None and not df_12m.empty:
                col = (
                    [c for c in df_12m.columns if c != "isPartial"][0]
                    if len(df_12m.columns) > 1
                    else df_12m.columns[0]
                )
                values_12m = df_12m[col].tolist()
                slope_12m_raw = compute_slope(values_12m)
                avg_12m = round(sum(values_12m) / len(values_12m), 1)
                data_points_12m = len(values_12m)

            time.sleep(1.5)
            df_5y = tr.interest_over_time([keyword], timeframe="today 5-y")
            slope_5y_raw = 0.0
            avg_5y = 0.0
            data_points_5y = 0

            if df_5y is not None and not df_5y.empty:
                col = (
                    [c for c in df_5y.columns if c != "isPartial"][0]
                    if len(df_5y.columns) > 1
                    else df_5y.columns[0]
                )
                values_5y = df_5y[col].tolist()
                slope_5y_raw = compute_slope(values_5y)
                avg_5y = round(sum(values_5y) / len(values_5y), 1)
                data_points_5y = len(values_5y)

            all_results[keyword] = {
                "12_month": {
                    "slope_raw": round(slope_12m_raw, 3),
                    "slope_direction": classify_slope(slope_12m_raw),
                    "avg_interest": avg_12m,
                    "data_points": data_points_12m,
                },
                "5_year": {
                    "slope_raw": round(slope_5y_raw, 3),
                    "slope_direction": classify_slope(slope_5y_raw),
                    "avg_interest": avg_5y,
                    "data_points": data_points_5y,
                },
            }
        except Exception as e:
            all_results[keyword] = {
                "error": str(e),
                "12_month": None,
                "5_year": None,
            }

    if not all_results:
        return {
            "error": "No results retrieved",
            "keywords_analyzed": [],
            "overall": None,
        }

    successful = {k: v for k, v in all_results.items() if "error" not in v}
    if not successful:
        return {
            "error": "All keyword queries failed",
            "keywords_analyzed": list(all_results.keys()),
            "failures": {k: v["error"] for k, v in all_results.items() if "error" in v},
            "overall": None,
        }

    avg_slope_12m = sum(v["12_month"]["slope_raw"] for v in successful.values()) / len(
        successful
    )
    avg_slope_5y = sum(v["5_year"]["slope_raw"] for v in successful.values()) / len(
        successful
    )
    avg_interest_12m = sum(
        v["12_month"]["avg_interest"] for v in successful.values()
    ) / len(successful)

    if avg_slope_12m > 0.3:
        trend_12m = "accelerating"
    elif avg_slope_12m < -0.3:
        trend_12m = "declining"
    else:
        trend_12m = "flat"

    if avg_slope_5y > 0.2:
        trend_5y = "growing"
    elif avg_slope_5y < -0.2:
        trend_5y = "declining"
    else:
        trend_5y = "stable"

    return {
        "error": None,
        "keywords_analyzed": list(all_results.keys()),
        "keywords_failed": [k for k, v in all_results.items() if "error" in v],
        "per_keyword": all_results,
        "overall": {
            "trend_12m": trend_12m,
            "trend_5y": trend_5y,
            "avg_slope_12m": round(avg_slope_12m, 3),
            "avg_slope_5y": round(avg_slope_5y, 3),
            "avg_interest_12m": round(avg_interest_12m, 1),
            "keywords_consensus": "all keywords agree"
            if len(set(v["12_month"]["slope_direction"] for v in successful.values()))
            == 1
            else "mixed signals across keywords",
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="Check Google Trends for keyword interest"
    )
    parser.add_argument(
        "--keywords", required=True, help="Comma-separated keywords to check"
    )
    args = parser.parse_args()

    keywords = [k.strip() for k in args.keywords.split(",")]
    if not keywords:
        print(json.dumps({"error": "--keywords is required", "results": None}))
        sys.exit(1)

    result = get_trends(keywords)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
