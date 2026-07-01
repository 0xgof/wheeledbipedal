"""Filesystem store for controller-candidate artifacts.

The store owns the on-disk layout under a runs-like root directory. It deliberately
does not depend on training frameworks, simulators, or ROS so it can be used by local
tests, HPC jobs, and later validation runners.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json

import yaml

from wheeled_biped_rl.registry.manifest import (
    CandidateManifest,
    MetricRecord,
    StatusTransition,
    manifest_from_dict,
    record_to_dict,
)
from wheeled_biped_rl.registry.metadata import current_timestamp


class CandidateStore:
    """File-backed store for local controller-candidate artifacts.

    A store rooted at ``runs`` writes candidates under ``runs/candidates`` and derived
    indexes under ``runs/indexes``. Methods prefer explicit candidate ids so training
    and validation jobs can resume or append to known candidate folders.
    """

    def __init__(self, root: str | Path) -> None:
        """Initialize a store rooted at a runs-like directory.

        Args:
            root: Directory containing ``candidates/`` and later ``indexes/``.
        """

        self.root = Path(root)
        self.candidates_root = self.root / "candidates"

    def candidate_dir(self, candidate_id: str) -> Path:
        """Return the directory path for a candidate id.

        Args:
            candidate_id: Controller-candidate identifier.

        Returns:
            Path to the candidate folder, whether or not it already exists.
        """

        candidate_path = self.candidates_root / candidate_id
        return candidate_path

    def create_candidate(self, manifest: CandidateManifest) -> Path:
        """Create the folder layout and initial files for one candidate.

        The method writes the manifest, recipe snapshot, empty resolved config, empty
        metric/evaluation streams, and artifact subdirectories. It fails if the
        candidate directory already exists so accidental id reuse is visible.

        Args:
            manifest: Validated manifest to persist.

        Returns:
            Path to the created candidate directory.
        """

        candidate_path = self.candidate_dir(manifest.candidate_id)
        candidate_path.mkdir(parents=True, exist_ok=False)
        for artifact_dir in ("checkpoints", "exports", "artifacts"):
            (candidate_path / artifact_dir).mkdir()

        self.write_manifest(manifest)
        self._write_yaml(candidate_path / "recipe.yaml", record_to_dict(manifest.recipe))
        self._write_yaml(candidate_path / "resolved_config.yaml", {})
        (candidate_path / "metrics.jsonl").write_text("", encoding="utf-8")
        (candidate_path / "evaluations.jsonl").write_text("", encoding="utf-8")
        return candidate_path

    def write_manifest(self, manifest: CandidateManifest) -> None:
        """Write a candidate manifest to its candidate folder.

        Args:
            manifest: Manifest to serialize as ``candidate.yaml``.
        """

        candidate_path = self.candidate_dir(manifest.candidate_id)
        manifest_path = candidate_path / "candidate.yaml"
        self._write_yaml(manifest_path, record_to_dict(manifest))

    def read_manifest(self, candidate_id: str) -> CandidateManifest:
        """Read and validate a candidate manifest from disk.

        Args:
            candidate_id: Candidate whose ``candidate.yaml`` should be loaded.

        Returns:
            Reconstructed and validated manifest.
        """

        manifest_path = self.candidate_dir(candidate_id) / "candidate.yaml"
        manifest_dict = self._read_yaml(manifest_path)
        manifest = manifest_from_dict(manifest_dict)
        return manifest

    def append_metric(self, metric_record: MetricRecord) -> None:
        """Append one training metric record to the candidate metrics stream.

        Args:
            metric_record: Metric record serialized as one JSONL row.
        """

        metric_path = self.candidate_dir(metric_record.candidate_id) / "metrics.jsonl"
        self._append_jsonl(metric_path, record_to_dict(metric_record))

    def append_evaluation(self, evaluation_record: Any) -> None:
        """Append one evaluation record to the candidate evaluations stream.

        Args:
            evaluation_record: Dataclass or dictionary containing at least
                ``candidate_id`` and evaluation fields.
        """

        evaluation_dict = record_to_dict(evaluation_record)
        evaluation_path = (self.candidate_dir(evaluation_dict["candidate_id"])
                           / "evaluations.jsonl")
        self._append_jsonl(evaluation_path, evaluation_dict)

    def read_evaluations(self, candidate_id: str) -> list[dict[str, Any]]:
        """Read all evaluation records for a candidate.

        Args:
            candidate_id: Candidate whose ``evaluations.jsonl`` should be read.

        Returns:
            Evaluation records in append order.
        """

        evaluation_path = self.candidate_dir(candidate_id) / "evaluations.jsonl"
        evaluations = []
        for evaluation_line in evaluation_path.read_text(encoding="utf-8").splitlines():
            evaluations.append(json.loads(evaluation_line))
        return evaluations

    def transition_status(self,
                          candidate_id: str,
                          status: str,
                          reason: str,
                          evaluator: str | None = None) -> StatusTransition:
        """Update candidate status and append a lifecycle transition record.

        Args:
            candidate_id: Candidate to update.
            status: New lifecycle status.
            reason: Human-readable reason for the transition.
            evaluator: Optional process, gate, or person making the decision.

        Returns:
            The transition record that was appended to the manifest history.
        """

        manifest = self.read_manifest(candidate_id)
        transition = StatusTransition(status=status,
                                      reason=reason,
                                      created_at=current_timestamp(),
                                      evaluator=evaluator)
        manifest.status = status
        manifest.status_history.append(transition)
        self.write_manifest(manifest)
        return transition

    def write_reward_spec(self,
                          candidate_id: str,
                          reward_spec: dict[str, Any]) -> None:
        """Write a candidate-local reward spec snapshot and update the manifest.

        Args:
            candidate_id: Candidate receiving the snapshot.
            reward_spec: Reward specification mapping to serialize as YAML.
        """

        candidate_path = self.candidate_dir(candidate_id)
        self._write_yaml(candidate_path / "reward_spec.yaml", reward_spec)
        manifest = self.read_manifest(candidate_id)
        manifest.artifacts.reward_spec = "reward_spec.yaml"
        self.write_manifest(manifest)

    def write_hyperparameters(self,
                              candidate_id: str,
                              hyperparameters: dict[str, Any]) -> None:
        """Write a candidate-local hyperparameter snapshot and update the manifest.

        Args:
            candidate_id: Candidate receiving the snapshot.
            hyperparameters: Algorithm and training hyperparameters to serialize.
        """

        candidate_path = self.candidate_dir(candidate_id)
        self._write_yaml(candidate_path / "hyperparameters.yaml", hyperparameters)
        manifest = self.read_manifest(candidate_id)
        manifest.artifacts.hyperparameters = "hyperparameters.yaml"
        self.write_manifest(manifest)

    def _append_jsonl(self,
                      jsonl_path: Path,
                      json_record: dict[str, Any]) -> None:
        """Append one JSON-serializable record to a JSONL file.

        The file is opened in append mode so existing metrics/evaluations are never
        rewritten during normal training.
        """

        json_line = json.dumps(json_record, sort_keys=True)
        with jsonl_path.open("a", encoding="utf-8") as output_file:
            output_file.write(json_line + "\n")

    def _write_yaml(self,
                    yaml_path: Path,
                    yaml_record: dict[str, Any]) -> None:
        """Write a dictionary as YAML using stable key ordering.

        Stable ordering keeps diffs and candidate artifacts easier to review.
        """

        yaml_text = yaml.safe_dump(yaml_record, sort_keys=True)
        yaml_path.write_text(yaml_text, encoding="utf-8")

    def _read_yaml(self, yaml_path: Path) -> dict[str, Any]:
        """Read a YAML mapping, treating empty files as empty dictionaries.

        Returns:
            Parsed YAML mapping. Empty YAML files become ``{}``.
        """

        yaml_record = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        if yaml_record is None:
            yaml_record = {}
        return yaml_record
