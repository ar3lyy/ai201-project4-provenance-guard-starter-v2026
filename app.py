#!/usr/bin/env python3
"""
Provenance Guard — the web service.

    python app.py

Routes:

    POST /ping        the worked example
    POST /submit      evaluate and log a submission
    POST /appeal      record an appeal
    GET  /log         read the audit log
    GET  /health      check the service
"""

import uuid

from flask import Flask, jsonify, request

import audit
import config
import detector
import stylometry
import scoring

app = Flask(__name__)

from request_instrumentation import install_request_logging
install_request_logging(app)


# ── Rate limiting — UNIT 8 ────────────────────────────────────────────────────

class _LimiterOff:
    """Leave routes untouched when rate limiting is disabled."""

    def limit(self, *args, **kwargs):
        return lambda view: view


limiter = _LimiterOff()

if config.RATE_LIMITING_ENABLED:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address

    def rate_limit_key():
        """Use creator_id when available; otherwise use the caller's address."""
        payload = request.get_json(silent=True)

        if not isinstance(payload, dict):
            return get_remote_address()

        creator = payload.get("creator_id")

        return (
            creator
            if isinstance(creator, str) and creator.strip()
            else get_remote_address()
        )

    limiter = Limiter(
        key_func=rate_limit_key,
        app=app,
        storage_uri=config.RATE_LIMIT_STORAGE,
        default_limits=[],
    )

    @app.errorhandler(429)
    def rate_limited(exc):
        """Record requests rejected by the rate limiter."""
        payload = request.get_json(silent=True)

        if not isinstance(payload, dict):
            payload = {}

        audit.log_rejection(
            creator_id=payload.get("creator_id", "unknown"),
            reason="rate_limited",
            limit=str(exc.description),
        )

        return jsonify({
            "error": "rate_limited",
            "message": "Too many submissions. Try again shortly.",
            "limit": str(exc.description),
        }), 429


# ── The worked example. Already works. Don't edit. ────────────────────────────

@app.post("/ping")
def ping():
    """
    Everything a route needs, in six lines.

    JSON arrives as a dict. You pull things out of it. You return a dict and
    the framework turns it into a response. That's the whole idea.
    """
    payload = request.get_json(silent=True) or {}
    return jsonify({
        "ok": True,
        "you_sent": payload.get("message"),
        "service": "provenance-guard",
    })


@app.get("/health")
def health():
    """Is the service up, and has the model been loaded?"""
    import detector

    loaded = detector._model is not None

    return jsonify({
        "ok": True,
        "detector_model": config.DETECTOR_MODEL,
        "detector_loaded": loaded,
        "rate_limiting": config.RATE_LIMITING_ENABLED,
        "log_entries": len(audit.read_entries()),
    })


# ── Submission rejection logging ─────────────────────────────────────────────

def reject_submission(payload, reason, message, status_code):
    """Log an input rejection and return its JSON error response."""
    creator_id = "unknown"

    if isinstance(payload, dict):
        creator = payload.get("creator_id")

        if isinstance(creator, str) and creator.strip():
            creator_id = creator.strip()

    audit.log_rejection(
        creator_id=creator_id,
        reason=reason,
        status_code=status_code,
        route="/submit",
    )

    return jsonify({
        "error": reason,
        "message": message,
    }), status_code


# ── Submission endpoint ──────────────────────────────────────────────────────

@app.post("/submit")
@limiter.limit(
    f"{config.RATE_LIMIT_PER_MINUTE}/minute;"
    f"{config.RATE_LIMIT_PER_DAY}/day"
)
def submit():
    """Validate text, run both signals, record the decision, and respond."""
    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return reject_submission(
            payload,
            "invalid_input",
            "Send a JSON object with text and creator_id.",
            400,
        )

    text = payload.get("text")
    creator_id = payload.get("creator_id")

    if not isinstance(text, str) or not text.strip():
        return reject_submission(
            payload,
            "invalid_text",
            "Text is required and must be a nonempty string.",
            400,
        )

    text = text.strip()

    if len(text) < 50:
        return reject_submission(
            payload,
            "text_too_short",
            "Text must contain at least 50 characters.",
            400,
        )

    if len(text) > 10000:
        return reject_submission(
            payload,
            "text_too_long",
            "Text must contain no more than 10,000 characters.",
            413,
        )

    if not isinstance(creator_id, str) or not creator_id.strip():
        return reject_submission(
            payload,
            "invalid_creator_id",
            "creator_id must be a nonempty string.",
            400,
        )

    creator_id = creator_id.strip()
    content_id = str(uuid.uuid4())

    model_score = float(detector.model_signal(text))
    style_score = float(stylometry.style_signal(text))
    confidence = float(scoring.combine_signals(model_score, style_score))

    guess, label = scoring.score_to_label(confidence)

    audit.log_decision(
        content_id=content_id,
        creator_id=creator_id,
        guess=guess,
        model_score=model_score,
        style_score=style_score,
        combined_score=confidence,
        label=label,
        status="decided",
    )

    return jsonify({
        "content_id": content_id,
        "guess": guess,
        "confidence": confidence,
        "label": label,
        "model_score": model_score,
        "style_score": style_score,
    }), 200


# ── Appeal endpoint ──────────────────────────────────────────────────────────

@app.post("/appeal")
@app.post("/appeal")
def appeal():
    """Record a valid appeal without repeating the same explanation."""
    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify({
            "error": "invalid_input",
            "message": "Send a JSON object with content_id and reasoning."
        }), 400

    content_id = payload.get("content_id")
    reasoning = payload.get("reasoning")

    if not isinstance(content_id, str) or not content_id.strip():
        return jsonify({
            "error": "invalid_content_id",
            "message": "content_id must be a nonempty string."
        }), 400

    if not isinstance(reasoning, str) or not reasoning.strip():
        return jsonify({
            "error": "invalid_reasoning",
            "message": "Please provide your appeal explanation."
        }), 400

    content_id = content_id.strip()
    reasoning = reasoning.strip()

    if len(reasoning.split()) < 25:
        return jsonify({
            "error": "reasoning_too_short",
            "message": "Your explanation must contain at least 25 words."
        }), 400

    entries = audit.entries_for(content_id)
    decisions = [
        entry for entry in entries
        if entry.get("event") != "appeal"
        and "model_score" in entry
    ]

    if not decisions:
        return jsonify({
            "error": "content_not_found",
            "message": "No submission exists with that content_id."
        }), 404

    normalized_reasoning = " ".join(reasoning.split()).casefold()

    for entry in entries:
        if entry.get("event") == "appeal":
            previous_reasoning = " ".join(
                entry.get("reasoning", "").split()
            ).casefold()

            if previous_reasoning == normalized_reasoning:
                return jsonify({
                    "content_id": content_id,
                    "status": "under_review",
                    "message": (
                        "This explanation is already recorded. "
                        "No duplicate appeal was saved."
                    ),
                    "duplicate": True,
                }), 200

    audit.log_appeal(
        content_id=content_id,
        creator_id=decisions[0]["creator_id"],
        reasoning=reasoning,
    )

    return jsonify({
        "content_id": content_id,
        "status": "under_review",
        "message": (
            "Your appeal has been recorded for review. "
            "The writing has not been automatically rescored."
        ),
        "duplicate": False,
    }), 200


# ── Already works ─────────────────────────────────────────────────────────────

@app.get("/log")
def get_log():
    """
    The audit log, most recent last.

        curl "http://127.0.0.1:5000/log?limit=10"
    """
    limit = request.args.get("limit", type=int)
    entries = audit.read_entries(limit=limit)

    return jsonify({
        "count": len(entries),
        "entries": entries,
    })


def main():
    print(f"Provenance Guard on http://{config.HOST}:{config.PORT}")
    print(f"  detector model:  {config.DETECTOR_MODEL}")
    print(
        f"  rate limiting:   "
        f"{'ON' if config.RATE_LIMITING_ENABLED else 'off (unit 8)'}"
    )
    print(f"  audit log:       {config.AUDIT_LOG}")
    print()
    print("Check it's alive:")
    print(f'  curl -X POST http://{config.HOST}:{config.PORT}/ping \\')
    print('    -H "Content-Type: application/json" \\')
    print("    -d '{\"message\": \"hello\"}'")
    print()

    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG,
    )


if __name__ == "__main__":
    main()