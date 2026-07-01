"""Manifest records for controller candidates."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields, is_dataclass
from typing import Any
import re

_VERSIONED_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*_v\d+$")
_PLAIN_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")

_ALLOWED_STATUS = {
    "candidate",
    "promoted",
    "rejected",
    "archived",
    "deployment_candidate",
    "hardware_tested",
}


def _require_text(field_name: str,
                  field_value: str) -> None:
    """Require a non-empty text field in a manifest record."""

    if not isinstance(field_value, str) or not field_value:
        raise ValueError(f"{field_name} is required")


def _require_versioned_id(field_name: str,
                          field_value: str) -> None:
    """Require a lowercase snake-case identifier with a version suffix."""

    _require_text(field_name, field_value)
    if not _VERSIONED_ID_PATTERN.fullmatch(field_value):
        raise ValueError(f"{field_name} must be lowercase snake case ending in _vN")


@dataclass
class ArtifactRefs:
    """Relative artifact paths stored inside a controller candidate folder."""

    checkpoint: str | None = None
    resolved_config: str = "resolved_config.yaml"
    recipe: str = "recipe.yaml"
    reward_spec: str | None = None
    hyperparameters: str | None = None
    metrics: str = "metrics.jsonl"
    evaluations: str = "evaluations.jsonl"


@dataclass
class CandidateRecipe:
    """Versioned inputs that define a controller candidate's meaning."""

    action_interface_id: str
    observation_interface_id: str
    task_id: str
    reward_id: str
    algo_id: str
    backend_id: str
    robot_config_id: str
    mechanism_id: str

    def __post_init__(self) -> None:
        for recipe_field in fields(self):
            field_name = recipe_field.name
            field_value = getattr(self, field_name)
            _require_versioned_id(field_name, field_value)


@dataclass
class CandidateManifest:
    """Top-level metadata record for one controller candidate."""

    candidate_id: str
    run_id: str
    checkpoint_id: str
    parent_candidate_id: str | None
    created_at: str
    git_revision: str
    dirty_tree: bool
    training_layer: str
    status: str
    recipe: CandidateRecipe
    artifacts: ArtifactRefs
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _require_text("candidate_id", self.candidate_id)
        _require_text("run_id", self.run_id)
        _require_text("checkpoint_id", self.checkpoint_id)
        _require_text("created_at", self.created_at)
        _require_text("git_revision", self.git_revision)
        _require_text("training_layer", self.training_layer)
        if not _PLAIN_ID_PATTERN.fullmatch(self.training_layer):
            raise ValueError("training_layer must be lowercase snake case")
        if self.status not in _ALLOWED_STATUS:
            raise ValueError(f"status must be one of {sorted(_ALLOWED_STATUS)}")
        if not isinstance(self.recipe, CandidateRecipe):
            raise ValueError("recipe must be a CandidateRecipe")
        if not isinstance(self.artifacts, ArtifactRefs):
            raise ValueError("artifacts must be ArtifactRefs")


@dataclass
class MetricRecord:
    """One append-only training metric row for a candidate checkpoint."""

    candidate_id: str
    checkpoint_id: str
    step: int
    metrics: dict[str, float]

    def __post_init__(self) -> None:
        _require_text("candidate_id", self.candidate_id)
        _require_text("checkpoint_id", self.checkpoint_id)
        if self.step < 0:
            raise ValueError("step must be non-negative")


@dataclass
class EvaluationRecord:
    """One append-only deterministic evaluation result for a candidate."""

    candidate_id: str
    checkpoint_id: str
    evaluation_id: str
    validation_layer: str
    scenario_id: str
    seed: int
    passed: bool
    score: float
    metrics: dict[str, float]
    failure_reason: str | None = None

    def __post_init__(self) -> None:
        _require_text("candidate_id", self.candidate_id)
        _require_text("checkpoint_id", self.checkpoint_id)
        _require_text("evaluation_id", self.evaluation_id)
        _require_text("validation_layer", self.validation_layer)
        _require_versioned_id("scenario_id", self.scenario_id)


def record_to_dict(record: Any) -> dict[str, Any]:
    """Convert a dataclass or mapping record into a plain dictionary."""

    if is_dataclass(record):
        record_dict = asdict(record)
        return record_dict
    if isinstance(record, dict):
        return dict(record)
    raise TypeError(f"unsupported record type: {type(record).__name__}")


def candidate_recipe_from_dict(recipe_dict: dict[str, Any]) -> CandidateRecipe:
    """Build and validate a candidate recipe from serialized fields."""

    recipe = CandidateRecipe(**recipe_dict)
    return recipe


def artifact_refs_from_dict(artifact_dict: dict[str, Any]) -> ArtifactRefs:
    """Build artifact references from serialized fields."""

    artifacts = ArtifactRefs(**artifact_dict)
    return artifacts


def manifest_from_dict(manifest_dict: dict[str, Any]) -> CandidateManifest:
    """Build and validate a manifest from serialized YAML fields."""

    manifest_fields = dict(manifest_dict)
    manifest_fields["recipe"] = candidate_recipe_from_dict(manifest_fields["recipe"])
    manifest_fields["artifacts"] = artifact_refs_from_dict(manifest_fields["artifacts"])
    manifest = CandidateManifest(**manifest_fields)
    return manifest
