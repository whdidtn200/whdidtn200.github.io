#!/usr/bin/env python3
"""Bootstrap alarm persistence rules from the published bearing feature set."""

from __future__ import annotations

import csv
import random
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "lab-results"
ASSET_DIR = ROOT / "assets" / "lab-generated"
SOURCE = DATA_DIR / "bearing-threshold-samples.csv"
SUMMARY = DATA_DIR / "bearing-threshold-summary.csv"
SEED = 2026071702
SEQUENCES_PER_CLASS = 1_000
WINDOWS = 12
FAULT_START = 4
RULES = {
    "1_of_1": (1, 1),
    "2_of_3": (2, 3),
    "3_of_5": (3, 5),
}


def load_rows() -> list[dict]:
    with SOURCE.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["normalized_impulse"] = float(row["normalized_impulse"])
    return rows


def load_threshold() -> float:
    with SUMMARY.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["detector"] == "context_normalized":
                return float(row["threshold"])
    raise RuntimeError("context_normalized threshold not found")


def first_alarm(flags: list[bool], required: int, span: int) -> int | None:
    for index in range(len(flags)):
        start = max(0, index - span + 1)
        if sum(flags[start : index + 1]) >= required:
            return index
    return None


def simulate(rows: list[dict], threshold: float) -> tuple[list[dict], list[dict]]:
    rng = random.Random(SEED)
    detail = []
    summary = []
    conditions = sorted({row["condition"] for row in rows})
    for condition in conditions:
        healthy_pool = [row for row in rows if row["condition"] == condition and row["class"] == "healthy"]
        fault_pool = [row for row in rows if row["condition"] == condition and row["class"] == "fault"]
        for event_class in ("healthy", "fault"):
            sequences = []
            for event_id in range(SEQUENCES_PER_CLASS):
                values = []
                for window in range(WINDOWS):
                    pool = healthy_pool if event_class == "healthy" or window < FAULT_START else fault_pool
                    values.append(rng.choice(pool)["normalized_impulse"])
                flags = [value > threshold for value in values]
                sequences.append(flags)
                if event_id < 20:
                    for window, (value, exceeded) in enumerate(zip(values, flags)):
                        detail.append(
                            {
                                "condition": condition,
                                "event_class": event_class,
                                "event_id": event_id + 1,
                                "window": window,
                                "fault_active": event_class == "fault" and window >= FAULT_START,
                                "score": value,
                                "threshold": threshold,
                                "exceeded": exceeded,
                            }
                        )
            for rule_name, (required, span) in RULES.items():
                alarms = [first_alarm(flags, required, span) for flags in sequences]
                if event_class == "healthy":
                    false_alarm_rate = sum(index is not None for index in alarms) / len(alarms)
                    detection_rate = ""
                    delays: list[int] = []
                else:
                    valid = [index for index in alarms if index is not None and index >= FAULT_START]
                    false_alarm_rate = sum(index is not None and index < FAULT_START for index in alarms) / len(alarms)
                    detection_rate = len(valid) / len(alarms)
                    delays = [index - FAULT_START for index in valid]
                summary.append(
                    {
                        "condition": condition,
                        "event_class": event_class,
                        "rule": rule_name,
                        "sequences": len(sequences),
                        "false_alarm_event_rate": false_alarm_rate,
                        "detection_event_rate": detection_rate,
                        "median_detection_delay_windows": statistics.median(delays) if delays else "",
                    }
                )
    return detail, summary


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def chart(summary: list[dict]) -> str:
    rows = [row for row in summary if row["event_class"] == "healthy"]
    conditions = ["clean", "high_noise", "speed_drift", "load_change", "combined"]
    colors = {"1_of_1": "#e06c3b", "2_of_3": "#d8a62e", "3_of_5": "#087f8c"}
    labels = {"1_of_1": "1-of-1", "2_of_3": "2-of-3", "3_of_5": "3-of-5"}
    width, height = 1_180, 720
    left, top, chart_width, chart_height = 110, 150, 980, 420
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Event false alarm rate by persistence rule</title>',
        '<desc id="desc">Twelve-window healthy events bootstrapped from the published synthetic bearing feature set.</desc>',
        '<rect width="1180" height="720" rx="28" fill="#f4f8fa"/>',
        '<text x="70" y="70" font-family="Avenir Next, sans-serif" font-size="32" font-weight="700" fill="#10253a">Event false alarm rate by persistence rule</text>',
        '<text x="70" y="108" font-family="Avenir Next, sans-serif" font-size="17" fill="#526a7f">1,000 healthy 12-window events per condition; bootstrap seed 2026071702</text>',
    ]
    for tick in range(0, 101, 20):
        y = top + chart_height - chart_height * tick / 100
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + chart_width}" y2="{y:.1f}" stroke="#d5e1e8"/>')
        parts.append(f'<text x="{left - 18}" y="{y + 6:.1f}" text-anchor="end" font-family="Avenir Next, sans-serif" font-size="14" fill="#60768a">{tick}%</text>')
    group_width = chart_width / len(conditions)
    bar_width = 42
    offsets = {"1_of_1": -bar_width, "2_of_3": 0, "3_of_5": bar_width}
    for condition_index, condition in enumerate(conditions):
        center = left + group_width * (condition_index + 0.5)
        for rule in RULES:
            row = next(item for item in rows if item["condition"] == condition and item["rule"] == rule)
            value = float(row["false_alarm_event_rate"]) * 100
            bar_height = chart_height * value / 100
            x = center + offsets[rule] - bar_width / 2
            y = top + chart_height - bar_height
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width}" height="{bar_height:.1f}" rx="7" fill="{colors[rule]}"/>')
            parts.append(f'<text x="{x + bar_width / 2:.1f}" y="{max(y - 8, 140):.1f}" text-anchor="middle" font-family="Avenir Next, sans-serif" font-size="12" font-weight="700" fill="#20384c">{value:.1f}</text>')
        parts.append(f'<text x="{center:.1f}" y="{top + chart_height + 34}" text-anchor="middle" font-family="Avenir Next, sans-serif" font-size="14" fill="#42586d">{condition.replace("_", " ")}</text>')
    for index, rule in enumerate(RULES):
        x = 230 + index * 260
        parts.append(f'<rect x="{x}" y="640" width="22" height="22" rx="5" fill="{colors[rule]}"/>')
        parts.append(f'<text x="{x + 34}" y="657" font-family="Avenir Next, sans-serif" font-size="16" fill="#314a60">{labels[rule]}</text>')
    parts.append('</svg>')
    return "\n".join(parts) + "\n"


def main() -> None:
    rows = load_rows()
    threshold = load_threshold()
    detail, summary = simulate(rows, threshold)
    write_csv(DATA_DIR / "alarm-persistence-event-sample.csv", detail)
    write_csv(DATA_DIR / "alarm-persistence-summary.csv", summary)
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    (ASSET_DIR / "2026-07-17-alarm-persistence-false-alarm.svg").write_text(chart(summary), encoding="utf-8")
    print(f"seed={SEED} source_rows={len(rows)} event_windows={len(detail)} threshold={threshold:.6f}")
    for row in summary:
        if row["event_class"] == "healthy":
            print(row["condition"], row["rule"], f"false_alarm={float(row['false_alarm_event_rate']):.3f}")


if __name__ == "__main__":
    main()
