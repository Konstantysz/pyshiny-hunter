Configuration
=============

PyShiny Hunter provides extensive configuration options for fine-tuning detection algorithms and performance settings.

Configuration File
------------------

All settings are centralized in ``pyshiny_hunter/config.py``. See :doc:`api/config` for complete API reference.

Shiny Detection Settings
------------------------

Frame Difference Threshold
~~~~~~~~~~~~~~~~~~~~~~~~~~

Controls the primary shiny detection method:

.. code-block:: python

   SHINY_FRAME_DIFF_THRESHOLD = 500

**Description**: Minimum frame count for shiny animation. Shiny encounters have longer entry animations (>500 frames), while non-shiny encounters are shorter.

**Tuning**:

- **Increase (550-600)**: Fewer false positives, may miss edge cases
- **Decrease (450-480)**: Catch more edge cases, more false positives

**Recommendation**: Leave at default (500) - validated on 1,934 real frames.

Sparkle Detection Thresholds
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Secondary detection method based on sparkle effect:

.. code-block:: python

   SHINY_SPARKLE_BRIGHTNESS_THRESHOLD = 247
   SHINY_SPARKLE_MIN_AREA_PCT = 0.2  # 20%

**Description**:

- ``BRIGHTNESS_THRESHOLD``: Pixel brightness (0-255) to detect sparkles
- ``MIN_AREA_PCT``: Minimum percentage of region with bright pixels

**Tuning**:

- **Brightness (220-255)**: Lower = more sensitive, higher = more strict
- **Area (0.1-0.3)**: Lower = more sensitive, higher = more strict

**Note**: Sparkle detection is exploratory. Frame counting is the primary method.

OCR Settings
------------

Image Preprocessing
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   OCR_UPSCALE_FACTOR = 2
   OCR_BINARY_THRESHOLD = 128

**Description**:

- ``UPSCALE_FACTOR``: LANCZOS4 upsampling multiplier (improves OCR accuracy)
- ``BINARY_THRESHOLD``: Grayscale to binary conversion threshold

**Tuning**:

- **Upscale (1-3)**: Higher = more accurate OCR, slower processing
- **Binary (100-150)**: Adjust based on image brightness

GPU Acceleration
~~~~~~~~~~~~~~~~

.. code-block:: python

   OCR_USE_GPU = True

**Description**: Enable CUDA acceleration for EasyOCR (5-10× faster).

**Requirements**:

- NVIDIA GPU with CUDA support
- Install: ``pip install -e .[cuda]``

**Auto-detection**: Falls back to CPU if GPU not available.

Fuzzy Matching
~~~~~~~~~~~~~~

.. code-block:: python

   FUZZY_MATCH_THRESHOLD = 80  # 0-100

**Description**: Minimum similarity score for Pokémon name matching.

**Tuning**:

- **80-85**: Balanced (recommended)
- **85-95**: More strict (fewer false matches)
- **70-80**: More lenient (handles more OCR errors)

Screen Region Coordinates
-------------------------

Pokémon Black 2 has specific screen regions for detection:

Name Region
~~~~~~~~~~~

.. code-block:: python

   NAME_REGION_X1 = 40
   NAME_REGION_Y1 = 30
   NAME_REGION_X2 = 200
   NAME_REGION_Y2 = 60

**Description**: Where Pokémon name appears during encounter.

**Coordinates**: (x1, y1) = top-left, (x2, y2) = bottom-right

Center Region (Sparkles)
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   CENTER_REGION_X1 = 80
   CENTER_REGION_Y1 = 150
   CENTER_REGION_X2 = 176
   CENTER_REGION_Y2 = 230

**Description**: Where shiny sparkle effect appears.

**Note**: Adjust only if using different game version or resolution.

Multi-Process Settings
----------------------

RNG Desynchronization
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   WORKER_RNG_BASE_OFFSET_FRAMES = 60  # 1s per worker
   WORKER_RNG_JITTER_FRAMES = 30       # 0-0.5s randomization

**Description**: Controls how workers desynchronize their RNG states.

**Algorithm**:

- Worker N offset = ``N × BASE_OFFSET + random(0, JITTER)``
- Creates non-overlapping ranges for unique encounters

**Tuning**:

- **Faster startup**: Decrease ``BASE_OFFSET`` (30-50)
- **More unique RNG**: Increase ``BASE_OFFSET`` (90-120)
- **Less randomization**: Decrease ``JITTER`` (10-20)
- **More randomization**: Increase ``JITTER`` (40-60)

**Impact**: 4 workers with defaults = 3.5s startup time

Queue Management
~~~~~~~~~~~~~~~~

.. code-block:: python

   SCREENSHOT_QUEUE_MAXSIZE = 10  # Frames per worker

**Description**: Maximum buffered frames in screenshot queue.

**Tuning**:

- **Larger (15-20)**: Smoother streaming, more memory usage
- **Smaller (5-8)**: Less memory, possible frame drops

**Recommendation**: 10 frames per worker (balance)

Barrier Synchronization
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   BARRIER_TIMEOUT = 30  # Seconds

**Description**: Maximum wait time for worker synchronization.

**Tuning**:

- **Longer (60-120)**: For slow systems or many workers
- **Shorter (15-20)**: For fast systems

**Note**: Prevents infinite hang if worker fails to initialize.

GUI Settings
------------

Window Dimensions
~~~~~~~~~~~~~~~~~

.. code-block:: python

   GUI_WINDOW_WIDTH = 1920
   GUI_WINDOW_HEIGHT = 1080

**Description**: Initial window size (auto-maximized on startup).

**Note**: Window is responsive and adapts to resize.

Rendering Performance
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   GUI_TARGET_FPS = 60

**Description**: Target rendering frame rate.

**Tuning**:

- **30 FPS**: Lower CPU usage, less smooth
- **60 FPS**: Smooth rendering (recommended)
- **120 FPS**: Higher CPU usage, minimal visual benefit

Panel Layout
~~~~~~~~~~~~

.. code-block:: python

   WORKER_PANEL_WIDTH = 426   # Video + stats
   WORKER_PANEL_HEIGHT = 414  # Native DS height
   SIDEBAR_WIDTH = 350        # Aggregate + shiny log

   MAX_GRID_COLUMNS = 4       # Max columns
   WORKER_PANEL_SPACING = 10  # Pixels between panels

**Description**: Panel dimensions and grid layout.

**Note**: Layout automatically adapts to worker count.

File Paths
----------

Resource Directories
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   POKEMON_NAMES_DIR = "resources/pokemon_names"

**Description**: Location of Pokémon name databases (Gen 1-9).

**Custom Database**: Point to custom directory if needed.

Output Files
~~~~~~~~~~~~

.. code-block:: python

   SHINY_LOG_FILE = "shiny_log.json"
   ENCOUNTER_STATS_FILE = "encounter_stats.json"

**Description**: Output file names for session data.

**Custom Location**: Use absolute paths for custom directories.

Emulator Settings
-----------------

Emulation Speed
~~~~~~~~~~~~~~~

.. code-block:: python

   EMULATOR_FPS_TARGET = 60

**Description**: Target emulation frame rate.

**Values**:

- **60 FPS**: Real-time speed (recommended)
- **120 FPS**: 2× speed (faster hunting, higher CPU usage)
- **30 FPS**: 0.5× speed (lower CPU usage, slower hunting)

Save State Naming
~~~~~~~~~~~~~~~~~

.. code-block:: python

   SHINY_SAVE_PREFIX = "shiny"
   SHINY_SAVE_SUFFIX = ".dst"

**Description**: Format for auto-saved shiny states.

**Example**: ``shiny_2_20250115_143215.dst``

Environment Variables
---------------------

Some settings can be overridden via environment variables:

.. code-block:: bash

   # Windows (PowerShell)
   $env:OCR_USE_GPU = "false"
   $env:POKEMON_NAMES_DIR = "C:\custom\names"

   # Linux/macOS (Bash)
   export OCR_USE_GPU=false
   export POKEMON_NAMES_DIR=/custom/names

Supported Variables
~~~~~~~~~~~~~~~~~~~

- ``OCR_USE_GPU``: Enable/disable GPU (true/false)
- ``POKEMON_NAMES_DIR``: Custom Pokémon names directory
- ``SHINY_LOG_FILE``: Custom shiny log path
- ``ENCOUNTER_STATS_FILE``: Custom stats file path

Configuration Examples
----------------------

High Accuracy Setup
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Strict detection (fewer false positives)
   SHINY_FRAME_DIFF_THRESHOLD = 550
   FUZZY_MATCH_THRESHOLD = 90
   OCR_UPSCALE_FACTOR = 3

Fast Performance Setup
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Speed over accuracy
   OCR_UPSCALE_FACTOR = 1
   EMULATOR_FPS_TARGET = 120
   WORKER_RNG_BASE_OFFSET_FRAMES = 30

Balanced Setup (Default)
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Recommended for most users
   SHINY_FRAME_DIFF_THRESHOLD = 500
   OCR_UPSCALE_FACTOR = 2
   FUZZY_MATCH_THRESHOLD = 80
   EMULATOR_FPS_TARGET = 60

Best Practices
--------------

1. **Test changes incrementally**: Adjust one parameter at a time
2. **Document modifications**: Add comments explaining changes
3. **Use version control**: Track config in Git
4. **Validate thresholds**: Test with known shiny/non-shiny encounters
5. **Share optimizations**: Contribute successful configs via PR

Troubleshooting
---------------

False Positives
~~~~~~~~~~~~~~~

**Problem**: Non-shinies detected as shiny

**Solution**: Increase ``SHINY_FRAME_DIFF_THRESHOLD`` (550-600)

False Negatives
~~~~~~~~~~~~~~~

**Problem**: Shinies not detected

**Solution**: Decrease ``SHINY_FRAME_DIFF_THRESHOLD`` (450-480)

OCR Errors
~~~~~~~~~~

**Problem**: Pokémon names not recognized

**Solutions**:

1. Increase ``OCR_UPSCALE_FACTOR`` (3)
2. Adjust ``OCR_BINARY_THRESHOLD`` (100-150)
3. Lower ``FUZZY_MATCH_THRESHOLD`` (75-80)

Slow Performance
~~~~~~~~~~~~~~~~

**Problem**: Low FPS, laggy GUI

**Solutions**:

1. Enable GPU: ``pip install -e .[cuda]``
2. Reduce ``OCR_UPSCALE_FACTOR`` (1)
3. Lower ``GUI_TARGET_FPS`` (30)
4. Reduce ``num_workers``

See Also
--------

- :doc:`api/config` - Complete configuration API reference
- :doc:`usage` - Usage guide
- :doc:`troubleshooting` - Common issues
- ``examples/data_exploration_and_algorithm_design.ipynb`` - Threshold validation
