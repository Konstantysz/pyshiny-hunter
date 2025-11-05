PyShiny Hunter Documentation
==============================

**Automated shiny Pokémon hunting using Computer Vision and OCR**

PyShiny Hunter is a Computer Vision-based automation tool for shiny Pokémon hunting in Pokémon Black 2 using the DeSmuME emulator. It combines image processing, OCR, and state machine patterns to detect and identify shiny Pokémon encounters automatically.

.. image:: https://img.shields.io/badge/python-3.9+-blue.svg
   :target: https://www.python.org/downloads/
   :alt: Python 3.9+

.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: ../../LICENSE.md
   :alt: License: MIT

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
   :alt: Code style: black

Features
--------

- 🎯 **Automated Shiny Detection** - Identifies shiny Pokémon through animation analysis and sparkle detection
- 🔍 **Enhanced OCR Recognition** - 3-stage pipeline (EasyOCR → SymSpell → Fuzzy matching) with 100% accuracy on test dataset
- ⚡ **GPU Acceleration** - Optional CUDA support for faster OCR processing
- 📊 **Encounter Tracking** - Logs all encounters with automatic name recognition and fuzzy matching
- 🎮 **DeSmuME Integration** - Direct emulator control via py-desmume bindings
- 🖼️ **Real-time GUI** - ImGui-based monitoring interface for live progress
- ⚙️ **State Machine Architecture** - Clean, extensible design for future game support
- 🚀 **Multi-Process Mode** - Run multiple emulators simultaneously with unified GUI
- 📈 **Centralized Statistics** - Real-time encounter tracking and shiny logging across all workers

Quick Start
-----------

Installation
~~~~~~~~~~~~

.. code-block:: bash

   # Clone repository
   git clone https://github.com/your-username/pyshiny-hunter.git
   cd pyshiny-hunter

   # Create virtual environment
   python -m venv venv

   # Activate (Windows)
   venv\\Scripts\\Activate.ps1
   # Or Linux/macOS
   source venv/bin/activate

   # Install package
   pip install -e .

Usage
~~~~~

**Single Mode (Default)**

.. code-block:: bash

   # Run with ROM and save state
   pyshiny-hunter path/to/pokemon_black2.nds --state path/to/savestate.dst

**Multi-Process Mode**

.. code-block:: bash

   # 4 workers with randomized starts
   pyshiny-hunter roms/black2.nds --state savestate.dst --num-workers 4

Documentation Contents
----------------------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   installation
   usage
   configuration
   troubleshooting

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/modules
   api/hunter
   api/black2_hunter
   api/enhanced_ocr
   api/py_desmume_manager
   api/worker_process
   api/gui_process
   api/config
   api/utils

.. toctree::
   :maxdepth: 1
   :caption: Development

   contributing
   architecture
   testing
   changelog

.. toctree::
   :maxdepth: 1
   :caption: Legal

   legal

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
