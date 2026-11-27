"""Suite-wide check: the suite needs PyCATSHOO, and says so by name without it.

Without this, every test module that builds a system fails on its own import
and nothing names the cause. The few tests that are ABOUT the engine's absence
simulate it in a subprocess of their own.
"""

import pytest

from cod3s_pycatshoo.engine import NativeEngineMissingError, native_engine


def pytest_configure(config):
    try:
        native_engine()
    except NativeEngineMissingError as error:
        raise pytest.UsageError(
            f"cod3s-pycatshoo's test suite cannot run here: {error}"
        ) from error
