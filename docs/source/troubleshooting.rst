Troubleshooting
===============

This guide covers common issues and their solutions.

Installation Issues
-------------------

Module Not Found
~~~~~~~~~~~~~~~~

**Error:**

.. code-block:: text

   ModuleNotFoundError: No module named 'pyshiny_hunter'

**Solutions:**

1. Ensure virtual environment is activated:

   .. code-block:: bash

      # Windows
      venv\Scripts\Activate.ps1
      # Linux/macOS
      source venv/bin/activate

2. Reinstall package:

   .. code-block:: bash

      pip install -e .

OpenCV Import Error
~~~~~~~~~~~~~~~~~~~

**Error:**

.. code-block:: text

   ImportError: libGL.so.1: cannot open shared object file

**Solution (Linux):**

.. code-block:: bash

   sudo apt install libgl1-mesa-glx libglib2.0-0

py-desmume Error
~~~~~~~~~~~~~~~~

**Error:**

.. code-block:: text

   OSError: [WinError 126] The specified module could not be found

**Solutions (Windows):**

1. Install Visual C++ Redistributable:

   - Download: https://aka.ms/vs/17/release/vc_redist.x64.exe
   - Install and restart

2. Verify Python architecture matches DeSmuME bindings (both 64-bit)

Runtime Issues
--------------

Low FPS
~~~~~~~

**Symptoms**: Emulator FPS < 55, slow hunting

**Solutions:**

1. **Reduce worker count:**

   .. code-block:: bash

      # Try fewer workers
      pyshiny-hunter rom.nds --state hunt.dst --num-workers 2

2. **Close background applications:**

   - Check Task Manager (Windows) or htop (Linux)
   - Close unnecessary programs

3. **Enable GPU acceleration:**

   .. code-block:: bash

      pip install -e .[cuda]

4. **Lower GUI FPS** (edit ``config.py``):

   .. code-block:: python

      GUI_TARGET_FPS = 30  # Instead of 60

Workers Stalled
~~~~~~~~~~~~~~~

**Symptoms**: Worker status shows "STALLED" (red text)

**Solutions:**

1. **Restart application**: Close and relaunch

2. **Check system resources**:

   - Verify CPU usage < 90%
   - Ensure sufficient RAM available

3. **Reduce worker count**:

   .. code-block:: bash

      # If running 8 workers, try 4
      pyshiny-hunter rom.nds --state hunt.dst --num-workers 4

4. **Increase barrier timeout** (edit ``config.py``):

   .. code-block:: python

      BARRIER_TIMEOUT = 60  # Instead of 30

No GUI Window
~~~~~~~~~~~~~

**Symptoms**: Application starts but no window appears

**Solutions:**

1. **Check display settings**: Ensure monitor connected

2. **Try windowed mode**: Disable auto-maximization temporarily

3. **Update graphics drivers**: Install latest drivers

4. **Check logs**: Look for OpenGL errors

Detection Issues
----------------

False Positives
~~~~~~~~~~~~~~~

**Symptoms**: Non-shiny Pokémon detected as shiny

**Solutions:**

1. **Increase frame threshold** (edit ``config.py``):

   .. code-block:: python

      SHINY_FRAME_DIFF_THRESHOLD = 550  # Instead of 500

2. **Verify save state location**: Ensure hunting in correct area

3. **Report issue**: Create GitHub issue with:

   - Screenshot/video of false positive
   - Save state file
   - Configuration settings

False Negatives
~~~~~~~~~~~~~~~

**Symptoms**: Shiny Pokémon not detected

**Solutions:**

1. **Decrease frame threshold** (edit ``config.py``):

   .. code-block:: python

      SHINY_FRAME_DIFF_THRESHOLD = 450  # Instead of 500

2. **Check animation**: Verify shiny sparkle appears

3. **Test manually**: Load save state in DeSmuME, verify it's shiny

OCR Not Working
~~~~~~~~~~~~~~~

**Symptoms**: Pokémon names not recognized or incorrect

**Solutions:**

1. **Increase upscale factor** (edit ``config.py``):

   .. code-block:: python

      OCR_UPSCALE_FACTOR = 3  # Instead of 2

2. **Adjust binary threshold** (edit ``config.py``):

   .. code-block:: python

      OCR_BINARY_THRESHOLD = 100  # Try 100-150

3. **Lower fuzzy match threshold** (edit ``config.py``):

   .. code-block:: python

      FUZZY_MATCH_THRESHOLD = 75  # Instead of 80

4. **Enable GPU acceleration:**

   .. code-block:: bash

      pip install -e .[cuda]

No Encounters Detected
~~~~~~~~~~~~~~~~~~~~~~

**Symptoms**: Encounter counter stays at 0

**Solutions:**

1. **Verify save state location**:

   - Must be in wild grass area
   - Not in building or on path

2. **Check hunter state**:

   - Should cycle: search → check_shiny → battle → search
   - If stuck in one state, save state may be invalid

3. **Test manually**: Load save state in DeSmuME, verify encounters work

Multi-Process Issues
--------------------

Workers Not Starting
~~~~~~~~~~~~~~~~~~~~

**Symptoms**: Progress bar stuck at 0/N workers

**Solutions:**

1. **Check barrier timeout**: Workers may be taking too long

   .. code-block:: python

      BARRIER_TIMEOUT = 60  # Increase in config.py

2. **Verify ROM path**: Ensure ROM file exists and is readable

3. **Check logs**: Look for error messages in console

4. **Reduce worker count**:

   .. code-block:: bash

      pyshiny-hunter rom.nds --state hunt.dst --num-workers 2

Queue Overflow
~~~~~~~~~~~~~~

**Symptoms**: High memory usage, lag

**Solutions:**

1. **Reduce queue size** (edit ``config.py``):

   .. code-block:: python

      SCREENSHOT_QUEUE_MAXSIZE = 5  # Instead of 10

2. **Reduce worker count**: Fewer workers = less memory

Duplicate Encounters
~~~~~~~~~~~~~~~~~~~~

**Symptoms**: All workers finding same Pokémon

**Solutions:**

1. **Verify RNG desync working**: Check worker status during init

2. **Increase RNG offset** (edit ``config.py``):

   .. code-block:: python

      WORKER_RNG_BASE_OFFSET_FRAMES = 120  # Instead of 60

3. **Ensure using save state**: ROM without save state has deterministic RNG

GPU/CUDA Issues
---------------

CUDA Not Detected
~~~~~~~~~~~~~~~~~

**Symptoms**: ``CUDA available: False`` in logs

**Solutions:**

1. **Verify NVIDIA GPU**:

   .. code-block:: bash

      nvidia-smi  # Should show GPU info

2. **Install CUDA Toolkit**:

   - Download: https://developer.nvidia.com/cuda-downloads
   - Install CUDA 11.8+ or 12.1+

3. **Reinstall PyTorch with CUDA**:

   .. code-block:: bash

      pip uninstall torch torchvision
      pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

4. **Verify installation**:

   .. code-block:: python

      import torch
      print(torch.cuda.is_available())  # Should be True
      print(torch.cuda.get_device_name(0))  # GPU name

Out of Memory (OOM)
~~~~~~~~~~~~~~~~~~~

**Symptoms**: CUDA out of memory error

**Solutions:**

1. **Reduce batch size** (if applicable)

2. **Force CPU mode** (edit ``config.py``):

   .. code-block:: python

      OCR_USE_GPU = False

3. **Close other GPU applications**: Check GPU usage with ``nvidia-smi``

File Issues
-----------

ROM Not Found
~~~~~~~~~~~~~

**Error:**

.. code-block:: text

   FileNotFoundError: ROM file not found

**Solutions:**

1. **Verify ROM path**: Use absolute path

   .. code-block:: bash

      pyshiny-hunter "C:\roms\pokemon_black2.nds"

2. **Check file exists**: Use ``ls`` or File Explorer

3. **Check permissions**: Ensure read access to ROM file

Save State Errors
~~~~~~~~~~~~~~~~~

**Error:**

.. code-block:: text

   Error loading save state

**Solutions:**

1. **Verify .dst format**: Must be DeSmuME save state file

2. **Check save state version**: Created with compatible DeSmuME version

3. **Test save state manually**: Load in DeSmuME standalone

Cannot Write Output
~~~~~~~~~~~~~~~~~~~

**Error:**

.. code-block:: text

   PermissionError: Cannot write shiny_log.json

**Solutions:**

1. **Check write permissions**: Run with appropriate permissions

2. **Close other programs**: Ensure files not open elsewhere

3. **Use custom output path** (environment variable):

   .. code-block:: bash

      export SHINY_LOG_FILE="/path/to/writable/shiny_log.json"

Diagnostic Commands
-------------------

Check Installation
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Verify package installed
   python -c "import pyshiny_hunter; print(pyshiny_hunter.__version__)"

   # Check dependencies
   pip list | grep -E "opencv|easyocr|imgui|desmume"

   # Run tests
   pytest -v

Check GPU
~~~~~~~~~

.. code-block:: bash

   # NVIDIA GPU info
   nvidia-smi

   # PyTorch CUDA check
   python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"

   # EasyOCR GPU check
   python -c "import easyocr; reader = easyocr.Reader(['en']); print('GPU OK')"

System Resources
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Windows (PowerShell)
   Get-Process | Sort-Object CPU -Descending | Select-Object -First 10

   # Linux
   htop  # Interactive process viewer
   ps aux --sort=-%cpu | head -n 11  # Top CPU processes

Getting Help
------------

If issues persist:

1. **Check documentation**: :doc:`usage`, :doc:`configuration`

2. **Search existing issues**: `GitHub Issues <https://github.com/your-username/pyshiny-hunter/issues>`_

3. **Create new issue** with:

   - PyShiny Hunter version
   - Python version (``python --version``)
   - Operating system
   - Error messages (full traceback)
   - Steps to reproduce
   - Configuration changes (if any)

4. **Provide logs**: Include console output

5. **Share configuration**: Attach ``config.py`` if modified

Common Error Messages
---------------------

.. list-table::
   :header-rows: 1

   * - Error
     - Cause
     - Solution
   * - ``ModuleNotFoundError``
     - Package not installed
     - ``pip install -e .``
   * - ``FileNotFoundError``
     - ROM/state file missing
     - Check file path
   * - ``PermissionError``
     - No write access
     - Check permissions
   * - ``OSError: [WinError 126]``
     - Missing Visual C++
     - Install redistributable
   * - ``CUDA out of memory``
     - GPU memory full
     - Force CPU mode
   * - ``ImportError: libGL``
     - Missing OpenGL libs
     - Install mesa (Linux)

See Also
--------

- :doc:`installation` - Installation guide
- :doc:`usage` - Usage guide
- :doc:`configuration` - Configuration options
- `GitHub Issues <https://github.com/your-username/pyshiny-hunter/issues>`_
