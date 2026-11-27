"""muscadet finds PyCATSHOO as a registered engine, without importing it by name."""

import importlib.metadata
import subprocess
import sys
import textwrap

import muscadet
import muscadet.engine

from cod3s_pycatshoo import ENGINE_NAME


def test_the_distribution_advertises_the_engine():
    advertised = {
        entry.name: entry.value
        for entry in importlib.metadata.entry_points(group="muscadet.engines")
    }
    assert advertised[ENGINE_NAME] == "cod3s_pycatshoo.engine:register"


def test_muscadet_discovers_it_through_the_entry_point():
    muscadet.engine.reset_engines()
    try:
        assert ENGINE_NAME in muscadet.registered_engines()
        engine = muscadet.get_engine(ENGINE_NAME)
        assert engine.simulate is not None
        assert engine.isimu_start is not None
    finally:
        muscadet.engine.reset_engines()


def test_importing_the_package_loads_nothing_native():
    """Listing what is installed must not cost more than a metadata read."""
    probe = textwrap.dedent(
        """
        import sys
        import cod3s_pycatshoo  # noqa: F401
        import cod3s_pycatshoo.engine  # noqa: F401
        heavy = ("Pycatshoo", "cod3s", "muscadet")
        loaded = sorted(name for name in heavy if name in sys.modules)
        print(loaded)
        """
    )
    done = subprocess.run(
        [sys.executable, "-c", probe], capture_output=True, text=True, check=True
    )
    assert done.stdout.strip() == "[]"


#: Makes PyCATSHOO unfindable, which is what a machine without it looks like.
_BLOCK_THE_ENGINE = textwrap.dedent(
    """
    import importlib.abc
    import sys


    class _NoEngine(importlib.abc.MetaPathFinder):
        def find_spec(self, name, path=None, target=None):
            if name == "Pycatshoo" or name.startswith("Pycatshoo."):
                raise ModuleNotFoundError("no Pycatshoo here", name="Pycatshoo")
            return None


    sys.meta_path.insert(0, _NoEngine())
    """
)


def test_registration_is_refused_where_the_native_library_is_missing():
    """Installed and unable to run is said by name, not discovered mid-campaign."""
    probe = _BLOCK_THE_ENGINE + textwrap.dedent(
        """
        import muscadet

        print(sorted(muscadet.registered_engines()))
        try:
            muscadet.get_engine("pycatshoo")
        except muscadet.UnknownEngineError as error:
            print(error)
        """
    )
    done = subprocess.run(
        [sys.executable, "-c", probe], capture_output=True, text=True, check=True
    )
    listed, _, reason = done.stdout.partition("\n")
    assert "pycatshoo" not in listed
    assert "NativeEngineMissingError" in reason
    assert "LD_LIBRARY_PATH" in reason
