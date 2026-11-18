"""Capture submission and appeal requests without changing their responses."""

import time
import uuid

from flask import g, jsonify, request

from request_audit import write_request

TRACKED_ROUTES = {"/submit", "/appeal"}


def install_request_logging(app):
    @app.before_request
    def start_request_record():
        if request.path not in TRACKED_ROUTES:
            return

        g.request_started = time.perf_counter()
        g.request_record_id = str(uuid.uuid4())

        # Cache the body so reading it here does not consume it for the route.
        raw_body = request.get_data(cache=True, as_text=True)
        if request.is_json:
            parsed = request.get_json(silent=True)
            g.request_record_input = {
                "content_type": request.content_type,
                "body": raw_body,
                "json": parsed,
            }
        else:
            g.request_record_input = {
                "content_type": request.content_type,
                "body": raw_body,
            }

    @app.after_request
    def finish_request_record(response):
        if not hasattr(g, "request_started"):
            return response

        duration = time.perf_counter() - g.request_started
        output = response.get_json(silent=True)
        if not response.is_json:
            output = response.get_data(as_text=True)

        write_request(
            request_id=g.request_record_id,
            route=request.path,
            method=request.method,
            input_data=g.request_record_input,
            output_data=output,
            status_code=response.status_code,
            duration_seconds=duration,
        )

        return response


    @app.errorhandler(500)
    def record_server_error(error):
        """Return a JSON failure that the response hook can record."""
        if request.path not in TRACKED_ROUTES:
            return error

        return jsonify({
            "error": "internal_server_error",
            "message": "The request could not be completed.",
        }), 500
