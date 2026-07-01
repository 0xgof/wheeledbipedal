"""Query helpers for controller-candidate manifests.

The registry intentionally distinguishes candidate identity from candidate
compatibility. Two candidates can both exist and still be incompatible for direct
comparison if their action, observation, reward, backend, robot, or mechanism ids
differ.
"""

from __future__ import annotations

from dataclasses import dataclass

from wheeled_biped_rl.registry.manifest import CandidateManifest

_COMPATIBILITY_FIELDS = (
    "action_interface_id",
    "observation_interface_id",
    "task_id",
    "reward_id",
    "algo_id",
    "backend_id",
    "robot_config_id",
    "mechanism_id",
)


@dataclass
class CompatibilityComparison:
    """Compatibility result for two controller-candidate manifests.

    Attributes:
        compatible: ``True`` when all candidate-defining recipe ids match.
        mismatches: Mapping of field name to ``(first_value, second_value)`` for
            every incompatible recipe id.
    """

    compatible: bool
    mismatches: dict[str, tuple[str, str]]


def compare_candidate_interfaces(first_candidate: CandidateManifest,
                                 second_candidate: CandidateManifest
                                 ) -> CompatibilityComparison:
    """Compare candidate-defining recipe ids and report mismatches.

    Args:
        first_candidate: First manifest to compare.
        second_candidate: Second manifest to compare.

    Returns:
        A compatibility report listing all differing recipe ids.
    """

    mismatches = {}
    for field_name in _COMPATIBILITY_FIELDS:
        first_value = getattr(first_candidate.recipe, field_name)
        second_value = getattr(second_candidate.recipe, field_name)
        if first_value != second_value:
            mismatches[field_name] = (first_value, second_value)

    compatible = len(mismatches) == 0
    comparison = CompatibilityComparison(compatible=compatible, mismatches=mismatches)
    return comparison
