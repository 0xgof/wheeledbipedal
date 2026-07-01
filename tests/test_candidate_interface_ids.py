import pytest

from wheeled_biped_rl.registry.manifest import CandidateRecipe
from wheeled_biped_rl.registry.query import compare_candidate_interfaces

from tests.test_candidate_store import make_manifest, make_recipe


def test_candidate_recipe_requires_interface_ids() -> None:
    with pytest.raises(ValueError, match="action_interface_id"):
        CandidateRecipe(
            action_interface_id="",
            observation_interface_id="actor_obs_balance_v1",
            task_id="stand_balance_v1",
            reward_id="balance_v1",
            algo_id="ppo_foundation_v1",
            backend_id="python_sim_v1",
            robot_config_id="robot_config_wheeled_biped_v1",
            mechanism_id="mechanism_rigid_no_spring_v1")


def test_candidate_recipe_rejects_malformed_ids() -> None:
    with pytest.raises(ValueError, match="reward_id"):
        CandidateRecipe(
            action_interface_id="hip_wheel_4d_v1",
            observation_interface_id="actor_obs_balance_v1",
            task_id="stand_balance_v1",
            reward_id="Balance V1",
            algo_id="ppo_foundation_v1",
            backend_id="python_sim_v1",
            robot_config_id="robot_config_wheeled_biped_v1",
            mechanism_id="mechanism_rigid_no_spring_v1")


def test_compare_reports_interface_mismatch() -> None:
    first_manifest = make_manifest()
    second_manifest = make_manifest()
    second_manifest.recipe = make_recipe()
    second_manifest.recipe.observation_interface_id = "actor_obs_balance_v2"

    comparison = compare_candidate_interfaces(first_manifest, second_manifest)

    assert comparison.compatible is False
    assert comparison.mismatches == {
        "observation_interface_id": ("actor_obs_balance_v1", "actor_obs_balance_v2")
    }

