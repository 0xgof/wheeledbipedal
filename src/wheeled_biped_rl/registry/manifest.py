"""Manifest records for controller candidates.

This module defines the serializable records stored in candidate folders. The
records are deliberately small dataclasses with explicit validation so registry
files remain human-readable YAML/JSONL while still rejecting missing or malformed
candidate-defining fields.
"""

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
    """Require a non-empty text field in a manifest record.

    Args:
        field_name: Name used in the validation error.
        field_value: Value expected to be a non-empty string.

    Raises:
        ValueError: If the field is missing, non-text, or empty.
    """

    if not isinstance(field_value, str) or not field_value:
        raise ValueError(f"{field_name} is required")


def _require_versioned_id(field_name: str,
                          field_value: str) -> None:
    """Require a lowercase snake-case identifier with a version suffix.

    Versioned ids make compatibility checks explicit. Examples include
    ``balance_v1``, ``hip_wheel_4d_v1``, and ``python_sim_v1``.
    """

    _require_text(field_name, field_value)
    if not _VERSIONED_ID_PATTERN.fullmatch(field_value):
        raise ValueError(f"{field_name} must be lowercase snake case ending in _vN")


@dataclass
class ArtifactRefs:
    """Relative artifact paths stored inside a controller candidate folder.

    Paths are intentionally relative so a candidate folder can be moved, archived, or
    synced from an HPC run without rewriting manifest contents.
    """

    checkpoint: str | None = None
    resolved_config: str = "resolved_config.yaml"
    recipe: str = "recipe.yaml"
    reward_spec: str | None = None
    hyperparameters: str | None = None
    metrics: str = "metrics.jsonl"
    evaluations: str = "evaluations.jsonl"


@dataclass
class StatusTransition:
    """One lifecycle status change for a controller candidate.

    Attributes:
        status: New candidate lifecycle status.
        reason: Human-readable reason for the transition.
        created_at: UTC timestamp for the transition.
        evaluator: Optional person, process, or gate that made the decision.
    """

    status: str
    reason: str
    created_at: str
    evaluator: str | None = None

    def __post_init__(self) -> None:
        """Validate status transition fields after dataclass construction."""

        if self.status not in _ALLOWED_STATUS:
            raise ValueError(f"status must be one of {sorted(_ALLOWED_STATUS)}")
        _require_text("reason", self.reason)
        _require_text("created_at", self.created_at)


@dataclass
class CandidateRecipe:
    """Versioned inputs that define a controller candidate's meaning.

    A recipe is the compatibility contract for a checkpoint. Candidates with
    different recipe ids may both be valid but should not be directly compared as if
    they were trained under the same assumptions.
    """

    action_interface_id: str
    observation_interface_id: str
    task_id: str
    reward_id: str
    algo_id: str
    backend_id: str
    robot_config_id: str
    mechanism_id: str

    def __post_init__(self) -> None:
        """Validate every recipe id as a versioned lowercase identifier."""

        for recipe_field in fields(self):
            field_name = recipe_field.name
            field_value = getattr(self, field_name)
            _require_versioned_id(field_name, field_value)


@dataclass
class CandidateManifest:
    """Top-level metadata record for one controller candidate.

    The manifest is the primary entry point for a candidate folder. It connects
    candidate identity, code provenance, lifecycle state, candidate-defining recipe
    ids, and relative artifact paths.
    """

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
    status_history: list[StatusTransition] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate required identity, lifecycle, recipe, and artifact fields."""

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
        for transition in self.status_history:
            if not isinstance(transition, StatusTransition):
                raise ValueError("status_history must contain StatusTransition records")


@dataclass
class MetricRecord:
    """One append-only training metric row for a candidate checkpoint.

    Metric records are written as JSONL so long-running training jobs can append
    progress without rewriting existing artifacts.
    """

    candidate_id: str
    checkpoint_id: str
    step: int
    metrics: dict[str, float]

    def __post_init__(self) -> None:
        """Validate metric identity and non-negative training step."""

        _require_text("candidate_id", self.candidate_id)
        _require_text("checkpoint_id", self.checkpoint_id)
        if self.step < 0:
            raise ValueError("step must be non-negative")


@dataclass
class EvaluationRecord:
    """One append-only deterministic evaluation result for a candidate.

    Evaluation records are separate from training metrics because they represent a
    named scenario, seed, validation layer, and pass/fail outcome.
    """

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
        """Validate evaluation identity and versioned scenario id."""

        _require_text("candidate_id", self.candidate_id)
        _require_text("checkpoint_id", self.checkpoint_id)
        _require_text("evaluation_id", self.evaluation_id)
        _require_text("validation_layer", self.validation_layer)
        _require_versioned_id("scenario_id", self.scenario_id)


def record_to_dict(record: Any) -> dict[str, Any]:
    """Convert a dataclass or mapping record into a plain dictionary.

    Args:
        record: Dataclass instance or mapping-like dictionary.

    Returns:
        A plain dictionary suitable for YAML or JSON serialization.
    """

    if is_dataclass(record):
        record_dict = asdict(record)
        return record_dict
    if isinstance(record, dict):
        return dict(record)
    raise TypeError(f"unsupported record type: {type(record).__name__}")


def candidate_recipe_from_dict(recipe_dict: dict[str, Any]) -> CandidateRecipe:
    """Build and validate a candidate recipe from serialized fields.

    Args:
        recipe_dict: Mapping loaded from a manifest or recipe YAML file.

    Returns:
        Validated ``CandidateRecipe`` instance.
    """

    recipe = CandidateRecipe(**recipe_dict)
    return recipe


def artifact_refs_from_dict(artifact_dict: dict[str, Any]) -> ArtifactRefs:
    """Build artifact references from serialized fields.

    Args:
        artifact_dict: Mapping loaded from serialized manifest artifact fields.

    Returns:
        ``ArtifactRefs`` with default paths filled where fields are omitted.
    """

    artifacts = ArtifactRefs(**artifact_dict)
    return artifacts


def status_transition_from_dict(transition_dict: dict[str, Any]) -> StatusTransition:
    """Build a status transition from serialized fields.

    Args:
        transition_dict: Mapping loaded from manifest ``status_history``.

    Returns:
        Validated lifecycle transition record.
    """

    transition = StatusTransition(**transition_dict)
    return transition


def manifest_from_dict(manifest_dict: dict[str, Any]) -> CandidateManifest:
    """Build and validate a manifest from serialized YAML fields.

    Args:
        manifest_dict: Mapping loaded from ``candidate.yaml``.

    Returns:
        Validated ``CandidateManifest`` with nested records reconstructed.
    """

    manifest_fields = dict(manifest_dict)
    manifest_fields["recipe"] = candidate_recipe_from_dict(manifest_fields["recipe"])
    manifest_fields["artifacts"] = artifact_refs_from_dict(manifest_fields["artifacts"])
    status_history = manifest_fields.get("status_history", [])
    manifest_fields["status_history"] = [
        status_transition_from_dict(transition_dict)
        for transition_dict in status_history
    ]
    manifest = CandidateManifest(**manifest_fields)
    return manifest
