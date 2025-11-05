worker_process - Multi-Process Worker Management
================================================

.. automodule:: pyshiny_hunter.worker_process
   :members:
   :undoc-members:
   :show-inheritance:

Overview
--------

The ``worker_process`` module implements multi-process mode, allowing multiple emulator instances to run simultaneously with a unified GUI. Each worker runs in a separate process and streams screenshots to the main GUI process.

Key Features
------------

- **Headless Workers**: Each process runs an emulator without GUI
- **Video Streaming**: Real-time 60 FPS screenshot streaming via multiprocessing.Queue
- **RNG Desynchronization**: Hybrid progressive + random approach for unique encounters
- **Barrier Synchronization**: Workers start simultaneously after desync
- **Shared Statistics**: Centralized encounter tracking and shiny logging
- **Status Reporting**: Real-time progress updates during initialization

Functions
---------

Worker Process
~~~~~~~~~~~~~~

.. autofunction:: pyshiny_hunter.worker_process.headless_worker

   Main worker process function. Runs headless emulator and streams data to GUI.

   :param worker_id: Unique worker identifier (0, 1, 2, ...)
   :param rom_path: Path to .nds ROM file
   :param save_state_path: Optional path to .dst save state
   :param sav_path: Optional path to .sav save file
   :param screenshot_queue: Queue for sending screenshots to GUI
   :param shared_stats: Shared dict for encounter statistics
   :param shared_shiny_log: Shared list for shiny discoveries
   :param session_start_time: Shared timestamp for session tracking
   :param barrier: Synchronization barrier for coordinated startup
   :param worker_status: Shared dict for initialization status

Multi-Process Launcher
~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: pyshiny_hunter.worker_process.launch_multi_mode

   Launches multiple worker processes with unified GUI.

   :param num_workers: Number of emulator processes (1-12+)
   :param rom_path: Path to .nds ROM file
   :param save_state_path: Optional path to .dst save state
   :param sav_path: Optional path to .sav save file

RNG Desynchronization
---------------------

Algorithm
~~~~~~~~~

Workers use a hybrid approach to ensure unique RNG states:

1. **Progressive Base Offset**: ``worker_id × 60 frames`` (1 second per worker)
2. **Random Jitter**: ``+random(0, 30)`` frames (0-0.5s additional randomization)

This creates non-overlapping ranges:

.. code-block:: python

   Worker 0: [0, 30] frames       # 0.0 - 0.5s
   Worker 1: [60, 90] frames      # 1.0 - 1.5s
   Worker 2: [120, 150] frames    # 2.0 - 2.5s
   Worker 3: [180, 210] frames    # 3.0 - 3.5s

Benefits:

- **40× faster** than random 0-8192 approach (3.5s vs 2+ minutes for 4 workers)
- **100% unique** RNG states (no collision possible)
- **Predictable** startup time scaling

Configuration
~~~~~~~~~~~~~

.. code-block:: python

   # config.py
   WORKER_RNG_BASE_OFFSET_FRAMES = 60   # 1 second per worker
   WORKER_RNG_JITTER_FRAMES = 30        # 0-0.5s randomization

Barrier Synchronization
-----------------------

Workers synchronize using ``multiprocessing.Barrier``:

1. **Load Emulator**: Worker loads ROM and save state
2. **Desync RNG**: Worker advances RNG by calculated offset
3. **Wait at Barrier**: Worker waits for all others to finish
4. **Start Streaming**: All workers begin simultaneously

Timeline (4 workers):

.. code-block:: text

   T=0.0s  Main: Launch all workers + GUI
   T=0.5s  Worker 0: Load → Desync 12 frames → Wait
   T=1.2s  Worker 1: Load → Desync 88 frames → Wait
   T=2.1s  Worker 2: Load → Desync 125 frames → Wait
   T=3.3s  Worker 3: Load → Desync 199 frames → BARRIER RELEASED!
   T=3.4s  ALL WORKERS: Start streaming

Timeout Protection
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Barrier timeout prevents infinite hang
   barrier.wait(timeout=30)  # 30-second max wait

Shared State Management
-----------------------

The module uses ``multiprocessing.Manager()`` for shared state:

Encounter Statistics
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   shared_stats = {
       "total_encounters": 0,
       "pokemon_counts": {},      # {"Watchog": 89, "Patrat": 45}
       "worker_encounters": {},   # {0: 23, 1: 19, 2: 25, 3: 22}
   }

Shiny Log
~~~~~~~~~

.. code-block:: python

   shared_shiny_log = [
       {
           "worker_id": 2,
           "timestamp": "2025-01-15 14:32:15",
           "frame_diff": 523,
           "save_file": "shiny_2_20250115_143215.dst",
           "total_encounters": 142,
           "encounters": {"Watchog": 89, "Patrat": 53}
       },
       # ... more entries
   ]

Worker Status
~~~~~~~~~~~~~

.. code-block:: python

   worker_status = {
       0: "loading",     # Loading emulator
       1: "desyncing",   # Desyncing RNG
       2: "waiting",     # Waiting at barrier
       3: "ready",       # Ready to stream
   }

Screenshot Queue
----------------

Workers stream screenshots via ``multiprocessing.Queue``:

.. code-block:: python

   screenshot_queue.put({
       "worker_id": 0,
       "frame": frame,           # numpy.ndarray (384, 256, 3)
       "state": "search",        # Current hunter state
       "frame_count": 12345,     # Total frames processed
       "encounters": {...},      # Encounter dict
       "total_encounters": 42,   # Total count
       "fps": 59.8,             # Emulator FPS
   })

Queue Management:

- **Max Size**: 10 frames per worker (prevents memory buildup)
- **Non-Blocking Puts**: Drops frames if queue full (maintains 60 FPS)
- **Main Process**: Reads and displays latest frame

Performance
-----------

Startup Time Comparison
~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Workers
     - Old Method (Random)
     - New Method (Hybrid)
     - Speedup
   * - 2
     - 0-136s (avg 68s)
     - 1.5s
     - 45×
   * - 4
     - 0-136s (avg 68s)
     - 3.5s
     - 19×
   * - 8
     - 0-136s (avg 68s)
     - 7.5s
     - 9×

Scaling
~~~~~~~

- **Linear Scaling**: Startup time scales linearly with worker count
- **Memory Efficient**: Queue buffering prevents unbounded growth
- **CPU Usage**: Each worker runs at 100% of 1 core (expected)

Usage Example
-------------

Launching Multi-Process Mode
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pyshiny_hunter.worker_process import launch_multi_mode

   # Launch 4 workers with unified GUI
   launch_multi_mode(
       num_workers=4,
       rom_path="pokemon_black2.nds",
       save_state_path="shiny_hunt.dst"
   )

Direct Worker Usage
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pyshiny_hunter.worker_process import headless_worker
   import multiprocessing as mp

   # Create shared resources
   manager = mp.Manager()
   screenshot_queue = mp.Queue()
   shared_stats = manager.dict()
   shared_shiny_log = manager.list()
   session_start = manager.Value('d', time.time())
   barrier = mp.Barrier(2)
   worker_status = manager.dict()

   # Launch worker
   process = mp.Process(
       target=headless_worker,
       args=(
           0,                      # worker_id
           "game.nds",             # rom_path
           "hunt.dst",             # save_state_path
           None,                   # sav_path
           screenshot_queue,       # screenshot_queue
           shared_stats,           # shared_stats
           shared_shiny_log,       # shared_shiny_log
           session_start,          # session_start_time
           barrier,                # barrier
           worker_status,          # worker_status
       )
   )
   process.start()

   # Read screenshots
   while True:
       data = screenshot_queue.get()
       print(f"Worker {data['worker_id']}: Frame {data['frame_count']}")

Configuration
-------------

Multi-process settings from ``config.py``:

.. code-block:: python

   # RNG desynchronization
   WORKER_RNG_BASE_OFFSET_FRAMES = 60  # 1s per worker
   WORKER_RNG_JITTER_FRAMES = 30       # 0-0.5s jitter

   # Queue settings
   SCREENSHOT_QUEUE_MAXSIZE = 10       # Frames per worker

   # Synchronization
   BARRIER_TIMEOUT = 30                # Seconds

See Also
--------

- :doc:`gui_process` - Unified GUI rendering
- :doc:`py_desmume_manager` - Emulator management
- ``docs/UNIFIED_GUI.md`` - Multi-process architecture guide
