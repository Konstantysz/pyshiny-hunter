# Contributing to PyShiny Hunter

Thank you for your interest in contributing to PyShiny Hunter! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites

- Python 3.9 or higher
- Tesseract OCR installed and in PATH
- Git

### Setup Instructions

1. Fork and clone the repository:
```bash
git clone https://github.com/your-username/pyshiny-hunter.git
cd pyshiny-hunter
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
- Windows: `venv\Scripts\Activate.ps1`
- Linux/Mac: `source venv/bin/activate`

4. Install the package in editable mode with development dependencies:
```bash
pip install -e ".[dev]"
```

5. Install pre-commit hooks:
```bash
pre-commit install
```

## Development Workflow

### Code Style

We use the following tools to maintain code quality:

- **Black**: Code formatter (line length: 100)
- **Ruff**: Fast Python linter
- **MyPy**: Static type checker (optional)
- **pytest**: Testing framework

All of these are automatically run via pre-commit hooks before each commit.

### Running Tests

Run the full test suite:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=pyshiny_hunter --cov-report=html
```

Run specific test file:
```bash
pytest tests/test_black2_hunter.py
```

Run tests matching a pattern:
```bash
pytest -k "test_shiny"
```

### Code Quality Checks

Run linter:
```bash
ruff check .
```

Run formatter:
```bash
black .
```

Run type checker:
```bash
mypy pyshiny_hunter
```

### Writing Tests

- All new features must include tests
- Aim for at least 70% code coverage
- Use fixtures from `tests/conftest.py`
- Follow the existing test structure

Example test:
```python
def test_my_feature(mock_pokemon_csv_files, monkeypatch):
    """Test description explaining what this tests."""
    monkeypatch.chdir(mock_pokemon_csv_files)
    hunter = Black2Hunter()

    result = hunter.some_method()

    assert result == expected_value
```

## Submitting Changes

### Pull Request Process

1. Create a new branch for your feature:
```bash
git checkout -b feature/my-new-feature
```

2. Make your changes and commit them:
```bash
git add .
git commit -m "Add: brief description of changes"
```

3. Push to your fork:
```bash
git push origin feature/my-new-feature
```

4. Open a Pull Request on GitHub

### Commit Message Guidelines

Follow conventional commits format:

- `Add: new feature or capability`
- `Fix: bug fix`
- `Update: enhancement to existing feature`
- `Refactor: code restructuring without behavior change`
- `Docs: documentation changes`
- `Test: test additions or modifications`
- `Chore: maintenance tasks`

Example:
```
Add: template matching for shiny detection

Implement alternative shiny detection method using OpenCV template
matching to detect sparkle effects. This provides more reliable
detection than frame counting alone.
```

### Pull Request Requirements

Before submitting a PR, ensure:

- [ ] All tests pass (`pytest`)
- [ ] Code coverage remains above 70%
- [ ] Code is formatted with Black
- [ ] Ruff linting passes with no errors
- [ ] Type hints are added to new functions
- [ ] Docstrings are added to public functions
- [ ] CHANGELOG is updated (if applicable)
- [ ] Documentation is updated (if needed)

## Code Organization

```
pyshiny_hunter/
├── hunter.py              # Abstract base class
├── black2_hunter.py       # Game-specific implementation
├── py_desmume_manager.py  # Emulator integration
├── module_logger.py       # Logging configuration
└── utils/
    └── gui_utils.py       # GUI utilities
```

### Adding New Game Support

To add support for a new Pokemon game:

1. Create a new hunter class inheriting from `Hunter`
2. Implement all abstract methods
3. Add game-specific constants
4. Update documentation

Example:
```python
from pyshiny_hunter.hunter import Hunter

class HeartGoldHunter(Hunter):
    def _found_pokemon(self, top_screen, bottom_screen):
        # Implement detection logic
        pass

    # Implement other abstract methods...
```

## Reporting Bugs

When reporting bugs, please include:

- Python version
- Operating system
- Steps to reproduce
- Expected behavior
- Actual behavior
- Screenshots (if applicable)
- Relevant log output

## Feature Requests

Feature requests are welcome! Please:

- Check if the feature already exists or is planned
- Clearly describe the use case
- Explain why this would benefit the project
- Provide examples if possible

## Questions?

- Open an issue for questions about development
- Check existing issues for similar questions
- Review the documentation in `docs/`

## License

By contributing, you agree that your contributions will be licensed under the MIT License.