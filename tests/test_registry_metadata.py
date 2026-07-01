from datetime import datetime

from wheeled_biped_rl.registry.metadata import (
    current_timestamp,
    get_git_revision,
    is_dirty_tree,
)


def test_current_timestamp_is_utc_iso_string() -> None:
    timestamp = current_timestamp()

    parsed_timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    assert timestamp.endswith("Z")
    assert parsed_timestamp.tzinfo is not None


def test_git_revision_is_non_empty_for_repository() -> None:
    git_revision = get_git_revision()

    assert len(git_revision) >= 7


def test_dirty_tree_status_is_boolean() -> None:
    dirty_tree = is_dirty_tree()

    assert isinstance(dirty_tree, bool)

