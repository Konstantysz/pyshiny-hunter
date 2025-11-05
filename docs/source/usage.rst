Usage Guide
===========

This guide covers how to use PyShiny Hunter for automated shiny hunting.

Basic Usage
-----------

Single Mode (Default)
~~~~~~~~~~~~~~~~~~~~~

Run a single emulator instance with GUI:

.. code-block:: bash

   pyshiny-hunter path/to/pokemon_black2.nds

With save state:

.. code-block:: bash

   pyshiny-hunter roms/pokemon_black2.nds --state saves/shiny_hunt.dst

With save file:

.. code-block:: bash

   pyshiny-hunter roms/pokemon_black2.nds --sav saves/game.sav

Multi-Process Mode
~~~~~~~~~~~~~~~~~~

Run multiple emulators with unified GUI:

.. code-block:: bash

   # 2 workers
   pyshiny-hunter roms/black2.nds --state saves/hunt.dst --num-workers 2

   # 4 workers (recommended)
   pyshiny-hunter roms/black2.nds --state saves/hunt.dst --num-workers 4

   # 8 workers (high-end systems)
   pyshiny-hunter roms/black2.nds --state saves/hunt.dst --num-workers 8

Command-Line Options
--------------------

Required Arguments
~~~~~~~~~~~~~~~~~~

.. code-block:: text

   rom                Path to .nds ROM file

Optional Arguments
~~~~~~~~~~~~~~~~~~

.. code-block:: text

   --state STATE      Path to .dst save state file
   --sav SAV          Path to .sav save file
   --num-workers N    Number of emulator processes (default: 1)
   -h, --help         Show help message

Examples
~~~~~~~~

.. code-block:: bash

   # Minimal (single mode)
   pyshiny-hunter game.nds

   # With save state
   pyshiny-hunter game.nds --state hunt.dst

   # Multi-process with 4 workers
   pyshiny-hunter game.nds --state hunt.dst --num-workers 4

   # All options
   pyshiny-hunter roms/black2.nds \
       --state saves/route1.dst \
       --sav saves/game.sav \
       --num-workers 4

GUI Interface
-------------

Single Mode GUI
~~~~~~~~~~~~~~~

The single mode GUI displays:

- **Emulator Screen**: Real-time video feed (256×384 pixels)
- **Hunter State**: Current state (search, battle, etc.)
- **Frame Count**: Total frames processed
- **FPS**: Emulator performance
- **Encounters**: Total and per-Pokémon breakdown

Multi-Process GUI
~~~~~~~~~~~~~~~~~

The unified GUI shows:

**Worker Panels** (left side):

- Live emulator video (256×384)
- Worker status (running/stalled)
- Current state
- Frame count
- Encounter breakdown

**Aggregate Statistics** (right top):

- Total encounters across all workers
- Average worker FPS
- GUI FPS
- Pokémon breakdown with percentages
- Worker contribution leaderboard

**Shiny Log** (right bottom):

- Last 5 shinies found
- Worker ID, timestamp
- Frame difference
- Save file location
- Encounters at discovery time

GUI Controls
~~~~~~~~~~~~

- **Close Window**: Stop hunting and exit
- **Maximize**: Auto-maximized on startup (can be un-maximized)
- **Resize**: Layout adapts to window size

Hunting Workflow
----------------

1. Preparation
~~~~~~~~~~~~~~

Create a save state at your hunting location:

.. code-block:: bash

   # 1. Load ROM in DeSmuME standalone
   # 2. Navigate to hunting spot (e.g., Route 1 grass)
   # 3. Save state: File → Save State As...
   # 4. Save as "shiny_hunt.dst"

2. Start Hunting
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Single mode
   pyshiny-hunter roms/black2.nds --state saves/shiny_hunt.dst

   # Multi-process (4 workers)
   pyshiny-hunter roms/black2.nds --state saves/shiny_hunt.dst --num-workers 4

3. Monitor Progress
~~~~~~~~~~~~~~~~~~~

Watch the GUI for:

- **Encounter counter** increasing
- **FPS** around 60 (full speed)
- **Worker status** staying green (not stalled)

4. Shiny Detection
~~~~~~~~~~~~~~~~~~

When a shiny is found:

1. **Application pauses** (stays on shiny encounter)
2. **Save state created** automatically (``shiny_<worker>_<timestamp>.dst``)
3. **Log entry added** to ``shiny_log.json``
4. **GUI highlights** the discovery in Shiny Log panel

5. Retrieve Shiny
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # 1. Close PyShiny Hunter
   # 2. Open DeSmuME standalone
   # 3. Load ROM: File → Open ROM
   # 4. Load shiny save state: File → Load State From...
   # 5. Select "shiny_<worker>_<timestamp>.dst"
   # 6. Catch your shiny Pokémon!

Best Practices
--------------

Optimal Worker Count
~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - System
     - Workers
     - Rationale
   * - Laptop (4 cores)
     - 2-3
     - Leaves CPU for OS
   * - Desktop (6 cores)
     - 4
     - Balanced performance
   * - Workstation (8+ cores)
     - 6-8
     - Maximize throughput

**Formula**: ``num_workers = CPU_cores - 2`` (leave 2 for OS + GUI)

Save State Location
~~~~~~~~~~~~~~~~~~~

Good hunting locations in Pokémon Black 2:

.. list-table::
   :header-rows: 1

   * - Location
     - Pokémon
     - Shiny Odds
   * - Route 1
     - Patrat, Lillipup
     - 1/8192
   * - Route 2
     - Watchog, Patrat
     - 1/8192
   * - Floccesy Ranch
     - Riolu, Mareep
     - 1/8192

Tips:

- Save **just before** entering grass
- Ensure **no battle in progress**
- Use **repels off** (want encounters)

Performance Optimization
~~~~~~~~~~~~~~~~~~~~~~~~

For best performance:

.. code-block:: bash

   # 1. Close unnecessary applications
   # 2. Use GPU acceleration (if available)
   pip install -e .[cuda]

   # 3. Monitor system resources
   # Task Manager (Windows) or htop (Linux)

   # 4. Adjust worker count if CPU saturated
   # Reduce workers if system becomes slow

Session Management
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Start session
   pyshiny-hunter roms/black2.nds --state hunt.dst --num-workers 4

   # Statistics saved on exit to:
   # - shiny_log.json (all shinies found)
   # - encounter_stats.json (session statistics)

Output Files
------------

Shiny Log
~~~~~~~~~

``shiny_log.json`` contains all shiny discoveries:

.. code-block:: json

   [
       {
           "worker_id": 2,
           "timestamp": "2025-01-15 14:32:15",
           "frame_diff": 523,
           "save_file": "shiny_2_20250115_143215.dst",
           "total_encounters": 142,
           "encounters": {
               "Watchog": 89,
               "Patrat": 53
           }
       }
   ]

Encounter Statistics
~~~~~~~~~~~~~~~~~~~~

``encounter_stats.json`` contains session summary:

.. code-block:: json

   {
       "session_start": "2025-01-15 14:00:00",
       "session_end": "2025-01-15 15:30:00",
       "total_encounters": 234,
       "pokemon_counts": {
           "Watchog": 145,
           "Patrat": 89
       },
       "worker_encounters": {
           "0": 58,
           "1": 60,
           "2": 57,
           "3": 59
       }
   }

Save States
~~~~~~~~~~~

Shiny save states are named:

.. code-block:: text

   shiny_<worker_id>_<timestamp>.dst

Example: ``shiny_2_20250115_143215.dst``

Troubleshooting
---------------

Low FPS
~~~~~~~

If emulator FPS < 55:

1. **Reduce workers**: Try fewer workers
2. **Close apps**: Free up CPU resources
3. **Check CPU usage**: Task Manager / htop

Stalled Workers
~~~~~~~~~~~~~~~

If worker status shows "STALLED" (red):

1. **Check logs**: Look for error messages
2. **Restart**: Close and relaunch application
3. **Reduce workers**: May be overloading system

False Positives
~~~~~~~~~~~~~~~

If non-shinies detected as shiny:

1. **Check frame threshold**: See :doc:`configuration`
2. **Report issue**: Create GitHub issue with details

No Encounters
~~~~~~~~~~~~~

If encounter counter stays at 0:

1. **Check save state**: Must be in wild grass area
2. **Verify ROM**: Ensure correct game version
3. **Check state**: Hunter should transition to "battle"

Advanced Usage
--------------

Custom Configuration
~~~~~~~~~~~~~~~~~~~~

Create custom config file:

.. code-block:: python

   # custom_config.py
   from pyshiny_hunter import config

   # Adjust thresholds
   config.SHINY_FRAME_DIFF_THRESHOLD = 550
   config.OCR_UPSCALE_FACTOR = 3

See :doc:`configuration` for all options.

Programmatic Usage
~~~~~~~~~~~~~~~~~~

Use as Python library:

.. code-block:: python

   from pyshiny_hunter.black2_hunter import Black2Hunter
   from pyshiny_hunter.py_desmume_manager import PyDeSmuMEManager

   # Initialize
   manager = PyDeSmuMEManager(
       rom_path="roms/black2.nds",
       save_state_path="saves/hunt.dst"
   )

   hunter = Black2Hunter()

   # Run
   manager.run()

See API documentation for details: :doc:`api/modules`

Next Steps
----------

- **Configure settings**: :doc:`configuration`
- **Understand architecture**: :doc:`architecture`
- **Contribute**: :doc:`contributing`

See Also
--------

- :doc:`installation` - Installation guide
- :doc:`configuration` - Configuration options
- :doc:`troubleshooting` - Common issues
- ``docs/UNIFIED_GUI.md`` - Multi-process architecture
