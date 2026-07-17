#!/usr/bin/env python3
"""Reproducible synthetic benchmark for bearing alarm thresholds.

The experiment intentionally uses only Python's standard library so readers can
rerun it without installing a scientific stack. It is a mechanism test, not a
claim about field accuracy.
"""

from __future__ import annotations

import csv
import math
import random
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "lab-results"
ASSET_DIR = ROOT / "assets" / "lab-generated"
SEED = 20260717
SAMPLE_RATE = 2_048
SAMPLE_COUNT = 2_048
RUNS_PER_CLASS = 120

CONDITIONS = {
    "clean": {"noise": 0.10, "speed": (29.5, 30.5), "load": (0.95, 1.05)},
    "high_noise": {"noise": 0.28, "speed": (29.5, 30.5), "load": (0.95, 1.05)},
    "speed_drift": {"noise": 0.10, "speed": (24.0, 36.0), "load": (0.95, 1.05)},
    "load_change": {"noise": 0.10, "speed": (29.5, 30.5), "load": (0.55, 1.45)},
    "combined": {"noise": 0.24, "speed": (24.0, 36.0), "load": (0.55, 1.45)},
}


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def generate_signal(rng: random.Random, condition: dict, faulty: bool) -> list[float]:
    speed = rng.uniform(*condition["speed"])
    load = rng.uniform(*condition["load"])
    phase = rng.uniform(0, 2 * math.pi)
    signal = []
    for index in range(SAMPLE_COUNT):
        time = index / SAMPLE_RATE
        base = load * (
            0.62 * math.sin(2 * math.pi * speed * time + phase)
            + 0.20 * math.sin(2 * math.pi * speed * 2 * time + phase / 3)
        )
        signal.append(base + rng.gauss(0, condition["noise"]))

    if faulty:
        fault_rate = speed * 4.05
        interval = SAMPLE_RATE / fault_rate
        cursor = rng.uniform(0, interval)
        while cursor < SAMPLE_COUNT:
            start = int(cursor)
            amplitude = load * rng.uniform(0.72, 1.18)
            for offset in range(30):
                idx = start + offset
                if idx >= SAMPLE_COUNT:
                    break
                decay = math.exp(-offset / 7.0)
                resonance = math.sin(2 * math.pi * 620 * offset / SAMPLE_RATE)
                signal[idx] += amplitude * decay * resonance
            cursor += interval + rng.uniform(-0.08, 0.08) * interval
    return signal


def features(signal: list[float]) -> dict[str, float]:
    rms = math.sqrt(sum(value * value for value in signal) / len(signal))
    peak = max(abs(value) for value in signal)
    centered = [value - statistics.fmean(signal) for value in signal]
    variance = sum(value * value for value in centered) / len(centered)
    kurtosis = (
        sum(value**4 for value in centered) / len(centered) / (variance * variance)
        if variance > 0
        else 0.0
    )
    differences = [signal[index] - signal[index - 1] for index in range(1, len(signal))]
    diff_rms = math.sqrt(sum(value * value for value in differences) / len(differences))
    return {
        "rms": rms,
        "crest": peak / rms if rms else 0.0,
        "kurtosis": kurtosis,
        "diff_rms": diff_rms,
        "normalized_impulse": (diff_rms / rms) * math.sqrt(max(kurtosis, 0.0)),
    }


def build_samples() -> list[dict]:
    rng = random.Random(SEED)
    rows = []
    for condition_name, condition in CONDITIONS.items():
        for faulty in (False, True):
            for run in range(RUNS_PER_CLASS):
                row = {
                    "condition": condition_name,
                    "class": "fault" if faulty else "healthy",
                    "run": run + 1,
                }
                row.update(features(generate_signal(rng, condition, faulty)))
                rows.append(row)
    return rows


def evaluate(rows: list[dict]) -> tuple[list[dict], dict[str, float]]:
    clean_healthy = [
        row for row in rows if row["condition"] == "clean" and row["class"] == "healthy"
    ]
    all_healthy = [row for row in rows if row["class"] == "healthy"]
    thresholds = {
        "fixed_diff_rms": percentile([row["diff_rms"] for row in clean_healthy], 0.95),
        "context_normalized": percentile(
            [row["normalized_impulse"] for row in all_healthy], 0.95
        ),
    }

    results = []
    for condition_name in CONDITIONS:
        subset = [row for row in rows if row["condition"] == condition_name]
        for detector, threshold in thresholds.items():
            metric = "diff_rms" if detector == "fixed_diff_rms" else "normalized_impulse"
            healthy = [row for row in subset if row["class"] == "healthy"]
            faulty = [row for row in subset if row["class"] == "fault"]
            false_positives = sum(row[metric] > threshold for row in healthy)
            true_positives = sum(row[metric] > threshold for row in faulty)
            results.append(
                {
                    "condition": condition_name,
                    "detector": detector,
                    "threshold": threshold,
                    "false_alarm_rate": false_positives / len(healthy),
                    "detection_rate": true_positives / len(faulty),
                    "healthy_samples": len(healthy),
                    "fault_samples": len(faulty),
                }
            )
    return results, thresholds


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def svg_bar_chart(results: list[dict], metric: str, title: str, subtitle: str) -> str:
    width, height = 1_160, 700
    left, top, chart_width, chart_height = 110, 150, 960, 410
    conditions = list(CONDITIONS)
    colors = {"fixed_diff_rms": "#e06c3b", "context_normalized": "#087f8c"}
    labels = {"fixed_diff_rms": "Fixed absolute threshold", "context_normalized": "Context-normalized"}
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{title}</title><desc id="desc">{subtitle}</desc>',
        '<rect width="1160" height="700" rx="28" fill="#f4f8fa"/>',
        f'<text x="70" y="70" font-family="Avenir Next, sans-serif" font-size="32" font-weight="700" fill="#10253a">{title}</text>',
        f'<text x="70" y="108" font-family="Avenir Next, sans-serif" font-size="17" fill="#526a7f">{subtitle}</text>',
    ]
    for tick in range(0, 101, 20):
        y = top + chart_height - chart_height * tick / 100
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + chart_width}" y2="{y:.1f}" stroke="#d5e1e8"/>')
        parts.append(f'<text x="{left - 18}" y="{y + 6:.1f}" text-anchor="end" font-family="Avenir Next, sans-serif" font-size="14" fill="#60768a">{tick}%</text>')
    group_width = chart_width / len(conditions)
    bar_width = 54
    for index, condition in enumerate(conditions):
        center = left + group_width * (index + 0.5)
        for offset, detector in ((-bar_width / 2, "fixed_diff_rms"), (bar_width / 2, "context_normalized")):
            row = next(item for item in results if item["condition"] == condition and item["detector"] == detector)
            value = row[metric] * 100
            bar_height = chart_height * value / 100
            x = center + offset - bar_width / 2
            y = top + chart_height - bar_height
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width}" height="{bar_height:.1f}" rx="8" fill="{colors[detector]}"/>')
            parts.append(f'<text x="{x + bar_width / 2:.1f}" y="{max(y - 10, 136):.1f}" text-anchor="middle" font-family="Avenir Next, sans-serif" font-size="14" font-weight="700" fill="#20384c">{value:.1f}</text>')
        label = condition.replace("_", " ")
        parts.append(f'<text x="{center:.1f}" y="{top + chart_height + 34}" text-anchor="middle" font-family="Avenir Next, sans-serif" font-size="14" fill="#42586d">{label}</text>')
    legend_y = 640
    for index, detector in enumerate(("fixed_diff_rms", "context_normalized")):
        x = 260 + index * 350
        parts.append(f'<rect x="{x}" y="{legend_y - 16}" width="22" height="22" rx="5" fill="{colors[detector]}"/>')
        parts.append(f'<text x="{x + 34}" y="{legend_y + 1}" font-family="Avenir Next, sans-serif" font-size="16" fill="#314a60">{labels[detector]}</text>')
    parts.append('</svg>')
    return "\n".join(parts) + "\n"


def main() -> None:
    samples = build_samples()
    results, thresholds = evaluate(samples)
    write_csv(DATA_DIR / "bearing-threshold-samples.csv", samples)
    write_csv(DATA_DIR / "bearing-threshold-summary.csv", results)
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    (ASSET_DIR / "2026-07-17-bearing-threshold-detection.svg").write_text(
        svg_bar_chart(
            results,
            "detection_rate",
            "Fault detection rate by operating condition",
            "120 healthy and 120 fault simulations per condition; seed 20260717",
        ),
        encoding="utf-8",
    )
    (ASSET_DIR / "2026-07-17-bearing-threshold-false-alarm.svg").write_text(
        svg_bar_chart(
            results,
            "false_alarm_rate",
            "False alarm rate by operating condition",
            "A fixed clean-condition threshold is compared with a context-normalized score",
        ),
        encoding="utf-8",
    )
    print(f"seed={SEED} samples={len(samples)}")
    print("thresholds", {key: round(value, 6) for key, value in thresholds.items()})
    for row in results:
        print(
            row["condition"],
            row["detector"],
            f"detection={row['detection_rate']:.3f}",
            f"false_alarm={row['false_alarm_rate']:.3f}",
        )


if __name__ == "__main__":
    main()
