from wheeled_biped_rl.registry.cli import main
from wheeled_biped_rl.registry.store import CandidateStore

from tests.test_candidate_store import make_manifest


def test_cli_lists_candidates_by_task(tmp_path, capsys) -> None:
    store = CandidateStore(tmp_path)
    manifest = make_manifest()
    store.create_candidate(manifest)

    exit_code = main(["--root", str(tmp_path), "list", "--task", "stand_balance_v1"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert manifest.candidate_id in captured.out


def test_cli_compare_reports_mismatches(tmp_path, capsys) -> None:
    store = CandidateStore(tmp_path)
    first_manifest = make_manifest()
    second_manifest = make_manifest()
    second_manifest.candidate_id = "cand_20260701_121000_balance_bc23de"
    second_manifest.recipe.backend_id = "mujoco_v1"
    store.create_candidate(first_manifest)
    store.create_candidate(second_manifest)

    exit_code = main([
        "--root", str(tmp_path), "compare",
        first_manifest.candidate_id, second_manifest.candidate_id,
    ])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "backend_id" in captured.out

