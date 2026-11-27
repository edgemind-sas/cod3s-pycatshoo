"""A whole study runs from a declaration and writes its result table."""

import csv

import muscadet
import pytest

from cod3s_pycatshoo.study import StudyRun
from cod3s_pycatshoo.system import drop_system

from .models import series_declaration

STUDY = {
    "name": "series study",
    "simulation": {
        "nb_runs": 20,
        "seed": 4242,
        "schedule": [{"start": 0.0, "end": 10.0, "nvalues": 3}],
    },
    "results": {"indicators": [{"id": "indicators", "output": ["csv"]}]},
}


@pytest.fixture(scope="module")
def the_study_run(tmp_path_factory):
    results_dir = tmp_path_factory.mktemp("results")
    document = series_declaration("StudyRun")
    run = muscadet.simulate_declaration_on(
        "pycatshoo", document, study=STUDY, results_dir=results_dir
    )
    yield {"run": run, "results_dir": results_dir, "document": document}
    drop_system(run.system)


def test_the_run_hands_back_what_ran(the_study_run):
    run = the_study_run["run"]
    assert isinstance(run, StudyRun)
    assert run.components == len(the_study_run["document"]["components"])
    assert run.engine_version


def test_the_result_table_is_written(the_study_run):
    table = the_study_run["results_dir"] / "indicators.csv"
    assert table.is_file()
    with table.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows, "the campaign reduced nothing"


def test_a_study_run_refuses_campaign_parameters():
    """One source for the run's parameters: the study, or the call, never both."""
    from cod3s_pycatshoo.engine import simulate

    with pytest.raises(TypeError, match="takes its parameters from the study"):
        simulate({}, {"nb_runs": 2}, study=STUDY, results_dir="unused")


def test_a_study_run_needs_somewhere_to_write():
    from cod3s_pycatshoo.engine import simulate

    with pytest.raises(TypeError, match="results_dir"):
        simulate({}, study=STUDY)
