"""Check saved request records after a manual service restart."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

parser = argparse.ArgumentParser()
parser.add_argument("--label", choices=["before", "after"], required=True)
parser.add_argument("--trial", type=int, choices=[1, 2, 3], required=True)
args = parser.parse_args()

root = Path("results/capstone")
destination = root / f"{args.label}_restart_{args.trial}.json"
if destination.exists():
    raise SystemExit("Restart evidence already exists; refusing to overwrite.")

requests.get("http://127.0.0.1:5001/health", timeout=10).raise_for_status()
trial = json.loads(
    (root / f"{args.label}_trial_{args.trial}.json").read_text()
)
current = [
    json.loads(line)
    for line in Path("logs/requests.jsonl").read_text().splitlines()
    if line.strip()
]

checks = []
for original in trial["restart_snapshot"]:
    matches = [
        entry for entry in current
        if entry.get("request_id") == original["request_id"]
    ]
    checks.append({
        "request_id": original["request_id"],
        "preserved_exactly_once": len(matches) == 1 and matches[0] == original,
    })

evidence = {
    "label": args.label,
    "trial": args.trial,
    "checked_at": datetime.now(timezone.utc).isoformat(),
    "procedure": "Manually stopped and restarted Gunicorn before checking",
    "preserved": sum(item["preserved_exactly_once"] for item in checks),
    "total": len(checks),
    "checks": checks,
}
with destination.open("x", encoding="utf-8") as stream:
    json.dump(evidence, stream, indent=2)

print(f"Preserved unchanged, exactly once: {evidence['preserved']}/10")
print("Saved:", destination)