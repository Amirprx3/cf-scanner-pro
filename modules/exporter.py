"""
exporter.py – save results to CSV and JSON.
"""

import csv
import json
from typing import List
from .result import IPResult


def export(results: List[IPResult], base: str, min_score: int = 1):
    alive = sorted(
        [r for r in results if r.alive and r.score >= min_score],
        key=lambda r: r.score,
        reverse=True,
    )

    # ── CSV ──────────────────────────────────────────────────
    csv_path = f"{base}.csv"
    if alive:
        fieldnames = list(alive[0].to_dict().keys())
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in alive:
                writer.writerow(r.to_dict())

    # ── JSON ─────────────────────────────────────────────────
    json_path = f"{base}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump([r.to_dict() for r in alive], f, indent=2, ensure_ascii=False)

    # ── Plain actives.txt (IP only, for v2ray/xray configs) ──
    txt_path = f"{base}.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        for r in alive:
            f.write(r.ip + "\n")

    return csv_path, json_path, txt_path
