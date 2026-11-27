import numpy as np
import pytest

from scripts.synthetic_evaluation import (
    audit_splits,
    classification_metrics,
    make_splits,
    ranking_metrics,
    run,
)


def test_double_holdout_excludes_rows_sharing_one_axis():
    sites, devices = np.indices((8, 8)).reshape(2, -1)
    splits = make_splits(sites, devices, np.random.default_rng(18))
    assert [len(folds) for folds in splits.values()] == [4, 4, 4, 16]
    for name, folds in splits.items():
        audit_splits(name, folds, sites, devices)
    for train, test in splits["doubly_blind"]:
        assert train.sum() == 36
        assert test.sum() == 4
        assert (~(train | test)).sum() == 24
    with pytest.raises(ValueError, match="group overlap"):
        audit_splits("doubly_blind", splits["leave_site_out"], sites, devices)


def test_known_metrics_and_ranking_ties():
    labels = np.array([0, 1, 1, 0])
    scores = np.array([0.5, 0.5, 0.9, 0.1])
    ranking = ranking_metrics(labels, scores, np.arange(4))
    assert ranking == {"recall_at_1": 0.5, "recall_at_3": 1.0, "recall_at_5": 1.0, "mrr": 1.0}
    assert ranking_metrics(np.zeros(4), scores, np.arange(4)) is None
    values = classification_metrics(labels, scores)
    assert values["average_precision"] == pytest.approx(5 / 6)
    assert values["brier"] == pytest.approx(0.13)
    assert classification_metrics(np.ones(4), scores)["auprc"] is None


def test_reproducible_simulation_and_bootstrap():
    evaluated = run(seed=7, repeats=4)
    assert evaluated == run(seed=7, repeats=4)
    for split in evaluated.values():
        assert sum(row["test"] for row in split["fold_counts"]) == 768
        scorecard = split["simulated_scores"]
        assert sum(row["count"] for row in scorecard["reliability"]) == 768
        low, high = scorecard["site_bootstrap_95"]["average_precision"]["bounds"]
        assert 0 <= low <= high <= 1
