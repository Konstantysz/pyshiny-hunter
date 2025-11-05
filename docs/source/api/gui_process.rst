gui_process - Unified GUI Rendering
====================================

.. automodule:: pyshiny_hunter.gui_process
   :members:
   :undoc-members:
   :show-inheritance:

Overview
--------

The ``gui_process`` module implements the unified GUI that displays multiple worker streams in a single window. It receives screenshots from headless worker processes and renders them in a professional grid layout with real-time statistics.

Key Features
------------

- **Multi-Worker Display**: Grid layout with up to 12+ worker panels
- **Live Video Streaming**: Real-time 60 FPS feeds from all workers
- **Aggregate Statistics**: Total encounters, shiny probability, worker contributions
- **Shiny Log Panel**: Last 5 shinies with metadata
- **Progress Bar**: Initialization progress with per-worker status
- **Auto-Maximization**: Window automatically maximizes on startup
- **Responsive Layout**: Adapts to window resize and screen resolution

Functions
---------

Main GUI Process
~~~~~~~~~~~~~~~~

.. autofunction:: pyshiny_hunter.gui_process.unified_gui_main_process

   Main GUI process function. Renders unified window with all worker streams.

   :param num_workers: Number of worker processes
   :param screenshot_queue: Queue receiving screenshots from workers
   :param shared_stats: Shared dict with encounter statistics
   :param shared_shiny_log: Shared list with shiny discoveries
   :param session_start_time: Shared timestamp for session tracking
   :param worker_status: Shared dict with initialization status

GUI Layout
----------

Grid System
~~~~~~~~~~~

Workers are arranged in an optimal grid:

.. code-block:: python

   # Grid dimensions
   cols = min(4, math.ceil(math.sqrt(num_workers)))
   rows = math.ceil(num_workers / cols)

   # Examples:
   # 1-2 workers: 1×1, 1×2
   # 3-4 workers: 2×2
   # 5-6 workers: 2×3
   # 7-9 workers: 3×3
   # 10-12 workers: 3×4

Worker Panel Layout
~~~~~~~~~~~~~~~~~~~

Each worker panel uses a horizontal layout:

.. code-block:: text

   ┌─────────────────────────────────────┐
   │ Worker 0                            │
   ├──────────────┬──────────────────────┤
   │              │ Status: Running      │
   │   Emulator   │ State: search        │
   │   Video      │ Frame: 12345         │
   │   256×384    │ Encounters: 42       │
   │              │                      │
   │              │ Pokémon:             │
   │              │   Watchog: 23        │
   │              │   Patrat: 19         │
   └──────────────┴──────────────────────┘

Dimensions:

- **Video**: 256px wide × 384px tall (native DS resolution)
- **Stats**: 150px wide × 384px tall
- **Total Panel**: 426px × 414px

Sidebar Panels
~~~~~~~~~~~~~~

Fixed on right side:

1. **Aggregate Statistics** (top half)

   - Total encounters across all workers
   - Shiny probability calculation
   - Encounters per minute
   - Per-Pokémon breakdown
   - Worker contribution leaderboard

2. **Shiny Log** (bottom half)

   - Last 5 shinies found
   - Worker ID, timestamp, frame diff
   - Save file location
   - Total encounters at discovery

Initialization Progress
-----------------------

During startup, displays progress bar instead of worker panels:

.. code-block:: text

   ┌─────────────────────────────────────┐
   │  Initializing Workers...            │
   │                                     │
   │  Progress: ████████░░░░ 2/4         │
   │                                     │
   │  Worker 0: Ready            ✓       │
   │  Worker 1: Ready            ✓       │
   │  Worker 2: Desyncing RNG... ⟳       │
   │  Worker 3: Loading...       ⏳      │
   └─────────────────────────────────────┘

Status Colors:

- 🔵 **Loading**: "Loading emulator..." (blue)
- 🔷 **Desyncing**: "Desyncing RNG..." (cyan)
- 🟡 **Waiting**: "Waiting for others..." (yellow)
- 🟢 **Ready**: "Ready" (green)

Window Management
-----------------

Auto-Maximization
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Window automatically maximizes on startup
   glfw.maximize_window(window)

Responsive Sizing
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Track window size every frame
   current_width, current_height = glfw.get_window_size(window)

   # Calculate panel positions dynamically
   worker_panel_width = (available_width / cols) - 10
   sidebar_x = current_width - sidebar_width

Panels adapt to:

- Window maximization
- Manual resize
- Different screen resolutions

Statistics Display
------------------

Aggregate Stats Panel
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Example display
   Total Encounters: 142
   Active Workers: 4

   Average Worker FPS: 59.9

   Worker FPS:
     Worker 0: 60.1
     Worker 1: 59.8
     Worker 2: 59.9
     Worker 3: 59.8

   GUI FPS: 60.0

   Pokémon Breakdown:
     Watchog: 89 (62.7%)
     Patrat: 53 (37.3%)

   Worker Contributions:
     Worker 2: 37 encounters (26.1%)
     Worker 0: 36 encounters (25.4%)
     Worker 1: 35 encounters (24.6%)
     Worker 3: 34 encounters (23.9%)

Shiny Log Panel
~~~~~~~~~~~~~~~

.. code-block:: python

   # Example entry
   Shiny #1 (Worker 2)
   ━━━━━━━━━━━━━━━━━━━━
   Time: 2025-01-15 14:32:15
   Frame Diff: 523
   Save: shiny_2_20250115_143215.dst
   Total Encounters: 142
   Pokémon: Watchog: 89, Patrat: 53

Status Indicators
-----------------

Worker Status Colors
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Green: Worker active (updated within last 2 seconds)
   imgui.push_style_color(imgui.COLOR_TEXT, 0.0, 1.0, 0.0, 1.0)

   # Red: Worker stalled (no updates for >2 seconds)
   imgui.push_style_color(imgui.COLOR_TEXT, 1.0, 0.0, 0.0, 1.0)

Stall Detection
~~~~~~~~~~~~~~~

.. code-block:: python

   # Check last update time
   time_since_update = time.time() - last_update_time

   if time_since_update > 2.0:
       status = "STALLED"
   else:
       status = "Running"

Texture Management
------------------

OpenGL Texture Rendering
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pyshiny_hunter.utils.gui_utils import create_texture_from_frame

   # Create OpenGL texture from numpy array
   texture_id = create_texture_from_frame(frame)

   # Render texture in ImGui
   imgui.image(texture_id, 256, 384)

Frame Format:

- **Input**: NumPy array (384, 256, 3) BGR (from OpenCV)
- **Processing**: Convert BGR → RGB, flip vertically
- **Output**: OpenGL texture ID (GLuint)

Performance
-----------

Rendering Performance
~~~~~~~~~~~~~~~~~~~~~

- **Target FPS**: 60 FPS
- **Actual FPS**: 59-60 FPS (with V-Sync)
- **Frame Time**: ~16.7ms per frame

Memory Usage
~~~~~~~~~~~~

- **Base**: ~50-100 MB (ImGui + GLFW)
- **Per Worker**: ~10 MB (texture buffers)
- **4 Workers**: ~90-140 MB total

CPU Usage
~~~~~~~~~

- **GUI Thread**: 15-25% of 1 core (rendering)
- **Worker Processes**: 100% of 1 core each (emulation)

Configuration
-------------

GUI settings from ``config.py``:

.. code-block:: python

   # Window settings
   GUI_WINDOW_WIDTH = 1920        # Initial width
   GUI_WINDOW_HEIGHT = 1080       # Initial height
   GUI_TARGET_FPS = 60            # Rendering FPS

   # Panel sizes
   WORKER_PANEL_WIDTH = 426       # Video + stats
   WORKER_PANEL_HEIGHT = 414      # Native DS height
   SIDEBAR_WIDTH = 350            # Aggregate + shiny log

   # Grid settings
   MAX_GRID_COLUMNS = 4           # Max columns
   WORKER_PANEL_SPACING = 10      # Pixels between panels

Usage Example
-------------

Launching GUI
~~~~~~~~~~~~~

.. code-block:: python

   from pyshiny_hunter.gui_process import unified_gui_main_process
   import multiprocessing as mp

   # Create shared resources
   manager = mp.Manager()
   screenshot_queue = mp.Queue()
   shared_stats = manager.dict()
   shared_shiny_log = manager.list()
   session_start = manager.Value('d', time.time())
   worker_status = manager.dict()

   # Launch GUI (blocks until window closed)
   unified_gui_main_process(
       num_workers=4,
       screenshot_queue=screenshot_queue,
       shared_stats=shared_stats,
       shared_shiny_log=shared_shiny_log,
       session_start_time=session_start,
       worker_status=worker_status
   )

Accessing Shared State
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Read shared statistics
   total = shared_stats.get("total_encounters", 0)
   pokemon = shared_stats.get("pokemon_counts", {})

   # Read shiny log
   shinies = list(shared_shiny_log)
   print(f"Found {len(shinies)} shinies!")

See Also
--------

- :doc:`worker_process` - Worker process implementation
- :doc:`py_desmume_manager` - Emulator management
- ``pyshiny_hunter.utils.gui_utils`` - GUI utility functions
- ``docs/UNIFIED_GUI.md`` - Multi-process architecture guide
