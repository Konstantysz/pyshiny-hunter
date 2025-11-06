# PyShiny Hunter Documentation

This directory contains the Sphinx documentation for PyShiny Hunter.

## Building Documentation

### Prerequisites

Install documentation dependencies:

```bash
pip install -e .[docs]
```

### Build Commands

**Linux/macOS:**
```bash
cd docs
make html
```

**Windows:**
```bash
cd docs
make.bat html
```

**Alternative (cross-platform):**
```bash
sphinx-build -b html docs/source docs/build/html
```

### Viewing Documentation

After building, open `docs/build/html/index.html` in your web browser.

## Documentation Structure

- `source/` - Source files (.rst, .md)
- `source/api/` - API reference documentation
- `build/html/` - Generated HTML documentation

## See Also

- Full documentation in `docs/build/html/index.html`
- [Sphinx Documentation](https://www.sphinx-doc.org/)
