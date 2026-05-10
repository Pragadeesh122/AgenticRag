"""Subprocess management for the orchestrator and log parsing."""

import json
import subprocess
import sys
import threading
import time

SEPARATOR = "----" * 30


def _drain_stderr(pipe, log_lines: list):
    """Read stderr in a background thread to prevent deadlocks."""
    for line in pipe:
        log_lines.append(line.rstrip("\n"))


def send_prompt(
    proc: subprocess.Popen, stderr_logs: list, prompt: str, timeout: int = 120
) -> dict:
    """Send a prompt to the running orchestrator and capture its reply."""
    log_snapshot_start = len(stderr_logs)

    proc.stdin.write(prompt + "\n")
    proc.stdin.flush()

    output_lines = []
    start = time.time()

    while True:
        if time.time() - start > timeout:
            timeout_logs = stderr_logs[log_snapshot_start:]
            return {
                "response": "\n".join(output_lines),
                "logs": timeout_logs,
                "tools_used": _extract_tools(timeout_logs),
                "cache_hits": _extract_cache_hits(timeout_logs),
                "error": "timeout",
            }

        line = proc.stdout.readline()
        if not line:
            break

        line = line.rstrip("\n")

        if line == SEPARATOR:
            break
        else:
            output_lines.append(line)

    new_logs = stderr_logs[log_snapshot_start:]
    return {
        "response": "\n".join(output_lines).strip(),
        "logs": new_logs,
        "tools_used": _extract_tools(new_logs),
        "cache_hits": _extract_cache_hits(new_logs),
        "error": None,
    }


def _extract_tools(log_lines: list[str]) -> list[str]:
    """Parse tool names from orchestrator log lines."""
    tools_used = []
    for log in log_lines:
        if "tool_calls:" in log:
            try:
                bracket = log.split("tool_calls:")[1]
                names = json.loads(bracket.split("(")[0].strip().replace("'", '"'))
                tools_used.extend(names)
            except Exception:
                pass
    return tools_used


def _extract_cache_hits(log_lines: list[str]) -> list[str]:
    """Parse cache hit entries from orchestrator log lines."""
    hits = []
    for log in log_lines:
        if "cache hit for" in log:
            try:
                part = log.split("cache hit for")[1].strip()
                tool = part.split(":")[0].strip()
                hits.append(tool)
            except Exception:
                pass
    return hits


def start_orchestrator() -> tuple[subprocess.Popen, list]:
    """Start main.py as a subprocess. Returns (process, shared_stderr_logs)."""
    proc = subprocess.Popen(
        [sys.executable, "-u", "main.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    stderr_logs = []
    t = threading.Thread(
        target=_drain_stderr, args=(proc.stderr, stderr_logs), daemon=True
    )
    t.start()

    # consume the "Hello from RunaxAI!" banner
    proc.stdout.readline()
    return proc, stderr_logs


def stop_orchestrator(proc: subprocess.Popen):
    """Gracefully shut down the orchestrator."""
    try:
        proc.stdin.write("exit\n")
        proc.stdin.flush()
        proc.wait(timeout=15)
    except Exception:
        proc.kill()
