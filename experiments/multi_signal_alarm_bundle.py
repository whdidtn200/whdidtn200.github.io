#!/usr/bin/env python3
"""Compare score-only and evidence-bundle alarm policies on synthetic events."""

from __future__ import annotations

import csv
import random
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "lab-results"
ASSET_DIR = ROOT / "assets" / "lab-generated"
SOURCE = DATA_DIR / "bearing-threshold-samples.csv"
SEED = 2026072101
SEQUENCES_PER_CLASS = 1_000
WINDOWS = 12
FAULT_START = 4
POLICIES = ("score_only", "score_plus_diff", "triple_evidence")


def load_rows() -> list[dict]:
    with SOURCE.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        for field in ("rms", "crest", "kurtosis", "diff_rms", "normalized_impulse"):
            row[field] = float(row[field])
    return rows


def quantile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise RuntimeError("quantile requires at least one value")
    index = max(0, min(len(ordered) - 1, round((len(ordered) - 1) * fraction)))
    return ordered[index]


def build_thresholds(rows: list[dict]) -> dict[str, float]:
    healthy = [row for row in rows if row["class"] == "healthy"]
    return {
        "score": quantile([row["normalized_impulse"] for row in healthy], 0.95),
        "diff": quantile([row["diff_rms"] for row in healthy], 0.93),
        "kurtosis": quantile([row["kurtosis"] for row in healthy], 0.9),
    }


def classify_window(row: dict, thresholds: dict[str, float]) -> dict[str, bool]:
    score_hit = row["normalized_impulse"] > thresholds["score"]
    diff_hit = row["diff_rms"] > thresholds["diff"]
    kurtosis_hit = row["kurtosis"] > thresholds["kurtosis"]
    return {
        "score_only": score_hit,
        "score_plus_diff": score_hit and diff_hit,
        "triple_evidence": score_hit and diff_hit and kurtosis_hit,
    }


def first_alarm(flags: list[bool]) -> int | None:
    for index, flag in enumerate(flags):
        if flag:
            return index
    return None


def simulate(rows: list[dict], thresholds: dict[str, float]) -> tuple[list[dict], list[dict]]:
    rng = random.Random(SEED)
    detail: list[dict] = []
    summary: list[dict] = []
    conditions = sorted({row["condition"] for row in rows})
    for condition in conditions:
        healthy_pool = [row for row in rows if row["condition"] == condition and row["class"] == "healthy"]
        fault_pool = [row for row in rows if row["condition"] == condition and row["class"] == "fault"]
        for event_class in ("healthy", "fault"):
            outcomes = {policy: [] for policy in POLICIES}
            for event_id in range(SEQUENCES_PER_CLASS):
                event_rows = []
                for window in range(WINDOWS):
                    pool = healthy_pool if event_class == "healthy" or window < FAULT_START else fault_pool
                    event_rows.append(rng.choice(pool))
                policy_flags = {policy: [] for policy in POLICIES}
                for window, row in enumerate(event_rows):
                    flags = classify_window(row, thresholds)
                    for policy in POLICIES:
                        policy_flags[policy].append(flags[policy])
                    if event_id < 15:
                        detail.append(
                            {
                                "condition": condition,
                                "event_class": event_class,
                                "event_id": event_id + 1,
                                "window": window,
                                "fault_active": event_class == "fault" and window >= FAULT_START,
                                "normalized_impulse": row["normalized_impulse"],
                                "diff_rms": row["diff_rms"],
                                "kurtosis": row["kurtosis"],
                                "score_only": int(flags["score_only"]),
                                "score_plus_diff": int(flags["score_plus_diff"]),
                                "triple_evidence": int(flags["triple_evidence"]),
                            }
                        )
                for policy in POLICIES:
                    outcomes[policy].append(first_alarm(policy_flags[policy]))
            for policy in POLICIES:
                alarms = outcomes[policy]
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
                        "policy": policy,
                        "sequences": len(alarms),
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


def render_chart(summary: list[dict]) -> str:
    rows = [row for row in summary if row["condition"] == "combined" and row["event_class"] == "healthy"]
    colors = {
        "score_only": "#d3543f",
        "score_plus_diff": "#d8a62e",
        "triple_evidence": "#087f8c",
    }
    labels = {
        "score_only": "Score only",
        "score_plus_diff": "Score + diff_rms",
        "triple_evidence": "Score + diff_rms + kurtosis",
    }
    width, height = 1140, 700
    left, top, chart_width, chart_height = 110, 150, 900, 390
    bar_width = 170
    gap = 95
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">False alarm rate of evidence-bundle policies</title>',
        '<desc id="desc">Healthy combined-condition events from the public bearing feature set show how requiring multiple signals changes event false alarms.</desc>',
        '<rect width="1140" height="700" rx="28" fill="#f4f8fa"/>',
        '<text x="70" y="72" font-family="Avenir Next, sans-serif" font-size="32" font-weight="700" fill="#10253a">False alarm rate of evidence-bundle policies</text>',
        '<text x="70" y="108" font-family="Avenir Next, sans-serif" font-size="17" fill="#526a7f">1,000 healthy combined-condition events, bootstrap seed 2026072101</text>',
    ]
    for tick in range(0, 101, 20):
        y = top + chart_height - chart_height * tick / 100
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + chart_width}" y2="{y:.1f}" stroke="#d5e1e8"/>')
        parts.append(f'<text x="{left - 18}" y="{y + 6:.1f}" text-anchor="end" font-family="Avenir Next, sans-serif" font-size="14" fill="#60768a">{tick}%</text>')
    for index, policy in enumerate(POLICIES):
        row = next(item for item in rows if item["policy"] == policy)
        value = float(row["false_alarm_event_rate"]) * 100
        height_px = chart_height * value / 100
        x = left + 80 + index * (bar_width + gap)
        y = top + chart_height - height_px
        parts.append(f'<rect x="{x}" y="{y:.1f}" width="{bar_width}" height="{height_px:.1f}" rx="10" fill="{colors[policy]}"/>')
        parts.append(f'<text x="{x + bar_width / 2:.1f}" y="{y - 10:.1f}" text-anchor="middle" font-family="Avenir Next, sans-serif" font-size="16" font-weight="700" fill="#20384c">{value:.1f}%</text>')
        parts.append(f'<text x="{x + bar_width / 2:.1f}" y="{top + chart_height + 38:.1f}" text-anchor="middle" font-family="Avenir Next, sans-serif" font-size="15" fill="#42586d">{labels[policy]}</text>')
    parts.append('<text x="70" y="612" font-family="Avenir Next, sans-serif" font-size="16" fill="#42586d">Combined condition only. Lower is better for event-level nuisance burden.</text>')
    parts.append('</svg>')
    return "\n".join(parts) + "\n"


def main() -> None:
    rows = load_rows()
    thresholds = build_thresholds(rows)
    detail, summary = simulate(rows, thresholds)
    write_csv(DATA_DIR / "multi-signal-alarm-event-sample.csv", detail)
    write_csv(DATA_DIR / "multi-signal-alarm-summary.csv", summary)
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    (ASSET_DIR / "2026-07-21-multi-signal-alarm-false-alarm.svg").write_text(render_chart(summary), encoding="utf-8")
    print(f"seed={SEED} source_rows={len(rows)} thresholds={thresholds}")
    for row in summary:
        if row["condition"] == "combined" and row["event_class"] == "healthy":
            print(row["policy"], f"false_alarm={float(row['false_alarm_event_rate']):.3f}")


if __name__ == "__main__":
    main()
