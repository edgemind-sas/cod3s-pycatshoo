"""A whole study run on PyCATSHOO, from a system declaration.

A study is more than a campaign: simulation settings, result tables, sequence
analysis, all written under a results directory. At this stage the run is
delegated to ``cod3s.scripts.study_runner.run_study``, handed a builder that
builds the system from the declaration.

What the declaration already carries (failure modes, events, indicators) is
not applied a second time: the caller hands a study whose sections the document
covers are empty, and what is left configures the run.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from .engine import native_engine_version
from .system import build_system, order_indicators, watch_event_crossings


@dataclass(frozen=True)
class StudyRun:
    """What a study run hands back.

    ``system`` is the live PyCATSHOO system after the campaign, for a caller
    that wants to inspect it; that caller inherits the constraint of one live
    system per process.
    """

    #: The system the campaign ran on.
    system: Any
    #: The version the native PyCATSHOO library reports.
    engine_version: str
    #: How many components the system holds, modes and events included.
    components: int


class DeclarationBuilder:
    """A ``cod3s.scripts.builders.SystemBuilder`` that builds from a declaration."""

    def __init__(
        self,
        spec: dict,
        *,
        indicator_order: Iterable[str] | None = None,
        system: Any = None,
    ) -> None:
        self.spec = spec
        self.indicator_order = list(indicator_order) if indicator_order else None
        self._system = system

    def build(self, *, logger: Any = None) -> Any:
        system = build_system(self.spec, system=self._system)
        order_indicators(system, self.indicator_order)
        watched = watch_event_crossings(system)
        if logger is not None and watched:
            logger.info1(f"{watched} event(s) watched by the continuous solver")
        return system

    def __repr__(self) -> str:
        return "DeclarationBuilder()"


def run_study(
    spec: dict,
    study: Any,
    *,
    results_dir: Any,
    logger: Any = None,
    indicator_order: Iterable[str] | None = None,
    system: Any = None,
) -> StudyRun:
    """Run ``study`` on the system ``spec`` declares, and write its results.

    Parameters
    ----------
    spec : dict
        A muscadet system declaration.
    study : dict or cod3s.specs.StudyYaml
        The study, without the sections the declaration already carries.
    results_dir : path-like
        Where the result tables and the sequence artefacts are written.
    logger : optional
        Receives the run's log stream (``info1``/``info2``/``info3``,
        ``warning``, ``error``).
    indicator_order : iterable of str, optional
        The order the result tables list the indicators in. A system built from
        a declaration holds them sorted by name, which is rarely the order the
        study wrote them in.
    system : muscadet.System, optional
        An empty system to fill.
    """
    from cod3s.scripts.study_runner import run_study as cod3s_run_study

    builder = DeclarationBuilder(spec, indicator_order=indicator_order, system=system)
    ran = cod3s_run_study(
        system_builder=builder,
        study=study,
        results_dir=results_dir,
        logger=logger,
    )
    try:
        components = len(ran.comp or {})
    except Exception:
        components = 0
    return StudyRun(
        system=ran,
        engine_version=native_engine_version(),
        components=components,
    )
