# cod3s-pycatshoo

PyCATSHOO engine adapter for [muscadet](https://github.com/edgemind-sas/muscadet)
system declarations.

muscadet describes a system as a document, the *system declaration*, and knows
no simulation engine. An engine is a separate distribution that registers
itself at muscadet's extension point. This package is that distribution for
PyCATSHOO: it builds a PyCATSHOO system from a declaration and runs it, as a
Monte Carlo campaign, as a whole study, or as an interactive session.

## PyCATSHOO is not included

PyCATSHOO is a simulation engine developed by EDF R&D. It is **not**
distributed with this package, and this repository contains none of it. You
need your own PyCATSHOO installation, obtained from EDF under its own licence,
and the rights that licence gives you are the ones that apply to anything you
compute with it.

The adapter uses the public Python interface of the distributed PyCATSHOO
library, and nothing else.

PyCATSHOO has no Python distribution: it is found through `PYTHONPATH` and
loaded through `LD_LIBRARY_PATH`. Sourcing the `pycatshoorc` file of your
installation sets both:

```sh
export PYCATSHOO_DIR=<your PyCATSHOO installation>
. "$PYCATSHOO_DIR/pycatshoorc"
```

Where the library cannot be loaded, the adapter does not register, and muscadet
reports the reason when the engine is asked for.

## Installation

The adapter declares muscadet and cod3s by version range, without an embedded
URL. Neither is published on an index, so the project that installs the adapter
provides their git sources. With uv:

```toml
[project]
dependencies = ["cod3s-pycatshoo"]

[tool.uv.sources]
cod3s-pycatshoo = { git = "https://github.com/edgemind-sas/cod3s-pycatshoo.git", rev = "0.1.1" }
muscadet = { git = "https://github.com/edgemind-sas/muscadet.git", rev = "6.4.0" }
cod3s = { git = "https://github.com/edgemind-sas/cod3s.git", rev = "1.26.0" }
```

The cod3s reference must be the one the chosen muscadet release embeds.

Python `>=3.10,<3.11`, the interpreter line PyCATSHOO ships its native
libraries for.

## Usage

Installing the package is enough: muscadet discovers the engine through the
`muscadet.engines` entry point, under the name `pycatshoo`. Nothing imports
`cod3s_pycatshoo` by name.

```python
import muscadet

declaration = ...  # a muscadet system declaration (a dict)

# A campaign.
muscadet.simulate_declaration_on(
    "pycatshoo", declaration, {"nb_runs": 1000, "schedule": [0.0, 100.0]}
)

# A whole study, written under a directory.
run = muscadet.simulate_declaration_on(
    "pycatshoo", declaration, study=study, results_dir="results"
)

# An interactive session.
session = muscadet.isimu_start_declaration_on("pycatshoo", declaration)
```

PyCATSHOO allows a single live system per process. Run each declaration in a
process of its own, or drop the system you were handed back
(`cod3s_pycatshoo.system.drop_system`) before building another.

## Development

```sh
uv venv --python 3.10
uv pip install -r requirements-dev.txt -e .
export PYCATSHOO_DIR=<your PyCATSHOO installation>
. "$PYCATSHOO_DIR/pycatshoorc"
.venv/bin/python -m pytest
```

The suite needs PyCATSHOO and is refused by name without it. No continuous
integration runs it: the engine cannot be installed on a public runner. See
`CONVENTIONS.md` for the delivery rules.

## Licence

MIT, see `LICENSE`. The licence covers this adapter only, not PyCATSHOO.
