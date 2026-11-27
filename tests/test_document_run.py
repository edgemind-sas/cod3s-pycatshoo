"""A document runs on PyCATSHOO, and what ran reports the document it came from.

    system -> document -> PyCATSHOO -> the document that run reports

A system is declared and torn down, and the document alone is handed to the
engine through muscadet's seam. The system the engine built then reports, at
its own run, the very document it was built from: anything the declaration
drops on the way out, or invents on the way in, separates the two ends.

``source_cls`` is the one key excluded: it names the class a declaration was
READ BACK from, and a system built from a document has the document for origin.
"""

import muscadet
import pytest

from cod3s_pycatshoo.system import drop_system

from .models import FEARED_EVENT, series_declaration, without_provenance

RUN_PARAMS = {"nb_runs": 5, "schedule": [0.0, 5.0, 10.0], "seed": 4242}


@pytest.fixture(scope="module")
def the_run_from_a_document():
    document = series_declaration("RefDocRun")
    rebuilt = muscadet.System(name=document["name"])
    try:
        result = muscadet.simulate_declaration_on(
            "pycatshoo", document, RUN_PARAMS, system=rebuilt, targets=[FEARED_EVENT]
        )
    except BaseException:
        drop_system(rebuilt)
        raise
    yield {
        "document": document,
        "system": rebuilt,
        "result": result,
        "reported": rebuilt.run_declaration,
    }
    drop_system(rebuilt)


def test_the_engine_built_what_the_document_declared(the_run_from_a_document):
    assert set(the_run_from_a_document["system"].comp) == set(
        the_run_from_a_document["document"]["components"]
    )


def test_the_run_reports_the_document_it_was_built_from(the_run_from_a_document):
    assert without_provenance(the_run_from_a_document["reported"]) == (
        without_provenance(the_run_from_a_document["document"])
    )


def test_the_provenance_says_the_build_came_from_the_document(
    the_run_from_a_document,
):
    reported = the_run_from_a_document["reported"]["components"]
    assert reported["Src"]["source_cls"] == "ObjFlow"
    assert the_run_from_a_document["document"]["components"]["Src"]["source_cls"] == (
        "Source"
    )


def test_a_target_named_beside_the_document_reached_the_run(the_run_from_a_document):
    assert FEARED_EVENT in muscadet.declared_events(the_run_from_a_document["reported"])
    assert (
        muscadet.declared_occurrence_state(
            the_run_from_a_document["reported"], FEARED_EVENT
        )
        == "occ"
    )
