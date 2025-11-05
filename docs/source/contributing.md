# Contributing to PyShiny Hunter

Thank you for your interest in contributing! This document provides guidelines for contributing to PyShiny Hunter.

## Getting Started

### Development Setup

1. **Fork and clone repository:**

   ```bash
   git clone https://github.com/your-username/pyshiny-hunter.git
   cd pyshiny-hunter
   ```

2. **Create virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\Activate.ps1  # Windows
   ```

3. **Install development dependencies:**

   ```bash
   pip install -e .[dev]
   ```

4. **Install pre-commit hooks:**

   ```bash
   pre-commit install
   ```

## Development Workflow

### Creating a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### Making Changes

1. **Write code** following style guidelines (below)
2. **Add tests** for new functionality
3. **Update documentation** if needed
4. **Run tests locally:**

   ```bash
   pytest
   ```

5. **Check code quality:**

   ```bash
   # Format code
   black .

   # Lint
   ruff check .

   # Type check
   mypy pyshiny_hunter
   ```

### Committing Changes

Pre-commit hooks will automatically run:

- Black formatting
- Ruff linting
- MyPy type checking

If hooks pass:

```bash
git add .
git commit -m "Add feature: your feature description"
```

## Code Style Guidelines

### Python Style

- **PEP 8** compliance (enforced by Black and Ruff)
- **Line length**: 100 characters
- **Docstrings**: Google or NumPy style

### Docstring Example

```python
def recognize_pokemon_name(self, image: np.ndarray) -> str | None:
    """Recognize Pokémon name from preprocessed image.

    Uses 3-stage OCR pipeline:
    1. EasyOCR - Primary OCR
    2. SymSpell - Spell correction
    3. Fuzzy matching - Match against database

    Args:
        image: Preprocessed grayscale image (numpy.ndarray)

    Returns:
        Recognized Pokémon name or None if no match found

    Example:
        >>> ocr = EnhancedOCR()
        >>> image = cv2.imread("watchog.png", cv2.IMREAD_GRAYSCALE)
        >>> name = ocr.recognize_pokemon_name(image)
        >>> print(name)  # "Watchog"
    """
```

### Type Hints

Use type hints for all function signatures:

```python
from typing import Optional

def process_frame(frame: np.ndarray, threshold: int = 128) -> Optional[str]:
    pass
```

### Naming Conventions

- **Variables/functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private members**: `_leading_underscore`

## Testing Guidelines

### Writing Tests

- Place tests in `tests/` directory
- Name test files `test_<module>.py`
- Use `pytest` fixtures for setup/teardown

### Test Example

```python
import pytest
from pyshiny_hunter.enhanced_ocr import EnhancedOCR

@pytest.fixture
def ocr():
    return EnhancedOCR()

def test_recognize_pokemon_name(ocr):
    # Arrange
    image = create_test_image("Watchog")

    # Act
    result = ocr.recognize_pokemon_name(image)

    # Assert
    assert result == "Watchog"
```

### Running Tests

```bash
# All tests
pytest

# Specific file
pytest tests/test_enhanced_ocr.py

# With coverage
pytest --cov=pyshiny_hunter --cov-report=html

# Verbose
pytest -v
```

### Coverage Requirements

- **Minimum coverage**: 80% overall
- **Core logic**: 90%+ coverage (hunters, OCR, detection)
- **Check coverage**: `pytest --cov=pyshiny_hunter`

## Documentation

### Updating Documentation

Documentation is in `docs/source/`:

- **API docs**: Auto-generated from docstrings
- **User guides**: Written in RST/Markdown

### Building Documentation

```bash
cd docs
make html  # Linux/macOS
.\make.bat html  # Windows

# View: open build/html/index.html
```

### Documentation Style

- **Clear and concise**: Avoid jargon
- **Examples**: Include code examples
- **Cross-references**: Link to related sections

## Pull Request Process

### Before Submitting

1. ✅ All tests passing (`pytest`)
2. ✅ Code formatted (`black .`)
3. ✅ No linting errors (`ruff check .`)
4. ✅ Type checking passes (`mypy pyshiny_hunter`)
5. ✅ Documentation updated (if needed)
6. ✅ CHANGELOG.md updated (if applicable)

### PR Checklist

When creating a PR, include:

- **Description**: What does this PR do?
- **Motivation**: Why is this change needed?
- **Testing**: How was this tested?
- **Screenshots**: For GUI changes
- **Breaking changes**: Note any API changes

### PR Template

```markdown
## Description
Brief description of changes

## Motivation
Why is this change needed?

## Changes
- Added feature X
- Fixed bug Y
- Updated docs for Z

## Testing
- [ ] Added unit tests
- [ ] Manually tested
- [ ] All tests passing

## Checklist
- [ ] Code formatted (black)
- [ ] Linting passed (ruff)
- [ ] Type checking passed (mypy)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
```

## Issue Guidelines

### Reporting Bugs

Include:

- PyShiny Hunter version
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages (full traceback)
- Configuration changes (if any)

### Feature Requests

Include:

- Use case: Why is this feature needed?
- Proposed solution: How should it work?
- Alternatives: Other approaches considered?
- Additional context: Screenshots, examples

## Project Structure

```text
pyshiny-hunter/
├── pyshiny_hunter/           # Main package
│   ├── hunter.py             # Abstract base class
│   ├── black2_hunter.py      # Black 2 implementation
│   ├── enhanced_ocr.py       # OCR pipeline
│   ├── py_desmume_manager.py # Emulator integration
│   ├── worker_process.py     # Multi-process workers
│   ├── gui_process.py        # Unified GUI
│   ├── config.py             # Configuration
│   └── utils/                # Utility modules
├── tests/                    # Test suite
├── docs/                     # Documentation
│   ├── source/               # RST/MD files
│   └── build/                # Generated HTML
├── examples/                 # Jupyter notebooks
├── resources/                # Pokémon databases
└── pyproject.toml            # Package configuration
```

## Areas for Contribution

### High Priority

- 🎮 **Additional game support** (Black/White, HeartGold/SoulSilver)
- 🧪 **Test coverage** improvements
- 📝 **Documentation** enhancements
- 🐛 **Bug fixes** from GitHub issues

### Medium Priority

- ⚡ **Performance** optimizations
- 🎨 **GUI** improvements
- 📊 **Statistics** features
- 🔧 **Configuration** options

### Low Priority

- 🌍 **Internationalization** (non-English names)
- 📱 **Web interface** (optional)
- 🤖 **Discord bot** integration

## Code Review Process

### What We Look For

- **Correctness**: Does it work as intended?
- **Tests**: Are there adequate tests?
- **Style**: Follows project conventions?
- **Documentation**: Clear and complete?
- **Performance**: No unnecessary slowdowns?

### Review Timeline

- Initial review: Within 7 days
- Follow-up reviews: Within 3 days
- Merge: After approval + CI passing

## Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help newcomers

### Communication Channels

- **GitHub Issues**: Bug reports, feature requests
- **Pull Requests**: Code contributions
- **Discussions**: General questions (if enabled)

## Legal

### License

By contributing, you agree that your contributions will be licensed under the MIT License.

### Copyright

- Nintendo, Game Freak, and Creatures Inc. own Pokémon copyrights
- This project is for educational/personal use only
- Do not distribute ROM files

## Thank You!

Every contribution helps make PyShiny Hunter better. We appreciate your time and effort!

## Resources

- [Installation Guide](installation.rst)
- [Usage Guide](usage.rst)
- [API Documentation](api/modules.rst)
- [Architecture Overview](architecture.rst)

---

**Questions?** Open an issue or check existing documentation.
