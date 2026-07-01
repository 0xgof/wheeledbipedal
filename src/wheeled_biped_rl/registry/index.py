"""Derived indexes for local controller-candidate queries."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from wheeled_biped_rl.registry.manifest import record_to_dict
from wheeled_biped_rl.registry.store import CandidateStore


@dataclass
class IndexPaths:
    """Paths to the derived registry index files."""

    candidates: Path
    evaluations: Path


def _candidate_index_record(manifest) -> dict:
    """Flatten one candidate manifest into a JSONL-friendly index row."""

    manifest_dict = record_to_dict(manifest)
    recipe_dict = manifest_dict.pop("recipe")
    index_record = {
        "candidate_id": manifest.candidate_id,
        "run_id": manifest.run_id,
        "checkpoint_id": manifest.checkpoint_id,
        "status": manifest.status,
        "training_layer": manifest.training_layer,
        **recipe_dict,
    }
    return index_record


def rebuild_indexes(root: str | Path) -> IndexPaths:
    """Rebuild derived candidate and evaluation indexes from manifest folders."""

    store = CandidateStore(root)
    index_root = Path(root) / "indexes"
    index_root.mkdir(parents=True, exist_ok=True)
    candidate_index_path = index_root / "candidates.jsonl"
    evaluation_index_path = index_root / "evaluations.jsonl"

    candidate_records = []
    if store.candidates_root.exists():
        for manifest_path in sorted(store.candidates_root.glob("*/candidate.yaml")):
            manifest = store.read_manifest(manifest_path.parent.name)
            candidate_records.append(_candidate_index_record(manifest))

    with candidate_index_path.open("w", encoding="utf-8") as candidate_file:
        for candidate_record in candidate_records:
            json_line = json.dumps(candidate_record, sort_keys=True)
            candidate_file.write(json_line + "\n")

    with evaluation_index_path.open("w", encoding="utf-8") as evaluation_file:
        if store.candidates_root.exists():
            for evaluation_path in sorted(store.candidates_root.glob("*/evaluations.jsonl")):
                for evaluation_line in evaluation_path.read_text(encoding="utf-8").splitlines():
                    evaluation_file.write(evaluation_line + "\n")

    index_paths = IndexPaths(candidates=candidate_index_path,
                             evaluations=evaluation_index_path)
    return index_paths
