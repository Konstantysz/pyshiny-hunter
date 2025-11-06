# Changelog

All notable changes to PyShiny Hunter will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-15

### Added

- 🎯 **Automated Shiny Detection** - Frame counting and sparkle detection
- 🔍 **Enhanced OCR Pipeline** - 3-stage (EasyOCR + SymSpell + Fuzzy) with 100% accuracy
- ⚡ **GPU Acceleration** - Optional CUDA support for 5-10× faster OCR
- 📊 **Encounter Tracking** - Real-time logging and statistics
- 🎮 **DeSmuME Integration** - Full emulator control and screen capture
- 🖼️ **Real-time GUI** - ImGui-based monitoring interface
- ⚙️ **State Machine Architecture** - Clean, extensible design
- 🚀 **Multi-Process Mode** - Run multiple emulators simultaneously
- 📈 **Centralized Statistics** - Shared encounter tracking across workers
- 🎨 **Unified GUI** - Professional grid layout with aggregate stats
- 🔄 **RNG Desynchronization** - Hybrid progressive + random approach (40× faster)
- 📊 **Shiny Log Panel** - Track all shiny discoveries with metadata
- 🧪 **Test Suite** - 26 tests with 91% core coverage
- 📝 **Comprehensive Documentation** - API docs, user guides, architecture diagrams
- 🔧 **Configuration System** - Centralized tuning parameters
- 📦 **Package Distribution** - Installable via pip

### Technical Highlights

- **Phase 1-13 Complete** - Production-ready codebase
- **Multi-Platform CI/CD** - GitHub Actions (Ubuntu/Windows × Python 3.9-3.12)
- **Code Quality** - Ruff linting, Black formatting, MyPy type checking
- **Data Validation** - 1,934 real-world frames analyzed
- **Performance Optimizations** - Queue buffering, texture reuse, lazy OCR

### Breaking Changes

None (initial release)

---

## [Unreleased]

### Planned Features

- Additional game support (Black/White, HeartGold/SoulSilver)
- Discord webhook integration
- Web dashboard
- Internationalization (non-English Pokémon names)
- Custom OCR model training

### Known Issues

- py-desmume limitation: Single instance per process only
- macOS support limited (check py-desmume compatibility)
- False positives rare but possible (adjustable threshold)

---

## Version History

| Version | Date       | Status      | Notes                  |
| ------- | ---------- | ----------- | ---------------------- |
| 0.1.0   | 2025-01-15 | Stable      | Initial public release |
| 0.0.1   | 2024-12-01 | Development | Internal prototype     |

---

## Development Timeline

### Phase 1-13 Completion

**Phase 1**: Engineering fundamentals (packaging, testing, CI/CD)
**Phase 2**: Documentation excellence (docstrings, architecture)
**Phase 3**: Algorithm validation (real-world data analysis)
**Phase 4**: Comprehensive data exploration with video analysis
**Phase 5**: Multi-processing support + unified GUI
**Phase 6**: Grand code cleanup & architecture refactoring
**Phase 7**: GUI layout improvements & README update
**Phase 10**: OCR quality optimization (100% accuracy)
**Phase 12**: Enhanced OCR pipeline implementation
**Phase 13**: Performance optimizations & testing

### Key Milestones

- **2024-10-20**: Phase 4 complete - 1,934 frames analyzed
- **2024-10-21**: Phase 5-7 complete - Multi-process mode working
- **2024-10-23**: Phase 7.6-7.7 complete - FPS monitoring + fast RNG desync
- **2024-10-28**: Phase 10-13 complete - Enhanced OCR + production ready
- **2025-01-15**: v0.1.0 released - Public launch

---

## Contributors

- **Konstanty Szumigaj** - Initial work and maintainer

---

## License

This project is licensed under the MIT License - see [LICENSE.md](../../LICENSE.md) for details.

---

**Note**: All dates use ISO 8601 format (YYYY-MM-DD)
