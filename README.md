# Fake Commit Planner (GUI)

Cross-platform Flutter desktop app to preview, schedule, run, and undo natural-looking commit histories with behavior-aware patterns.

## Status
- Skeleton project setup for Windows/macOS/Linux desktop.
- Core plan baked in code structure; logic is stubbed for later implementation.

## Prerequisites
- Flutter SDK with desktop targets enabled (`flutter config --enable-windows-desktop` / `--enable-macos-desktop` / `--enable-linux-desktop`).
- Git available on PATH.

## Run (dev)
```bash
flutter pub get
flutter run -d windows   # or macos/linux
```

## Structure (initial)
- `lib/main.dart` – entry point, placeholder shell.
- `lib/app_shell.dart` – app scaffold with routing placeholders.
- `lib/domain/models.dart` – configs and plan models.
- `lib/services/` – stubs for planner, git adapter, content generator, history fetch, snapshot/undo manager.
- `lib/features/` – UI placeholders for repo picker, identity, behavior config, preview, run, and history/undo.

## Next steps to implement
1) Wire Riverpod providers for configs and planner preview.
2) Implement behavior engine (weekday weights, holidays, trend, Poisson sampling, jitter, intra-day windows).
3) Implement Git adapter (author/committer date env, add/commit, optional push) with snapshot + undo using `--force-with-lease` after confirm.
4) Add history fetch (GraphQL + HTML scrape fallback) and holiday presets (including VN).
5) Build preview heatmap widget and dry-run export.
