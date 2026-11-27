"""An interactive session opens on a declaration and replays a transition."""

import muscadet
import pytest

from cod3s_pycatshoo.session import InteractiveSession
from cod3s_pycatshoo.system import drop_system

from .models import FEARED_EVENT, series_declaration


@pytest.fixture(scope="module")
def the_session():
    document = series_declaration("Session")
    session = muscadet.isimu_start_declaration_on(
        "pycatshoo", document, targets=[FEARED_EVENT]
    )
    yield {"session": session, "document": document}
    drop_system(session.system)


def test_the_session_is_started_on_the_declared_system(the_session):
    session = the_session["session"]
    assert isinstance(session, InteractiveSession)
    assert set(session.system.comp) == set(the_session["document"]["components"])
    assert session.engine.current_time == 0.0
    assert session.engine_version


def _fire_the_first_fireable(engine, date):
    """Plan the first fireable transition at ``date`` and step onto it.

    A stochastic transition has no date of its own in a session: the operator
    plans it, which is what makes the session a replay rather than a draw.
    """
    engine.replan(trans_id=0, date=date)
    return engine.step_forward()


def test_a_transition_is_fired_then_replayed(the_session):
    engine = the_session["session"].engine
    assert engine.fireable(), "a failure mode is waiting to occur"
    at_rest = engine.vars_current

    fired = _fire_the_first_fireable(engine, 3.0)
    assert fired.transitions, "the step fired the planned transition"
    assert engine.current_time == 3.0
    failed = engine.vars_current
    assert failed != at_rest

    assert engine.step_backward(), "the step is undone"
    assert engine.current_time == 0.0

    replayed = _fire_the_first_fireable(engine, 3.0)
    assert replayed.transitions
    assert engine.current_time == 3.0
    assert engine.vars_current == failed
