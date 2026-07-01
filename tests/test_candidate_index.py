from wheeled_biped_rl.registry.index import rebuild_indexes
from wheeled_biped_rl.registry.store import CandidateStore

from tests.test_candidate_store import make_manifest


def test_rebuild_index_discovers_candidate_manifests(tmp_path) -> None:
    store = CandidateStore(tmp_path)
    manifest = make_manifest()
    store.create_candidate(manifest)

    index_paths = rebuild_indexes(tmp_path)

    candidate_index = index_paths.candidates
    index_text = candidate_index.read_text(encoding="utf-8")

    assert manifest.candidate_id in index_text
    assert "stand_balance_v1" in index_text

