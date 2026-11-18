"""Evaluation-only launcher with an independent timing record."""

import json
import time
from types import SimpleNamespace

from flask import g, request

from app import app
import config
import request_instrumentation

REFERENCE_LOG = config.LOG_DIR / "capstone_reference.jsonl"


def observed_clock():
    """Take adjacent readings from the logging and reference clocks."""
    reference = time.perf_counter_ns()
    measured = time.perf_counter()

    if not hasattr(g, "reference_started_ns"):
        g.reference_started_ns = reference
    else:
        g.reference_finished_ns = reference

    return measured


# Replace only the instrumentation module's clock reference.
# Detector code and the normal launcher are unchanged.
request_instrumentation.time = SimpleNamespace(
    perf_counter=observed_clock
)


def save_reference(response):
    if not hasattr(g, "reference_finished_ns"):
        return response

    entry = {
        "request_id": g.request_record_id,
        "route": request.path,
        "reference_duration_seconds": (
            g.reference_finished_ns - g.reference_started_ns
        ) / 1_000_000_000,
        "method": "Independent perf_counter_ns readings adjacent to "
                  "the instrumentation's start and stop readings",
    }

    REFERENCE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with REFERENCE_LOG.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(entry) + "\n")

    return response


# Flask runs response hooks in reverse registration order.
# Put this first so it runs after the normal request-log hook.
app.after_request_funcs.setdefault(None, []).insert(0, save_reference)