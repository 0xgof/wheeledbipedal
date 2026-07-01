"""Metadata helpers for controller-candidate provenance.

These helpers centralize the small pieces of run metadata that every controller
candidate should capture: wall-clock creation time, code revision, and whether the
working tree had uncommitted changes.
"""

from __future__ import annotations

from datetime import datetime, timezone
import subprocess


def current_timestamp() -> str:
    """Return the current UTC timestamp in compact ISO-8601 form.

    Returns:
        A UTC timestamp ending in ``Z`` with second precision.
    """

    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    utc_timestamp = timestamp.replace("+00:00", "Z")
    return utc_timestamp


def get_git_revision() -> str:
    """Return the current git commit hash.

    Returns:
        The full git ``HEAD`` hash, or ``"unknown"`` if the command cannot run.
    """

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
    """Return whether git reports local uncommitted changes.

    Returns:
        ``True`` when ``git status --short`` reports any local changes. Returns
        ``False`` outside a git repository so callers can still create manifests in
        temporary or packaged contexts.
    """

    completed = subprocess.run(
        ["git", "status", "--short"],
        capture_output=True,
        text=True,
        check=False)
    if completed.returncode != 0:
        return False
    dirty_tree = bool(completed.stdout.strip())
    return dirty_tree
