"""Metadata helpers for controller-candidate provenance."""

from __future__ import annotations

from datetime import datetime, timezone
import subprocess


def current_timestamp() -> str:
    """Return the current UTC timestamp in compact ISO-8601 form."""

    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    utc_timestamp = timestamp.replace("+00:00", "Z")
    return utc_timestamp


def get_git_revision() -> str:
    """Return the current git commit hash, or ``unknown`` outside a repository."""

    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False)
    if completed.returncode != 0:
        return "unknown"
    git_revision = completed.stdout.strip()
    return git_revision


def is_dirty_tree() -> bool:
    """Return whether git reports local uncommitted changes."""

    completed = subprocess.run(
        ["git", "status", "--short"],
        capture_output=True,
        text=True,
        check=False)
    if completed.returncode != 0:
        return False
    dirty_tree = bool(completed.stdout.strip())
    return dirty_tree

