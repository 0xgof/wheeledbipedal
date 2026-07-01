from wheeled_biped_rl.registry.store import CandidateStore

from tests.test_candidate_store import make_manifest


def test_store_writes_reward_and_hyperparameter_snapshots(tmp_path) -> None:
    store = CandidateStore(tmp_path)
    manifest = make_manifest()
    store.create_candidate(manifest)

    reward_spec = {
        "reward_id": "balance_v1",
        "components": {"upright": {"weight": 1.0}},
    }
    hyperparameters = {
        "algo_id": "ppo_foundation_v1",
        "learning_rate": 0.0003,
    }

    store.write_reward_spec(manifest.candidate_id, reward_spec)
    store.write_hyperparameters(manifest.candidate_id, hyperparameters)

    candidate_dir = store.candidate_dir(manifest.candidate_id)
    loaded_manifest = store.read_manifest(manifest.candidate_id)

    assert (candidate_dir / "reward_spec.yaml").is_file()
    assert (candidate_dir / "hyperparameters.yaml").is_file()
    assert loaded_manifest.artifacts.reward_spec == "reward_spec.yaml"
    assert loaded_manifest.artifacts.hyperparameters == "hyperparameters.yaml"

