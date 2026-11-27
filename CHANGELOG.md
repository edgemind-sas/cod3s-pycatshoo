# Changelog

## 0.1.0

First release. PyCATSHOO becomes an engine registered at muscadet's extension
point, like any other, instead of a special case written into muscadet.

- The distribution advertises `pycatshoo` under the `muscadet.engines` entry
  point group. muscadet discovers it without importing it by name.
- `simulate` runs a system declaration as a Monte Carlo campaign, or as a whole
  study when handed a `study` and a `results_dir`.
- `isimu_start` opens an interactive session on a declaration.
- Registration is refused where the PyCATSHOO native library cannot be loaded,
  with the reason, so that the engines registered with muscadet are the engines
  the interpreter can run.

At this stage the adapter delegates: muscadet's `declare.build_system` builds
the system and cod3s 1.x runs it. Requires muscadet 6.4.0 (or 6.0.4 on the 6.0
maintenance line) and cod3s 1.26.
