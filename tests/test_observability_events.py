from wheeled_biped_rl.observability.context import ExperimentContext, TraceContext
from wheeled_biped_rl.observability.events import ObservabilityEvent


def make_context() -> ExperimentContext:
    trace = TraceContext(trace_id="trace_test",
                         span_id="span_test",
                         parent_span_id="span_parent")
    context = ExperimentContext(run_id="run_test",
                                candidate_id="cand_test",
                                checkpoint_id="checkpoint_000001",
                                phase="training",
                                correlation_id="corr_test",
                                trace=trace)
    return context


def test_observability_event_serializes_correlation_and_trace_fields() -> None:
    event = ObservabilityEvent.from_context(context=make_context(),
                                           event_type="reward_component",
                                           message="reward component calculated",
                                           level="debug",
                                           step=42,
                                           episode=2,
                                           metrics={"reward": 1.5},
                                           payload={"component": "balance"})

    event_dict = event.to_dict()
    loaded_event = ObservabilityEvent.from_dict(event_dict)

    assert loaded_event == event
    assert event_dict["run_id"] == "run_test"
    assert event_dict["candidate_id"] == "cand_test"
    assert event_dict["checkpoint_id"] == "checkpoint_000001"
    assert event_dict["correlation_id"] == "corr_test"
    assert event_dict["trace_id"] == "trace_test"
    assert event_dict["span_id"] == "span_test"
    assert event_dict["parent_span_id"] == "span_parent"
    assert event_dict["metrics"]["reward"] == 1.5
    assert event_dict["payload"]["component"] == "balance"


def test_observability_event_rejects_missing_correlation_id() -> None:
    event_dict = ObservabilityEvent.from_context(context=make_context(),
                                                event_type="debug",
                                                message="debug event").to_dict()
    event_dict["correlation_id"] = ""

    try:
        ObservabilityEvent.from_dict(event_dict)
    except ValueError as exc:
        assert "correlation_id is required" in str(exc)
    else:
        raise AssertionError("missing correlation id should fail")
