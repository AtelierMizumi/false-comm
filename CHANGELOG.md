# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2026-11-01

### Added

- **Replay dry-run**: `false-comm replay <ref> --dry-run` previews the semantic
  partition without creating commits, branches, or safety snapshots.
- **Replay JSON plan export**: `false-comm replay <ref> --json` emits a
  machine-readable plan for automation/CI. The flag implies `--dry-run` and
  never mutates the repository.
- **`comeback` behavior profile** for post-hiatus / summer catch-up / ramp-up
  activity patterns.
- **Intensity controls** for `backfill` and `preview` via
  `--intensity {light,normal,heavy,<float>}`.
- **Gap-filling mode** (`--fill-gaps`) to prioritize inactive days and avoid
  stacking commits on days that already have activity.
- **Vacation toggle** (`--no-vacation`) to disable synthetic vacation blackout
  periods.

### Changed

- Behavior planner now supports gap-aware planning using existing commit counts.
- Added `--timezone` override support to `backfill`.

### Fixed

- Windows compatibility: guard `tzset` usage behind a platform check so mypy and
  runtime behave safely on Windows.
- English celebrate card now shows "Target Branch" instead of a Vietnamese
  label.

### Tests & CI

- Added integration coverage for real `backfill`, `replay`, and `undo`
  execution paths, plus Mission Control wizard wiring.
- Added parser tests for intensity values and JSON payload schema tests.
- Total test suite: 97 tests; project coverage: 87%.
- CI and release pipelines now enforce a minimum coverage of 80%.

## [2.0.0] - 2026-09-29

- Initial public release of the Python CLI rewrite: backfill, preview, replay,
  undo, doctor, audit, and behavior profiles, with Linux/macOS/Windows packaging.
