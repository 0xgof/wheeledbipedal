import json

from tests.test_candidate_store import make_manifest
from tests.test_visualization_recorder import make_frame

from wheeled_biped_rl.observability.context import ExperimentContext, TraceContext
from wheeled_biped_rl.observability.logger import JsonlExperimentLogger
from wheeled_biped_rl.registry.manifest import MetricRecord
from wheeled_biped_rl.registry.store import CandidateStore
from wheeled_biped_rl.visualization.recorder import JsonlTrajectorySink


def make_context(candidate_id: str,
                 phase: str = "registry") -> ExperimentContext:
    trace = TraceContext(trace_id="trace_test",
                         span_id="span_test",
                         parent_span_id=None)
    context = ExperimentContext(run_id="run_test",
                                candidate_id=candidate_id,
                                checkpoint_id="checkpoint_000001",
                                phase=phase,
                                correlation_id="corr_test",
                                trace=trace)
    return context


def test_candidate_store_optionally_logs_lifecycle_events(tmp_path) -> None:
    store = CandidateStore(tmp_path)
    manifest = make_manifest()
    context = make_context(manifest.candidate_id)

    store.create_candidate(manifest, observability_context=context)
    store.transition_status(candidate_id=manifest.candidate_id,
                            status="promoted",
                            reason="passed smoke validation",
                            evaluator="unit_test",
                            observability_context=context)

    events = store.read_observability(manifest.candidate_id)

    assert [event["event_type"] for event in events] == [
        "candidate_created",
        "candidate_status_transitioned",
    ]
    assert events[0]["correlation_id"] == "corr_test"
    assert events[0]["trace_id"] == "trace_test"
    assert events[0]["payload"]["training_layer"] == "foundational"
    assert events[1]["payload"]["status"] == "promoted"
    assert events[1]["payload"]["reason"] == "passed smoke validation"


def test_candidate_store_optionally_logs_metric_and_evaluation_events(tmp_path) -> None:
    store = CandidateStore(tmp_path)
    manifest = make_manifest()
    context = make_context(manifest.candidate_id)
    store.create_candidate(manifest)
    metric = MetricRecord(candidate_id=manifest.candidate_id,
                          checkpoint_id="checkpoint_000001",
                          step=10,
                          metrics={"reward": 1.25})
    evaluation = {
        "candidate_id": manifest.candidate_id,
        "checkpoint_id": "checkpoint_000001",
        "evaluation_id": "eval_001",
        "validation_layer": "foundational",
        "scenario_id": "balance_nominal_v1",
        "seed": 1,
        "passed": True,
        "score": 0.8,
        "metrics": {"duration_s": 5.0},
    }

    store.append_metric(metric, observability_context=context)
    store.append_evaluation(evaluation, observability_context=context)
    events = store.read_observability(manifest.candidate_id)

    assert [event["event_type"] for event in events] == [
        "metric_appended",
        "evaluation_appended",
    ]
    assert events[0]["step"] == 10
    assert events[0]["metrics"]["reward"] == 1.25
    assert events[1]["payload"]["evaluation_id"] == "eval_001"
    assert events[1]["payload"]["scenario_id"] == "balance_nominal_v1"


def test_trajectory_sink_optionally_logs_recording_summary(tmp_path) -> None:
    observability_path = tmp_path / "observability.jsonl"
    trajectory_path = tmp_path / "trajectory.jsonl"
    logger = JsonlExperimentLogger(observability_path)
    context = make_context("cand_test", phase="visualization")
    logger.start(context, metadata={})
    sink = JsonlTrajectorySink(trajectory_path, observability_logger=logger)

    sink.start({"source": "unit_test"})
    sink.consume(make_frame(1))
    sink.consume(make_frame(2))
    sink.close()
    logger.close()

    records = [json.loads(line)
               for line in observability_path.read_text(encoding="utf-8").splitlines()]
    events = [record["event"]
              for record in records
              if record["record_type"] == "event"]

    assert [event["event_type"] for event in events] == [
        "trajectory_recording_started",
        "trajectory_recording_closed",
    ]
    assert events[0]["payload"]["trajectory_path"] == str(trajectory_path)
    assert events[1]["payload"]["frame_count"] == 2
