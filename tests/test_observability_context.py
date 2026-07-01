from wheeled_biped_rl.observability.context import (
    ExperimentContext,
    TraceContext,
    make_experiment_context,
)


def test_experiment_context_generates_correlation_and_trace_ids() -> None:
    context = make_experiment_context(run_id="run_test",
                                      candidate_id="cand_test",
                                      checkpoint_id="checkpoint_000001",
                                      phase="training")

    assert context.run_id == "run_test"
    assert context.candidate_id == "cand_test"
    assert context.checkpoint_id == "checkpoint_000001"
    assert context.phase == "training"
    assert context.correlation_id.startswith("corr_")
    assert context.trace.trace_id.startswith("trace_")
    assert context.trace.span_id.startswith("span_")
    assert context.trace.parent_span_id is None


def test_child_span_keeps_trace_id_and_sets_parent_span() -> None:
    parent_trace = TraceContext(trace_id="trace_parent",
                                span_id="span_parent",
                                parent_span_id=None)
    context = ExperimentContext(run_id="run_test",
                                candidate_id="cand_test",
                                checkpoint_id="checkpoint_000001",
                                phase="training",
                                correlation_id="corr_test",
                                trace=parent_trace)

    child_context = context.child_span(phase="environment_step")

    assert child_context.phase == "environment_step"
    assert child_context.correlation_id == "corr_test"
    assert child_context.trace.trace_id == "trace_parent"
    assert child_context.trace.parent_span_id == "span_parent"
    assert child_context.trace.span_id.startswith("span_")
