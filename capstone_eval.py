"""Run one capstone evaluation trial against the local test launcher."""

import argparse
import json
import math
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import requests

parser = argparse.ArgumentParser()
parser.add_argument("--label", choices=["before", "after"], required=True)
parser.add_argument("--trial", type=int, choices=[1, 2, 3], required=True)
args = parser.parse_args()

root = Path("results/capstone")
destination = root / f"{args.label}_trial_{args.trial}.json"
if destination.exists():
    raise SystemExit(f"{destination} already exists; refusing to overwrite.")

cases = json.loads((root / "submission_cases.json").read_text())
baseline = json.loads((root / "original_responses.json").read_text())
baseline = {
    (row["trial"], row["case"]): row
    for row in baseline
}
base = "http://127.0.0.1:5001"
session = uuid.uuid4().hex[:12]


def read_jsonl(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines()
            if line.strip()]


def make_payload(case, suffix):
    payload = dict(case["payload"])
    if "creator_id" not in payload:
        payload["creator_id"] = f"capstone-{session}-{suffix}"
    if payload.get("creator_id", "") is None:
        payload.pop("creator_id", None)
    return payload


def detection_fields(body):
    return {key: value for key, value in body.items()
            if key != "content_id"}


# Warm up this server process before measuring the ten valid requests.
warm = requests.post(
    base + "/submit",
    json=make_payload(cases[0], "warmup"),
    timeout=120,
)
warm.raise_for_status()
assert requests.get(base + "/health", timeout=10).json()["detector_loaded"]

rows = []
for case in cases:
    payload = make_payload(case, case["name"])
    log_path = Path("logs/requests.jsonl")
    previous_count = len(read_jsonl(log_path))

    started = time.perf_counter()
    response = requests.post(base + "/submit", json=payload, timeout=120)
    client_seconds = time.perf_counter() - started
    body = response.json()

    new_records = read_jsonl(log_path)[previous_count:]
    record = new_records[0] if len(new_records) == 1 else None

    references = read_jsonl(Path("logs/capstone_reference.jsonl"))
    matching_references = [
        item for item in references
        if record and item["request_id"] == record["request_id"]
    ]
    reference = (
        matching_references[0]
        if len(matching_references) == 1 else None
    )

    timestamp_ok = False
    if record:
        try:
            timestamp = datetime.fromisoformat(
                record["timestamp"].replace("Z", "+00:00")
            )
            timestamp_ok = timestamp.utcoffset() == timedelta(0)
        except (KeyError, ValueError, TypeError):
            pass

    timing_error = None
    if record and reference:
        expected_duration = reference["reference_duration_seconds"]
        if expected_duration > 0:
            timing_error = abs(
                record["duration_seconds"] - expected_duration
            ) / expected_duration

    log_correct = bool(
        record
        and timestamp_ok
        and record.get("input", {}).get("json") == payload
        and record.get("output") == body
        and record.get("status_code") == response.status_code
        and isinstance(record.get("duration_seconds"), (int, float))
        and math.isfinite(record["duration_seconds"])
        and record["duration_seconds"] >= 0
        and timing_error is not None
        and timing_error <= 0.10
    )

    original = baseline[(args.trial, case["name"])]
    behavior_matches = (
        response.status_code == original["status_code"]
        and response.status_code == case["expected_status"]
        and detection_fields(body) == detection_fields(original["output"])
    )

    rows.append({
        "case": case["name"],
        "input": payload,
        "status_code": response.status_code,
        "output": body,
        "client_seconds": client_seconds,
        "request_record": record,
        "reference_record": reference,
        "relative_timing_error": timing_error,
        "log_correct": log_correct,
        "behavior_matches": behavior_matches,
    })
    print(
        f"{case['name']}: HTTP {response.status_code}, "
        f"{client_seconds:.4f}s, log={log_correct}, "
        f"baseline_match={behavior_matches}",
        flush=True,
    )

valid = rows[:10]
invalid = rows[10:]
summary = {
    "criterion_1_correct_valid_logs": sum(r["log_correct"] for r in valid),
    "criterion_2_correct_failure_logs": sum(r["log_correct"] for r in invalid),
    "criterion_3_restart": "PENDING actual service restart",
    "criterion_4_successful_requests_within_2s": sum(
        r["status_code"] == 200 and r["client_seconds"] <= 2
        for r in valid
    ),
    "criterion_5_matching_responses": sum(
        r["behavior_matches"] for r in rows
    ),
    "mean_warm_client_seconds": sum(
        r["client_seconds"] for r in valid
    ) / 10,
    "mean_warm_server_seconds": (
        sum(r["request_record"]["duration_seconds"] for r in valid) / 10
        if all(r["request_record"] for r in valid) else None
    ),
}

result = {
    "label": args.label,
    "trial": args.trial,
    "summary": summary,
    "requests": rows,
    "restart_snapshot": [r["request_record"] for r in valid],
}

with destination.open("x", encoding="utf-8") as stream:
    json.dump(result, stream, indent=2)

print(json.dumps(summary, indent=2))
print("Saved:", destination)