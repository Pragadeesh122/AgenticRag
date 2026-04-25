"""Structured logging configuration."""

import json
import logging
import os
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """Outputs log records as single-line JSON."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            entry["exception"] = self.formatException(record.exc_info)
        # Include OpenTelemetry trace ID if available
        trace_id = getattr(record, "otelTraceID", "0" * 32)
        if trace_id != "0" * 32:
            entry["trace_id"] = trace_id
        span_id = getattr(record, "otelSpanID", "0" * 16)
        if span_id != "0" * 16:
            entry["span_id"] = span_id
        return json.dumps(entry, default=str)


def setup_logging() -> None:
    """Configure root logger based on LOG_FORMAT env var.

    LOG_FORMAT=json  -> JSON lines (for production / log aggregation)
    Otherwise        -> plain text (for local development)
    """
    log_format = os.getenv("LOG_FORMAT", "text").lower()
    level = os.getenv("LOG_LEVEL", "INFO").upper()

    root = logging.getLogger()
    root.setLevel(level)

    # Remove existing handlers to avoid duplicates
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    if log_format == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(name)s | %(message)s")
        )

    root.addHandler(handler)
