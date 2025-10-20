# PyShiny Hunter

> Automated shiny Pokémon hunting using Computer Vision and OCR

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.md)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

PyShiny Hunter is a Computer Vision-based automation tool for shiny Pokémon hunting in Pokémon Black 2 using the DeSmuME emulator. It combines image processing, OCR, and state machine patterns to detect and identify shiny Pokémon encounters automatically.

## ✨ Features

- 🎯 **Automated Shiny Detection** - Identifies shiny Pokémon through animation analysis and sparkle detection
- 🔍 **OCR Pokemon Recognition** - Uses Tesseract OCR with preprocessing to identify encountered Pokémon
- 📊 **Encounter Tracking** - Logs all encounters with automatic name recognition and fuzzy matching
- 🎮 **DeSmuME Integration** - Direct emulator control via py-desmume bindings
- 🖼️ **Real-time GUI** - ImGui-based monitoring interface for live progress
- ⚙️ **State Machine Architecture** - Clean, extensible design for future game support
- 🚀 **Multi-Process Mode** - Run multiple emulators simultaneously with unified GUI (NEW!)

## 🛠️ Tech Stack

- **Computer Vision**: OpenCV, NumPy
- **OCR**: Tesseract with adaptive preprocessing
- **Automation**: py-desmume (Nintendo DS emulator bindings)
- **Architecture**: python-statemachine
- **GUI**: ImGui + OpenGL
- **Testing**: pytest, pytest-cov
- **Quality**: Ruff, Black, MyPy, pre-commit

## 📋 Prerequisites

- **Python 3.9+** - [Download](https://www.python.org/downloads/)
- **Tesseract OCR**:
  - Windows: [UB Mannheim installer](https://github.com/UB-Mannheim/tesseract/wiki)
  - Linux: `sudo apt install tesseract-ocr`
  - macOS: `brew install tesseract`
- **Pokemon Black 2 ROM** - You must own the game legally

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/your-username/pyshiny-hunter.git
cd pyshiny-hunter

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\Activate.ps1
# Or Linux/macOS
source venv/bin/activate

# Install package
pip install -e .
```

### Usage

#### Single Mode (Default)

```bash
# Run with ROM and save state
pyshiny-hunter path/to/pokemon_black2.nds --state path/to/savestate.dst

# Or use the script directly
python scripts/py_desmume_hunter.py path/to/rom.nds --state savestate.dst
```

#### Multi-Process Mode (NEW!)

Run multiple emulators with a unified GUI displaying all streams:

```bash
# 2 workers
python scripts/py_desmume_hunter.py roms/black2.nds --state savestate.dst --num-workers 2

# 4 workers with randomized starts
python scripts/py_desmume_hunter.py roms/black2.nds --state savestate.dst --num-workers 4 --randomize-start
```

Each worker runs in a separate process, displaying live video feeds side-by-side in a single GUI window. See [UNIFIED_GUI.md](docs/UNIFIED_GUI.md) for details.

### Command-Line Options

| Option              | Description                               | Required    |
| ------------------- | ----------------------------------------- | ----------- |
| `rom`               | Path to `.nds` ROM file                   | ✅ Yes      |
| `--state`           | Path to `.dst` save state file            | ❌ Optional |
| `--sav`             | Path to `.sav` save file                  | ❌ Optional |
| `--num-workers`     | Number of emulator processes (default: 1) | ❌ Optional |
| `--randomize-start` | Randomize starting frame for each worker  | ❌ Optional |

## 🎮 How It Works

### Computer Vision Pipeline

```
Game Screen Capture (60 FPS)
    ↓
Region Extraction (Pokémon name area)
    ↓
Image Preprocessing
  ├─ 3× Upsampling (OCR accuracy)
  ├─ Grayscale Conversion
  └─ Binary Thresholding
    ↓
Tesseract OCR (character whitelist)
    ↓
Fuzzy String Matching (error correction)
    ↓
Pokémon Identified
```

### Shiny Detection

1. **Animation Frame Counting** - Shiny Pokémon have longer entry animations (>500 frames)
2. **Sparkle Detection** - Analyzes pixel brightness in center region for sparkle effect
3. **State Machine** - Tracks game state transitions for reliable detection

### State Flow

```
Search → Check Shiny → Pre-Battle → Battle → Found/Reset
```

## 📊 Project Structure

```
pyshiny-hunter/
├── pyshiny_hunter/          # Main package
│   ├── hunter.py            # Abstract hunter base class
│   ├── black2_hunter.py     # Black 2 implementation
│   ├── py_desmume_manager.py  # Emulator integration
│   └── utils/               # Utilities
├── scripts/                 # Entry point scripts
├── tests/                   # Test suite (pytest)
├── resources/
│   └── pokemon_names/       # Pokémon database (Gen 1-9)
├── docs/                    # Documentation
└── .github/workflows/       # CI/CD
```

## ⚖️ Legal Notice

**Important**: This tool requires a Pokémon Black 2 ROM file.

- ✅ **Legal**: Use ROM backups from games you physically own
- ❌ **Illegal**: Download or distribute ROM files

**This repository does NOT include ROM files** due to Nintendo copyright.

See [docs/LEGAL.md](docs/LEGAL.md) for complete copyright policy and compliance information.

## 🧪 Development

### Setup Development Environment

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run with coverage
pytest --cov=pyshiny_hunter --cov-report=html
```

### Code Quality

```bash
# Format code
black .

# Lint
ruff check .

# Type check
mypy pyshiny_hunter
```

### Running Tests

```bash
# All tests
pytest -v

# Specific test file
pytest tests/test_black2_hunter.py

# With coverage report
pytest --cov=pyshiny_hunter --cov-report=term-missing
```

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Development setup
- Code style guidelines
- Testing requirements
- Pull request process

## 📚 Documentation

- **[Contributing Guide](CONTRIBUTING.md)** - Development guidelines and workflow
- **[Legal Notice](docs/LEGAL.md)** - Copyright policy and ROM requirements

## 🐛 Troubleshooting

### Tesseract Not Found

Ensure Tesseract is installed and added to your system's PATH:

```bash
tesseract --version
```

### Missing Dependencies

Make sure you're in the activated virtual environment:

```bash
pip install -e .
```

### ROM File Issues

- Place your legally-obtained `.nds` ROM in the `roms/` directory
- ROM files are NOT included in this repository due to copyright
- You must own a physical copy of the game

## 📝 License

This project is licensed under the MIT License - see [LICENSE.md](LICENSE.md) for details.

## 🙏 Acknowledgments

- **Pokémon** is a registered trademark of Nintendo, Game Freak, and Creatures Inc.
- This project is not affiliated with or endorsed by Nintendo
- Pokémon name data compiled from public databases (PokeAPI, Bulbapedia)

## 📧 Contact

For questions or issues, please [open an issue](https://github.com/your-username/pyshiny-hunter/issues) on GitHub.

---

**Disclaimer**: This tool is for educational purposes and personal use only. Users are responsible for ensuring they comply with all applicable laws and Nintendo's terms of service.
