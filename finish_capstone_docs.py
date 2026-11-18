"""Assemble capstone documentation from saved evaluation evidence."""

import json
from pathlib import Path

root = Path("results/capstone")


def load(name):
    return json.loads((root / name).read_text())


def block(value):
    return "```json\n" + json.dumps(value, indent=2) + "\n```\n"


measurements = load("improvement_measurements.json")
model = load("model_size.json")
before = [load(f"before_trial_{i}.json") for i in range(1, 4)]
after = [load(f"after_trial_{i}.json") for i in range(1, 4)]
restart = {
    label: [load(f"{label}_restart_{i}.json") for i in range(1, 4)]
    for label in ["before", "after"]
}

names = [
    "Complete and accurate valid-request logs",
    "Accurate failed-request logs",
    "Logs preserved after restart",
    "Successful warm submissions within 2 seconds",
    "Existing submission behavior preserved",
]
targets = ["10/10", "10/10", "10/10", "At least 9/10", "20/20"]
denominators = [10, 10, 10, 10, 20]
thresholds = [10, 10, 10, 9, 20]


def counts(label, trials):
    return [
        [t["summary"]["criterion_1_correct_valid_logs"] for t in trials],
        [t["summary"]["criterion_2_correct_failure_logs"] for t in trials],
        [r["preserved"] for r in restart[label]],
        [t["summary"]["criterion_4_successful_requests_within_2s"]
         for t in trials],
        [t["summary"]["criterion_5_matching_responses"] for t in trials],
    ]


def table(label, trials):
    values = counts(label, trials)
    lines = [
        "| Criterion | Target | Trial 1 | Trial 2 | Trial 3 | Verdict |",
        "|---|---|---|---|---|---|",
    ]
    for i, name in enumerate(names):
        scores = " | ".join(
            f"{value}/{denominators[i]}" for value in values[i]
        )
        verdict = "MET" if all(
            value >= thresholds[i] for value in values[i]
        ) else "MISSED"
        lines.append(
            f"| {i + 1}. {name} | {targets[i]} | {scores} | {verdict} |"
        )
    return "\n".join(lines) + "\n"


readme = Path("README.md")
text = readme.read_text()
marker = "**Running It**"
capstone = text.split("## Capstone", 1)
if len(capstone) != 2:
    raise SystemExit("Expected one existing Capstone heading.")
if marker in capstone[1]:
    raise SystemExit("Final sections already exist; refusing to duplicate.")

sections = """
**Running It**

I used Path B: local with logs. `RUNNING.md` contains the environment,
setup, and single Gunicorn start command. A fresh local clone with a
new virtual environment processed and logged a real submission. It reused
this machine's existing Hugging Face model cache; this was not a test
of downloading the model on a completely new machine.

The measured GPT-2 weight file is """
sections += (
    f"{model['bytes']:,} bytes ({model['decimal_MB']:.2f} decimal MB). "
    "That excludes PyTorch, tokenizer files, and the service itself. "
    "A 512 MB hosting allowance would not accommodate the loaded model "
    "and its runtime, so I kept the service local.\n\n"
)
sections += """
**Instrumentation**

`request_instrumentation.py::install_request_logging` captures `/submit`
and `/appeal` requests. `request_audit.py::write_request` appends UTF-8
JSON Lines to `logs/requests.jsonl`. Records hold a UTC timestamp,
request ID, route, method, input body and parsed JSON, response,
HTTP status, and duration in seconds.

The existing decision audit remains separate. Rejected inputs and rate
limits pass through the response logger. Unexpected server errors receive
a generic JSON 500 response; the traceback remains in the server error
output. A separately simulated detector failure was also checked.

Duration covers the request hook through the start of the response hook.
It excludes the log write and response transfer. The evaluation-only
`capstone_test_server.py::observed_clock` takes independent nanosecond
clock readings adjacent to the instrumentation clock readings at the
same boundaries. It checks elapsed-time agreement, not whether those
boundaries cover the complete HTTP lifecycle.

These are ten actual after-trial-1 request records:
"""
sections += block([r["request_record"] for r in after[0]["requests"][:10]])
sections += "\nActual rejected request from that trial:\n"
sections += block(after[0]["requests"][10]["request_record"])

failure = [
    json.loads(line)
    for line in Path("logs/capstone_failure_smoke.jsonl").read_text().splitlines()
    if line.strip()
]
sections += "\nSeparately simulated detector exception, not a natural outage:\n"
sections += block(failure[-1])

b = measurements["before"]
a = measurements["after"]
sections += "\n**What It Costs**\n\n"
sections += (
    "I measured elapsed processing time rather than API dollars, CPU time, "
    "or electricity. No hosted model API is called. Each trial measured "
    "ten valid warm submissions after a separate warm-up request. "
    "The reported average combines all 30 warm submissions per phase.\n\n"
    f"Before: {b['mean_server_processing_seconds']:.6f} server seconds "
    f"per request and {b['mean_client_seconds']:.6f} client seconds.\n\n"
    f"After: {a['mean_server_processing_seconds']:.6f} server seconds "
    f"per request and {a['mean_client_seconds']:.6f} client seconds.\n\n"
    "For 100 people making one submission each per day, the after-run "
    f"arithmetic is {a['mean_server_processing_seconds']:.6f} × 100 "
    f"= {a['server_seconds_for_100_requests']:.3f} seconds of accumulated "
    "server processing per day. This assumes the same inputs, hardware, "
    "and warm model. It excludes startup, idle time, concurrency effects, "
    "log-writing time, and additional submissions or appeals.\n"
)

sections += """
**Run Log and Verdicts**

Before-improvement results:
"""
sections += table("before", before)
sections += """
All five targets were met in all three trials; there were no missed
criteria to diagnose. The latency target was generous for this workload.
The ten valid fixtures are closely related synthetic paragraphs, not
a representative authorship dataset. These results establish behavior
for these cases, not general detector accuracy.

`capstone_eval.py` compares actual responses against the original
pre-instrumentation baseline, excluding generated content IDs.
`capstone_restart_check.py` checks field equality and exactly one
occurrence after a manual normal stop and restart. The before-phase
restart checks used equivalent inline Python, preserved in the resulting
evidence files. No criterion target was changed after seeing results.

Actual evidence for each criterion, from before trial 1:

1. Logging and reference timing, produced by the request hooks and
`capstone_test_server.py::observed_clock`:
"""
first = before[0]["requests"][0]
sections += block({
    key: first[key] for key in
    ["case", "request_record", "reference_record",
     "relative_timing_error", "log_correct"]
})
sections += "\n2. Rejection response and log, from `app.py::submit` and the hooks:\n"
sections += block(before[0]["requests"][10])
sections += "\n3. Restart comparison output from the before-trial-1 checker:\n"
sections += block(restart["before"][0])
sections += "\n4. Actual client timing from `capstone_eval.py`:\n"
sections += block({
    key: first[key] for key in ["case", "status_code", "client_seconds"]
})
original = load("original_responses.json")
original_first = next(
    r for r in original if r["trial"] == 1 and r["case"] == first["case"]
)
sections += "\n5. Actual original/current responses compared by `capstone_eval.py`:\n"
sections += block({
    "original_response": original_first["output"],
    "instrumented_response": first["output"],
    "matching_except_generated_id": first["behavior_matches"],
})

sections += """
**The Improvement**

No criterion failed, so I chose a small storage improvement:
`request_audit.py::write_request` now uses compact JSON separators.
The only service-code change removed optional JSON spacing.
All fields and parsed values were retained. Existing log lines were
left intact.

This addressed repeated serialization overhead in an append-only log.
It was not a fix for an observed detector or logging failure.

After-improvement results:
"""
sections += table("after", after)
sections += "\nSide-by-side results:\n\n"
sections += "| Criterion | Before trials 1 / 2 / 3 | After trials 1 / 2 / 3 |\n"
sections += "|---|---|---|\n"
for i, name in enumerate(names):
    left = " / ".join(str(v) for v in counts("before", before)[i])
    right = " / ".join(str(v) for v in counts("after", after)[i])
    sections += f"| {name} (out of {denominators[i]}) | {left} | {right} |\n"

controlled = measurements["same_records_formatting_comparison"]
sections += (
    f"\nActual records averaged {b['mean_bytes_per_record']:.2f} bytes before "
    f"and {a['mean_bytes_per_record']:.2f} bytes after, a "
    f"{measurements['storage_reduction_percent']:.2f}% decrease. "
    "Sizes include the UTF-8 newline. To isolate formatting from changing "
    "IDs, timestamps, and durations, I also serialized the exact same 60 "
    f"after-run records both ways: {controlled['default_bytes']:,} bytes "
    f"with default spacing versus {controlled['compact_bytes']:,} compact, "
    f"a {controlled['reduction_percent']:.2f}% reduction.\n\n"
    "The change helped storage modestly and preserved all five tested "
    "behaviors. Response-time averages were similar; these runs do not "
    "establish a speed improvement. Compact lines are less comfortable "
    "to read directly, although they still parse and can be pretty-printed.\n"
)

sections += """
**What's Still Broken**

No acceptance criterion remained missed. I would tighten criterion 4
from at least 9/10 under 2 seconds to at least 9/10 under 0.2 seconds
for this same warm, sequential, 100–200-word workload. This is a future
target, not a revision to the original criterion.

The tests used closely related valid inputs and ten specific invalid
cases. They do not establish performance across varied writing,
concurrent clients, or heavy load. Appeals and a detector exception
received smoke checks, not the full three-trial submission evaluation.
Rate-limit logging was implemented but was not deliberately exercised
in this capstone evaluation.

The writer is intended for one worker. A thread lock does not coordinate
multiple processes. Normal restarts preserved records, but abrupt power
loss, full disks, and failed log writes were not tested. Logs contain
submitted text, so a real deployment would also need access and
retention decisions.

I stopped after one measured change and the required before/after cycle
to keep the declared scope bounded. The existing detector's authorship
limitations remain; adding logs does not improve its accuracy.

With another unit, I would first replace the near-identical valid
fixtures with a more varied fixed workload spanning the allowed input
lengths. That would make the latency and regression evidence more useful
before considering additional deployment work.

**How I Used AI**

I asked for help making my acceptance statements testable and
evaluating the extension. I chose and wrote the criteria through that
discussion, including 10/10 logging, a 10% timing tolerance, restart
preservation, the 2-second target, and unchanged submission behavior.
The compact-JSON improvement was also suggested by ChatGPT. I ran it
and measured its actual storage effect rather than assuming it helped.
"""

readme.write_text(text.rstrip() + "\n\n" + sections.strip() + "\n")

running = Path("RUNNING.md")
run_text = running.read_text()
old = "The full three-trial acceptance evaluation is still pending."
new = (
    "The full before/after evaluation is complete: all five criteria met "
    "their targets in each of three trials per phase. Detailed results "
    "are under README.md's Capstone heading and in results/capstone/."
)
if old not in run_text:
    raise SystemExit("README written; RUNNING verification sentence needs manual review.")
run_text = run_text.replace(old, new, 1)
run_text += (
    f"\nMeasured GPT-2 weights: `{model['weights_file']}`, "
    f"{model['bytes']:,} bytes ({model['decimal_MB']:.2f} decimal MB). "
    "This excludes tokenizer and other cache files. "
    "See `results/capstone/model_size.json`.\n"
)
running.write_text(run_text)
print("Updated README.md and RUNNING.md using saved evidence.")