# Changelog

All notable changes to PyShiny Hunter will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-10-28

Initial release of PyShiny Hunter - an automated shiny hunting system for Pokemon Black 2.

### Features

- **Enhanced OCR**: 2x LANCZOS4 upscaling with 100% accuracy on test dataset
- **GPU Acceleration**: CUDA/DirectML support for 5-10x faster processing
- **Multi-Worker Mode**: Run multiple emulator instances with automatic RNG desynchronization
- **Unified GUI**: Real-time ImGui interface with live video feeds and statistics
- **Smart Detection**: Brightness analysis with configurable thresholds and dynamic Pokemon whitelist
- **Persistent Logging**: JSON export of shiny discoveries and encounter statistics (`shiny_log.json`, `encounter_stats.json`)

### Performance

- Fast multi-worker startup: 3.5 seconds vs 2+ minutes (40x improvement)
- Responsive grid layouts supporting 12+ workers
- Per-worker FPS tracking with aggregate statistics

### Documentation

- Multi-process architecture guide ([docs/UNIFIED_GUI.md](docs/UNIFIED_GUI.md))
- Data exploration notebook with 1,934 analyzed frames
- Complete inline documentation

### Testing & Quality

- 91% test coverage (26 passing tests)
- Pre-commit hooks (MyPy, Ruff, Black, Bandit)
- Type checking and linting enforced

---

[Unreleased]: https://github.com/Konstantysz/pyshiny-hunter/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Konstantysz/pyshiny-hunter/releases/tag/v0.1.0
