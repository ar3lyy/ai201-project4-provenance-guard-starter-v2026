"""Structured request records for the capstone instrumentation."""

import json
import threading
from datetime import datetime, timezone

import config

REQUEST_LOG = config.LOG_DIR / "requests.jsonl"
_lock = threading.Lock()


def write_request(*, request_id, route, method, input_data,
                  output_data, status_code, duration_seconds):
    """Append one completed request without changing earlier records."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
        "route": route,
        "method": method,
        "input": input_data,
        "output": output_data,
        "status_code": status_code,
        "duration_seconds": duration_seconds,
    }

    line = json.dumps(entry, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    REQUEST_LOG.parent.mkdir(parents=True, exist_ok=True)

    with _lock:
        with REQUEST_LOG.open("a", encoding="utf-8") as stream:
            stream.write(line + "\n")

    return entry
