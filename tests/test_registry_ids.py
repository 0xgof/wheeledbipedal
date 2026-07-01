import re

from wheeled_biped_rl.registry.ids import make_candidate_id, make_run_id


def test_candidate_ids_have_stable_prefix_and_slug() -> None:
    candidate_id = make_candidate_id("balance trial")

    assert re.fullmatch(r"cand_\d{8}_\d{6}_balance_trial_[a-z0-9]{6}", candidate_id)


def test_run_ids_have_stable_prefix_and_slug() -> None:
    run_id = make_run_id("ppo balance")

    assert re.fullmatch(r"run_\d{8}_\d{6}_ppo_balance_[a-z0-9]{6}", run_id)

