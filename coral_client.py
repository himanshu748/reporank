import subprocess
import json
import shutil
import time
import re
from typing import Any


def _coral_available() -> bool:
    return shutil.which("coral") is not None


def query(sql: str) -> list[dict[str, Any]]:
    """
    Run a SQL query via Coral CLI.
    Returns list of row dicts, or raises RuntimeError with stderr on failure.
    """
    if not _coral_available():
        raise RuntimeError(
            "Coral CLI not found. Install it:\n"
            "  brew install withcoral/tap/coral\n"
            "Then add your sources:\n"
            "  coral source add github\n"
            "  coral source add npm        (for JS packages)\n"
            "  coral source add pypi       (for Python packages)\n"
        )

    max_retries = 2
    for attempt in range(max_retries + 1):
        result = subprocess.run(
            ["coral", "sql", "--format", "json", sql],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            raw = result.stdout.strip()
            if not raw:
                return []
            return json.loads(raw)

        stderr = result.stderr.strip()
        if "rate limit exceeded" in stderr.lower() and attempt < max_retries:
            sleep_time = 5
            match = re.search(r"retry after (\d+)s", stderr.lower())
            if match:
                sleep_time = int(match.group(1)) + 1
            print(f"Coral rate limited. Retrying in {sleep_time}s... (Attempt {attempt + 1}/{max_retries})")
            time.sleep(sleep_time)
            continue

        raise RuntimeError(f"Coral query failed:\n{stderr}")


def query_one(sql: str) -> dict[str, Any] | None:
    """Return first row, or None if empty."""
    rows = query(sql)
    return rows[0] if rows else None
