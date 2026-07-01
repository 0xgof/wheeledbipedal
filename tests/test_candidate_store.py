import json

import pytest

from wheeled_biped_rl.registry.manifest import (
    ArtifactRefs,
    CandidateManifest,
    CandidateRecipe,
    MetricRecord,
)
from wheeled_biped_rl.registry.store import CandidateStore


def make_recipe() -> CandidateRecipe:
    return CandidateRecipe(
        action_interface_id="hip_wheel_4d_v1",
        observation_interface_id="actor_obs_balance_v1",
        task_id="stand_balance_v1",
        reward_id="balance_v1",
        algo_id="ppo_foundation_v1",
        backend_id="python_sim_v1",
        robot_config_id="robot_config_wheeled_biped_v1",
        mechanism_id="mechanism_rigid_no_spring_v1")


def make_manifest() -> CandidateManifest:
    return CandidateManifest(
        candidate_id="cand_20260701_120000_balance_ab12cd",
        run_id="run_20260701_115500_ppo_balance_ef34gh",
        checkpoint_id="checkpoint_000000",
        parent_candidate_id=None,
        created_at="2026-07-01T12:00:00Z",
        git_revision="abc123",
        dirty_tree=False,
        training_layer="foundational",
        status="candidate",
        recipe=make_recipe(),
        artifacts=ArtifactRefs())


def test_store_creates_candidate_layout(tmp_path) -> None:
    store = CandidateStore(tmp_path)
    manifest = make_manifest()

    candidate_dir = store.create_candidate(manifest)

    assert (candidate_dir / "candidate.yaml").is_file()
    assert (candidate_dir / "recipe.yaml").is_file()
    assert (candidate_dir / "resolved_config.yaml").is_file()
    assert (candidate_dir / "metrics.jsonl").is_file()
    assert (candidate_dir / "evaluations.jsonl").is_file()
    assert (candidate_dir / "checkpoints").is_dir()
    assert (candidate_dir / "exports").is_dir()
    assert (candidate_dir / "artifacts").is_dir()


def test_manifest_round_trips_through_store(tmp_path) -> None:
    store = CandidateStore(tmp_path)
    manifest = make_manifest()

    store.create_candidate(manifest)
    loaded_manifest = store.read_manifest(manifest.candidate_id)

    assert loaded_manifest == manifest


def test_store_appends_metric_records_without_overwriting(tmp_path) -> None:
    store = CandidateStore(tmp_path)
    manifest = make_manifest()
    store.create_candidate(manifest)

    first_metric = MetricRecord(
        candidate_id=manifest.candidate_id,
        checkpoint_id="checkpoint_000001",
        step=1,
        metrics={"reward": 1.0})
    second_metric = MetricRecord(
        candidate_id=manifest.candidate_id,
        checkpoint_id="checkpoint_000002",
        step=2,
        metrics={"reward": 2.0})

    store.append_metric(first_metric)
    store.append_metric(second_metric)

    metric_path = store.candidate_dir(manifest.candidate_id) / "metrics.jsonl"
    records = [json.loads(line) for line in metric_path.read_text().splitlines()]

    assert [record["step"] for record in records] == [1, 2]


def test_store_rejects_missing_required_manifest_fields() -> None:
    with pytest.raises(ValueError, match="candidate_id"):
        CandidateManifest(
            candidate_id="",
            run_id="run_20260701_115500_ppo_balance_ef34gh",
            checkpoint_id="checkpoint_000000",
            parent_candidate_id=None,
            created_at="2026-07-01T12:00:00Z",
            git_revision="abc123",
            dirty_tree=False,
            training_layer="foundational",
            status="candidate",
            recipe=make_recipe(),
            artifacts=ArtifactRefs())

