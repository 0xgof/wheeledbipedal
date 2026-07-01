import json

from wheeled_biped_rl.registry.manifest import StatusTransition
from wheeled_biped_rl.registry.store import CandidateStore

from tests.test_candidate_store import make_manifest


def test_store_records_status_transition_with_reason(tmp_path) -> None:
    store = CandidateStore(tmp_path)
    manifest = make_manifest()
    store.create_candidate(manifest)

    transition = store.transition_status(
        candidate_id=manifest.candidate_id,
        status="promoted",
        reason="passed balance gate",
        evaluator="pytest")

    loaded_manifest = store.read_manifest(manifest.candidate_id)

    assert isinstance(transition, StatusTransition)
    assert loaded_manifest.status == "promoted"
    assert loaded_manifest.status_history[-1].status == "promoted"
    assert loaded_manifest.status_history[-1].reason == "passed balance gate"
    assert loaded_manifest.status_history[-1].evaluator == "pytest"


def test_store_appends_and_reads_evaluation_records(tmp_path) -> None:
    store = CandidateStore(tmp_path)
    manifest = make_manifest()
    store.create_candidate(manifest)
    evaluation_record = {
        "candidate_id": manifest.candidate_id,
        "checkpoint_id": "checkpoint_000001",
        "evaluation_id": "eval_balance_nominal_001",
        "validation_layer": "foundational",
        "scenario_id": "balance_nominal_v1",
        "seed": 123,
        "passed": True,
        "score": 0.95,
        "metrics": {"survival_time_s": 20.0},
        "failure_reason": None,
    }

    store.append_evaluation(evaluation_record)

    evaluations = store.read_evaluations(manifest.candidate_id)

    assert evaluations == [evaluation_record]
    evaluation_path = store.candidate_dir(manifest.candidate_id) / "evaluations.jsonl"
    assert json.loads(evaluation_path.read_text().strip()) == evaluation_record

