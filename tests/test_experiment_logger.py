import json

from wheeled_biped_rl.observability.context import ExperimentContext, TraceContext
from wheeled_biped_rl.observability.logger import JsonlExperimentLogger


def make_context() -> ExperimentContext:
    trace = TraceContext(trace_id="trace_test",
                         span_id="span_test",
                         parent_span_id=None)
    context = ExperimentContext(run_id="run_test",
                                candidate_id="cand_test",
                                checkpoint_id="checkpoint_000001",
                                phase="training",
                                correlation_id="corr_test",
                                trace=trace)
    return context


def test_jsonl_experiment_logger_writes_metadata_and_events(tmp_path) -> None:
    log_path = tmp_path / "observability.jsonl"
    logger = JsonlExperimentLogger(log_path)

    logger.start(make_context(), metadata={"backend": "python_sim_v1"})
    logger.info(event_type="episode_start",
                message="episode started",
                step=0,
                episode=1,
                payload={"seed": 123})
    logger.debug(event_type="reward",
                 message="reward calculated",
                 step=1,
                 episode=1,
                 metrics={"reward": 0.5})
    logger.close()

    records = [json.loads(line)
               for line in log_path.read_text(encoding="utf-8").splitlines()]

    assert [record["record_type"] for record in records] == [
        "metadata",
        "event",
        "event",
    ]
    assert records[0]["metadata"]["backend"] == "python_sim_v1"
    assert records[1]["event"]["event_type"] == "episode_start"
    assert records[1]["event"]["correlation_id"] == "corr_test"
    assert records[2]["event"]["metrics"]["reward"] == 0.5


def test_jsonl_experiment_logger_records_exceptions_with_trace_fields(tmp_path) -> None:
    log_path = tmp_path / "observability.jsonl"
    logger = JsonlExperimentLogger(log_path)
    logger.start(make_context(), metadata={})

    try:
        raise RuntimeError("sim exploded")
    except RuntimeError as exc:
        logger.exception(event_type="simulation_error",
                         message="simulation failed",
                         exc=exc,
                         step=10,
                         episode=3)
    logger.close()

    records = [json.loads(line)
               for line in log_path.read_text(encoding="utf-8").splitlines()]
    event_record = records[1]["event"]

    assert event_record["level"] == "error"
    assert event_record["event_type"] == "simulation_error"
    assert event_record["payload"]["exception_type"] == "RuntimeError"
    assert event_record["payload"]["exception_message"] == "sim exploded"
    assert event_record["trace_id"] == "trace_test"
