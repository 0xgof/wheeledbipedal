"""Command-line interface for the local controller-candidate registry."""

from __future__ import annotations

from pathlib import Path
import argparse
import json
import sys

from wheeled_biped_rl.registry.index import rebuild_indexes
from wheeled_biped_rl.registry.query import compare_candidate_interfaces
from wheeled_biped_rl.registry.store import CandidateStore


def _load_index_records(root: Path) -> list[dict]:
    """Load candidate index rows, rebuilding the index if it is absent."""

    index_path = root / "indexes" / "candidates.jsonl"
    if not index_path.is_file():
        rebuild_indexes(root)
    records = []
    if index_path.is_file():
        for index_line in index_path.read_text(encoding="utf-8").splitlines():
            records.append(json.loads(index_line))
    return records


def _matches_filters(record: dict, args: argparse.Namespace) -> bool:
    """Return whether an index row satisfies list-command filters."""

    filters = {
        "task_id": args.task,
        "reward_id": args.reward,
        "backend_id": args.backend,
        "status": args.status,
    }
    for field_name, expected_value in filters.items():
        if expected_value is not None and record.get(field_name) != expected_value:
            return False
    return True


def _handle_list(root: Path, args: argparse.Namespace) -> int:
    """Print candidate ids matching the supplied filters."""

    records = _load_index_records(root)
    for record in records:
        if _matches_filters(record, args):
            print(record["candidate_id"])
    return 0


def _handle_show(root: Path, args: argparse.Namespace) -> int:
    """Print one candidate manifest as JSON."""

    store = CandidateStore(root)
    manifest = store.read_manifest(args.candidate_id)
    print(json.dumps(manifest.__dict__, default=lambda item: item.__dict__, indent=2))
    return 0


def _handle_compare(root: Path, args: argparse.Namespace) -> int:
    """Compare two candidates and print recipe-id mismatches."""

    store = CandidateStore(root)
    first_manifest = store.read_manifest(args.first_candidate_id)
    second_manifest = store.read_manifest(args.second_candidate_id)
    comparison = compare_candidate_interfaces(first_manifest, second_manifest)
    if comparison.compatible:
        print("compatible")
        return 0
    for field_name, values in comparison.mismatches.items():
        print(f"{field_name}: {values[0]} != {values[1]}")
    return 1


def _handle_status_transition(root: Path,
                              args: argparse.Namespace,
                              status: str) -> int:
    """Apply a lifecycle status transition and print the new status."""

    store = CandidateStore(root)
    store.transition_status(candidate_id=args.candidate_id,
                            status=status,
                            reason=args.reason,
                            evaluator=args.evaluator)
    print(status)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the registry CLI argument parser."""

    parser = argparse.ArgumentParser(prog="candidate-registry")
    parser.add_argument("--root", default="runs")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("index")

    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--task")
    list_parser.add_argument("--reward")
    list_parser.add_argument("--backend")
    list_parser.add_argument("--status")

    show_parser = subparsers.add_parser("show")
    show_parser.add_argument("candidate_id")

    compare_parser = subparsers.add_parser("compare")
    compare_parser.add_argument("first_candidate_id")
    compare_parser.add_argument("second_candidate_id")

    for command_name in ("promote", "reject", "archive"):
        status_parser = subparsers.add_parser(command_name)
        status_parser.add_argument("candidate_id")
        status_parser.add_argument("--reason", required=True)
        status_parser.add_argument("--evaluator")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the registry CLI and return a process-style exit code."""

    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.root)

    if args.command == "index":
        rebuild_indexes(root)
        return 0
    if args.command == "list":
        return _handle_list(root, args)
    if args.command == "show":
        return _handle_show(root, args)
    if args.command == "compare":
        return _handle_compare(root, args)
    if args.command == "promote":
        return _handle_status_transition(root, args, "promoted")
    if args.command == "reject":
        return _handle_status_transition(root, args, "rejected")
    if args.command == "archive":
        return _handle_status_transition(root, args, "archived")
    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
