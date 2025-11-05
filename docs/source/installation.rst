Installation
============

This guide covers the installation process for PyShiny Hunter.

Prerequisites
-------------

Before installing PyShiny Hunter, ensure you have:

- **Python 3.9+** - `Download Python <https://www.python.org/downloads/>`_
- **Pokemon Black 2 ROM** - You must own the game legally
- **Git** (optional) - For cloning the repository

Quick Installation
------------------

Using pip (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Clone repository
   git clone https://github.com/your-username/pyshiny-hunter.git
   cd pyshiny-hunter

   # Create virtual environment
   python -m venv venv

   # Activate virtual environment
   # Windows (PowerShell)
   venv\Scripts\Activate.ps1
   # Windows (CMD)
   venv\Scripts\activate.bat
   # Linux/macOS
   source venv/bin/activate

   # Install package
   pip install -e .

From Source
~~~~~~~~~~~

.. code-block:: bash

   # Clone and navigate
   git clone https://github.com/your-username/pyshiny-hunter.git
   cd pyshiny-hunter

   # Install dependencies manually
   pip install -r requirements.txt  # If available

   # Or install from pyproject.toml
   pip install -e .

Optional Dependencies
---------------------

GPU Acceleration (CUDA)
~~~~~~~~~~~~~~~~~~~~~~~

For 5-10× faster OCR processing with NVIDIA GPUs:

.. code-block:: bash

   # Install CUDA support
   pip install -e .[cuda]

Requirements:

- NVIDIA GPU with CUDA support
- CUDA Toolkit 11.8+ or 12.1+
- Latest NVIDIA drivers

Verification:

.. code-block:: python

   import torch
   print(f"CUDA available: {torch.cuda.is_available()}")
   print(f"CUDA device: {torch.cuda.get_device_name(0)}")

Development Tools
~~~~~~~~~~~~~~~~~

For contributing and development:

.. code-block:: bash

   # Install dev dependencies
   pip install -e .[dev]

   # Install pre-commit hooks
   pre-commit install

Includes:

- **Testing**: pytest, pytest-cov, pytest-mock
- **Linting**: ruff, black, mypy
- **Hooks**: pre-commit

Documentation Tools
~~~~~~~~~~~~~~~~~~~

For building documentation:

.. code-block:: bash

   # Install docs dependencies
   pip install -e .[docs]

Includes:

- **Sphinx**: Documentation generator
- **RTD Theme**: Read the Docs theme
- **Extensions**: autodoc, napoleon, myst-parser

Jupyter Notebooks
~~~~~~~~~~~~~~~~~

For running data exploration notebooks:

.. code-block:: bash

   # Install examples dependencies
   pip install -e .[examples]

Includes:

- **Jupyter**: Notebook environment
- **Matplotlib**: Plotting library

All Optional Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~

To install everything:

.. code-block:: bash

   pip install -e .[cuda,dev,docs,examples]

Platform-Specific Instructions
------------------------------

Windows
~~~~~~~

.. code-block:: powershell

   # Install Python from Microsoft Store or python.org
   # Recommended: Use PowerShell with execution policy enabled

   # Clone repository
   git clone https://github.com/your-username/pyshiny-hunter.git
   cd pyshiny-hunter

   # Create and activate venv
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Install
   pip install -e .

**Common Issues:**

- **Execution Policy Error**: Run ``Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser``
- **Missing Visual C++**: Install `Visual C++ Redistributable <https://aka.ms/vs/17/release/vc_redist.x64.exe>`_

Linux (Ubuntu/Debian)
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Install system dependencies
   sudo apt update
   sudo apt install python3 python3-pip python3-venv git

   # Clone repository
   git clone https://github.com/your-username/pyshiny-hunter.git
   cd pyshiny-hunter

   # Create and activate venv
   python3 -m venv venv
   source venv/bin/activate

   # Install
   pip install -e .

**Additional Dependencies:**

.. code-block:: bash

   # For OpenCV
   sudo apt install libgl1-mesa-glx libglib2.0-0

   # For SDL2 (if using py-desmume)
   sudo apt install libsdl2-dev

macOS
~~~~~

.. code-block:: bash

   # Install Homebrew (if not installed)
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

   # Install Python
   brew install python@3.9

   # Clone repository
   git clone https://github.com/your-username/pyshiny-hunter.git
   cd pyshiny-hunter

   # Create and activate venv
   python3 -m venv venv
   source venv/bin/activate

   # Install
   pip install -e .

**Note**: py-desmume support on macOS may be limited. Check compatibility.

Verifying Installation
----------------------

After installation, verify everything works:

.. code-block:: bash

   # Check CLI is available
   pyshiny-hunter --help

   # Check Python package
   python -c "import pyshiny_hunter; print(pyshiny_hunter.__version__)"

   # Run tests
   pytest

Expected output:

.. code-block:: text

   usage: pyshiny-hunter [-h] [--state STATE] [--sav SAV] [--num-workers NUM_WORKERS] rom

   26 passed in 2.31s

ROM Setup
---------

Obtaining a ROM
~~~~~~~~~~~~~~~

**Legal Notice**: PyShiny Hunter requires a Pokémon Black 2 ROM file.

- ✅ **Legal**: Create ROM backup from games you physically own
- ❌ **Illegal**: Download or distribute ROM files

This repository does NOT include ROM files due to Nintendo copyright.

ROM File Requirements
~~~~~~~~~~~~~~~~~~~~~

- **Format**: ``.nds`` (Nintendo DS ROM)
- **Game**: Pokémon Black 2 (USA/EUR/JPN versions supported)
- **Size**: ~128 MB
- **Checksum**: Verify ROM integrity with known good checksums

Recommended Directory Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   pyshiny-hunter/
   ├── roms/
   │   └── pokemon_black2.nds    # Your ROM file
   ├── saves/
   │   ├── shiny_hunt.dst        # Save states
   │   └── game.sav              # Save files
   └── ...

Save States
~~~~~~~~~~~

Create save states at shiny hunting locations:

1. **Load ROM in DeSmuME**
2. **Navigate to hunting location** (e.g., Route 1 grass)
3. **Save State**: ``File → Save State As...``
4. **Save as** ``shiny_hunt.dst``

Common hunting locations in Black 2:

- Route 1 (Patrat, Lillipup)
- Route 2 (Watchog, Patrat)
- Floccesy Ranch (Riolu, Mareep)

Troubleshooting
---------------

Import Errors
~~~~~~~~~~~~~

.. code-block:: text

   ModuleNotFoundError: No module named 'pyshiny_hunter'

**Solution:**

.. code-block:: bash

   # Ensure virtual environment is activated
   # Windows
   venv\Scripts\Activate.ps1
   # Linux/macOS
   source venv/bin/activate

   # Reinstall package
   pip install -e .

OpenCV Issues
~~~~~~~~~~~~~

.. code-block:: text

   ImportError: libGL.so.1: cannot open shared object file

**Solution (Linux):**

.. code-block:: bash

   sudo apt install libgl1-mesa-glx

py-desmume Errors
~~~~~~~~~~~~~~~~~

.. code-block:: text

   OSError: [WinError 126] The specified module could not be found

**Solution (Windows):**

1. Install Visual C++ Redistributable
2. Ensure 64-bit Python matches 64-bit DeSmuME bindings

CUDA Not Detected
~~~~~~~~~~~~~~~~~

.. code-block:: text

   CUDA available: False

**Solution:**

1. Verify NVIDIA GPU: ``nvidia-smi``
2. Install CUDA Toolkit: `CUDA Downloads <https://developer.nvidia.com/cuda-downloads>`_
3. Reinstall PyTorch with CUDA:

   .. code-block:: bash

      pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

Next Steps
----------

After installation:

1. **Read Usage Guide**: :doc:`usage`
2. **Configure Settings**: :doc:`configuration`
3. **Run Your First Hunt**: ``pyshiny-hunter roms/pokemon_black2.nds --state saves/shiny_hunt.dst``

See Also
--------

- :doc:`usage` - How to use PyShiny Hunter
- :doc:`configuration` - Configuration options
- :doc:`troubleshooting` - Common issues and solutions
- `GitHub Issues <https://github.com/your-username/pyshiny-hunter/issues>`_ - Report problems
