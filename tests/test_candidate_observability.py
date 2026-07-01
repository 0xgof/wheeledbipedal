from tests.test_candidate_store import make_manifest

from wheeled_biped_rl.observability.context import ExperimentContext, TraceContext
from wheeled_biped_rl.observability.events import ObservabilityEvent
from wheeled_biped_rl.registry.store import CandidateStore


def make_event(candidate_id: str) -> ObservabilityEvent:
    trace = TraceContext(trace_id="trace_test",
                         span_id="span_test",
                         parent_span_id=None)
    context = ExperimentContext(run_id="run_test",
                                candidate_id=candidate_id,
                                checkpoint_id="checkpoint_000001",
                                phase="training",
                                correlation_id="corr_test",
                                trace=trace)
    event = ObservabilityEvent.from_context(context=context,
                                           event_type="checkpoint_saved",
                                           message="checkpoint saved",
                                           level="info",
                                           step=100)
    return event


def test_candidate_store_creates_observability_stream(tmp_path) -> None:
    store = CandidateStore(tmp_path)
    manifest = make_manifest()

    candidate_dir = store.create_candidate(manifest)

    assert (candidate_dir / "observability.jsonl").is_file()
    loaded_manifest = store.read_manifest(manifest.candidate_id)
    assert loaded_manifest.artifacts.observability == "observability.jsonl"


def test_candidate_store_appends_and_reads_observability_events(tmp_path) -> None:
    store = CandidateStore(tmp_path)
    manifest = make_manifest()
    store.create_candidate(manifest)
    event = make_event(manifest.candidate_id)

    store.append_observability(event)
    loaded_events = store.read_observability(manifest.candidate_id)

    assert loaded_events == [event.to_dict()]
