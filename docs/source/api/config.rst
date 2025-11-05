config - Configuration Settings
================================

.. automodule:: pyshiny_hunter.config
   :members:
   :undoc-members:

Overview
--------

The ``config`` module provides centralized configuration for all PyShiny Hunter components. All constants and thresholds are defined here for easy tuning and experimentation.

Configuration Categories
------------------------

Shiny Detection Settings
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Frame difference threshold for shiny detection
   SHINY_FRAME_DIFF_THRESHOLD = 500

   # Sparkle detection thresholds
   SHINY_SPARKLE_BRIGHTNESS_THRESHOLD = 247
   SHINY_SPARKLE_MIN_AREA_PCT = 0.2  # 20% of region

**Explanation:**

- ``SHINY_FRAME_DIFF_THRESHOLD``: Shiny encounters have >500 frames in entry animation
- ``SHINY_SPARKLE_BRIGHTNESS_THRESHOLD``: Pixel brightness threshold (0-255)
- ``SHINY_SPARKLE_MIN_AREA_PCT``: Minimum percentage of region with bright pixels

OCR Settings
~~~~~~~~~~~~

.. code-block:: python

   # Image preprocessing
   OCR_UPSCALE_FACTOR = 2
   OCR_BINARY_THRESHOLD = 128

   # GPU acceleration
   OCR_USE_GPU = True  # Auto-detect, fallback to CPU

   # Fuzzy matching
   FUZZY_MATCH_THRESHOLD = 80  # 0-100 similarity score

**Explanation:**

- ``OCR_UPSCALE_FACTOR``: LANCZOS4 upsampling multiplier (improves OCR accuracy)
- ``OCR_BINARY_THRESHOLD``: Grayscale to binary conversion threshold
- ``OCR_USE_GPU``: Enable CUDA acceleration (requires NVIDIA GPU)
- ``FUZZY_MATCH_THRESHOLD``: Minimum similarity for fuzzy name matching

Screen Region Coordinates
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Pokémon name region (Black 2 specific)
   NAME_REGION_X1 = 40
   NAME_REGION_Y1 = 30
   NAME_REGION_X2 = 200
   NAME_REGION_Y2 = 60

   # Center region for sparkle detection
   CENTER_REGION_X1 = 80
   CENTER_REGION_Y1 = 150
   CENTER_REGION_X2 = 176
   CENTER_REGION_Y2 = 230

**Explanation:**

- Name region: Where Pokémon name appears during encounter
- Center region: Where shiny sparkle effect appears

Multi-Process Settings
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # RNG desynchronization
   WORKER_RNG_BASE_OFFSET_FRAMES = 60  # 1 second per worker
   WORKER_RNG_JITTER_FRAMES = 30       # 0-0.5s randomization

   # Queue management
   SCREENSHOT_QUEUE_MAXSIZE = 10       # Frames per worker

   # Synchronization
   BARRIER_TIMEOUT = 30                # Seconds

**Explanation:**

- ``WORKER_RNG_BASE_OFFSET_FRAMES``: Progressive offset between workers
- ``WORKER_RNG_JITTER_FRAMES``: Additional random offset range
- ``SCREENSHOT_QUEUE_MAXSIZE``: Max buffered frames per worker
- ``BARRIER_TIMEOUT``: Max wait time for worker synchronization

GUI Settings
~~~~~~~~~~~~

.. code-block:: python

   # Window dimensions
   GUI_WINDOW_WIDTH = 1920
   GUI_WINDOW_HEIGHT = 1080

   # Rendering
   GUI_TARGET_FPS = 60

   # Panel sizes
   WORKER_PANEL_WIDTH = 426
   WORKER_PANEL_HEIGHT = 414
   SIDEBAR_WIDTH = 350

   # Grid layout
   MAX_GRID_COLUMNS = 4
   WORKER_PANEL_SPACING = 10

**Explanation:**

- Window dimensions: Initial size (auto-maximized on startup)
- Panel sizes: Worker video + stats dimensions
- Grid layout: Maximum columns and spacing

File Paths
~~~~~~~~~~

.. code-block:: python

   # Resource directories
   POKEMON_NAMES_DIR = "resources/pokemon_names"

   # Output files
   SHINY_LOG_FILE = "shiny_log.json"
   ENCOUNTER_STATS_FILE = "encounter_stats.json"

**Explanation:**

- ``POKEMON_NAMES_DIR``: Location of Pokémon name databases (Gen 1-9)
- ``SHINY_LOG_FILE``: Persistent shiny discovery log
- ``ENCOUNTER_STATS_FILE``: Persistent encounter statistics

Emulator Settings
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # DeSmuME settings
   EMULATOR_FPS_TARGET = 60

   # Save state naming
   SHINY_SAVE_PREFIX = "shiny"
   SHINY_SAVE_SUFFIX = ".dst"

**Explanation:**

- ``EMULATOR_FPS_TARGET``: Target emulation speed (60 FPS = real-time)
- Save naming: Format for auto-saved shiny states

Tuning Guidelines
-----------------

Shiny Detection
~~~~~~~~~~~~~~~

If you experience false positives/negatives, adjust:

.. code-block:: python

   # More strict (fewer false positives)
   SHINY_FRAME_DIFF_THRESHOLD = 550  # Increase

   # More lenient (fewer false negatives)
   SHINY_FRAME_DIFF_THRESHOLD = 450  # Decrease

OCR Accuracy
~~~~~~~~~~~~

For better OCR accuracy:

.. code-block:: python

   # Higher upscaling (slower, more accurate)
   OCR_UPSCALE_FACTOR = 3

   # More strict fuzzy matching
   FUZZY_MATCH_THRESHOLD = 90

   # Experiment with binary threshold
   OCR_BINARY_THRESHOLD = 100  # Lower for darker images
   OCR_BINARY_THRESHOLD = 150  # Higher for lighter images

Multi-Process Performance
~~~~~~~~~~~~~~~~~~~~~~~~~

For different worker counts:

.. code-block:: python

   # Faster startup (less unique RNG)
   WORKER_RNG_BASE_OFFSET_FRAMES = 30  # 0.5s per worker

   # Slower startup (more unique RNG)
   WORKER_RNG_BASE_OFFSET_FRAMES = 120  # 2s per worker

   # Larger queue buffer (more memory, smoother streaming)
   SCREENSHOT_QUEUE_MAXSIZE = 20

   # Smaller queue buffer (less memory, possible frame drops)
   SCREENSHOT_QUEUE_MAXSIZE = 5

Constants Reference
-------------------

All Configuration Constants
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autodata:: pyshiny_hunter.config.SHINY_FRAME_DIFF_THRESHOLD
.. autodata:: pyshiny_hunter.config.SHINY_SPARKLE_BRIGHTNESS_THRESHOLD
.. autodata:: pyshiny_hunter.config.SHINY_SPARKLE_MIN_AREA_PCT
.. autodata:: pyshiny_hunter.config.OCR_UPSCALE_FACTOR
.. autodata:: pyshiny_hunter.config.OCR_BINARY_THRESHOLD
.. autodata:: pyshiny_hunter.config.OCR_USE_GPU
.. autodata:: pyshiny_hunter.config.FUZZY_MATCH_THRESHOLD
.. autodata:: pyshiny_hunter.config.WORKER_RNG_BASE_OFFSET_FRAMES
.. autodata:: pyshiny_hunter.config.WORKER_RNG_JITTER_FRAMES

Best Practices
--------------

1. **Don't modify config.py directly** - Create a local config override file
2. **Test changes incrementally** - Adjust one parameter at a time
3. **Document custom values** - Add comments explaining why you changed defaults
4. **Use version control** - Track config changes in Git
5. **Share successful configs** - Contribute optimized values via PR

Environment Variables
---------------------

Some settings can be overridden via environment variables:

.. code-block:: bash

   # Disable GPU (force CPU)
   export OCR_USE_GPU=false

   # Custom Pokémon names directory
   export POKEMON_NAMES_DIR=/path/to/custom/names

   # Output file locations
   export SHINY_LOG_FILE=/path/to/shiny_log.json

See Also
--------

- :doc:`black2_hunter` - How config values are used in detection
- :doc:`enhanced_ocr` - OCR pipeline configuration
- :doc:`worker_process` - Multi-process settings
- ``examples/data_exploration_and_algorithm_design.ipynb`` - Threshold selection analysis
