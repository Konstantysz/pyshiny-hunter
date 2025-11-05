py_desmume_manager - DeSmuME Emulator Integration
=================================================

.. automodule:: pyshiny_hunter.py_desmume_manager
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Overview
--------

The ``py_desmume_manager`` module provides integration with the DeSmuME Nintendo DS emulator through the ``py-desmume`` bindings. It handles emulator initialization, screen capture, GUI rendering, and input management.

Key Features
------------

- **Emulator Control**: Load ROMs, save states, and manage emulator lifecycle
- **Screen Capture**: Real-time 60 FPS frame capture from emulator
- **GUI Rendering**: ImGui-based interface with OpenGL texture rendering
- **Headless Mode**: Run without GUI for multi-process workers
- **FPS Monitoring**: Track emulator performance

Classes
-------

PyDeSmuMEManager
~~~~~~~~~~~~~~~~

.. autoclass:: pyshiny_hunter.py_desmume_manager.PyDeSmuMEManager
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   Main manager class handling emulator initialization and GUI rendering.

   .. automethod:: __init__
   .. automethod:: run
   .. automethod:: close

DeSmuMEWrapper
~~~~~~~~~~~~~~

.. autoclass:: pyshiny_hunter.py_desmume_manager.DeSmuMEWrapper
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   Wrapper class for individual DeSmuME emulator instance.

   .. automethod:: __init__
   .. automethod:: get_screenshot
   .. automethod:: update_fps
   .. automethod:: get_fps

Methods
-------

Emulator Management
~~~~~~~~~~~~~~~~~~~

.. automethod:: pyshiny_hunter.py_desmume_manager.PyDeSmuMEManager.__init__

   :param rom_path: Path to .nds ROM file
   :param save_state_path: Optional path to .dst save state file
   :param sav_path: Optional path to .sav save file
   :param headless: Run without GUI (for worker processes)

.. automethod:: pyshiny_hunter.py_desmume_manager.PyDeSmuMEManager.run

   Main event loop. Processes frames, handles inputs, and renders GUI.

.. automethod:: pyshiny_hunter.py_desmume_manager.PyDeSmuMEManager.close

   Clean up emulator and GUI resources.

Screen Capture
~~~~~~~~~~~~~~

.. automethod:: pyshiny_hunter.py_desmume_manager.DeSmuMEWrapper.get_screenshot

   :return: RGB image array (256×384×3)
   :rtype: numpy.ndarray

FPS Tracking
~~~~~~~~~~~~

.. automethod:: pyshiny_hunter.py_desmume_manager.DeSmuMEWrapper.update_fps

   Updates FPS counter based on frame timing (1-second window).

.. automethod:: pyshiny_hunter.py_desmume_manager.DeSmuMEWrapper.get_fps

   :return: Current FPS value
   :rtype: float

Internal Methods
~~~~~~~~~~~~~~~~

.. automethod:: pyshiny_hunter.py_desmume_manager.PyDeSmuMEManager._PyDeSmuMEManager__initialize_emulators
.. automethod:: pyshiny_hunter.py_desmume_manager.PyDeSmuMEManager._PyDeSmuMEManager__initialize_glfw_window
.. automethod:: pyshiny_hunter.py_desmume_manager.PyDeSmuMEManager._PyDeSmuMEManager__initialize_imgui
.. automethod:: pyshiny_hunter.py_desmume_manager.PyDeSmuMEManager._PyDeSmuMEManager__emulators_next_frame
.. automethod:: pyshiny_hunter.py_desmume_manager.PyDeSmuMEManager._PyDeSmuMEManager__render_imgui
.. automethod:: pyshiny_hunter.py_desmume_manager.PyDeSmuMEManager._PyDeSmuMEManager__process_inputs

Headless Mode
-------------

The manager supports headless mode for multi-process workers:

.. code-block:: python

   # Headless mode (no GUI)
   manager = PyDeSmuMEManager(
       rom_path="game.nds",
       headless=True
   )

   # GUI mode (default)
   manager = PyDeSmuMEManager(
       rom_path="game.nds",
       headless=False
   )

In headless mode:

- GLFW/ImGui initialization is skipped
- Only emulator core is initialized
- Screen capture still works via ``get_screenshot()``
- Used by worker processes in multi-process mode

GUI Components
--------------

The ImGui interface displays:

- **Emulator Screen**: Real-time video feed (256×384 pixels)
- **State Information**: Current hunter state
- **Frame Counter**: Total frames processed
- **FPS Display**: Emulator performance
- **Encounter Stats**: Total encounters and Pokémon breakdown

Window Management
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Window title
   "PyShiny Hunter - {rom_name}"

   # Window size
   Width: 800px
   Height: 600px

   # Rendering
   60 FPS target (V-Sync enabled)

Configuration
-------------

Emulator settings from ``config.py``:

.. code-block:: python

   # Window settings
   WINDOW_WIDTH = 800
   WINDOW_HEIGHT = 600
   WINDOW_TITLE = "PyShiny Hunter"

   # Emulator settings
   EMULATOR_FPS_TARGET = 60

Usage Example
-------------

Single Mode
~~~~~~~~~~~

.. code-block:: python

   from pyshiny_hunter.py_desmume_manager import PyDeSmuMEManager
   from pyshiny_hunter.black2_hunter import Black2Hunter

   # Initialize manager with GUI
   manager = PyDeSmuMEManager(
       rom_path="pokemon_black2.nds",
       save_state_path="shiny_hunt.dst"
   )

   # Create hunter
   hunter = Black2Hunter()

   # Run (blocks until window closed)
   manager.run()

Headless Worker
~~~~~~~~~~~~~~~

.. code-block:: python

   from pyshiny_hunter.py_desmume_manager import PyDeSmuMEManager

   # Initialize headless emulator
   manager = PyDeSmuMEManager(
       rom_path="pokemon_black2.nds",
       headless=True
   )

   # Get emulator wrapper
   emulator = manager.emulators[0]

   # Capture frame
   frame = emulator.get_screenshot()
   print(f"Frame shape: {frame.shape}")  # (384, 256, 3)

   # Check FPS
   emulator.update_fps()
   print(f"FPS: {emulator.get_fps()}")

Limitations
-----------

py-desmume Constraints
~~~~~~~~~~~~~~~~~~~~~~

- **Single Instance Per Process**: Only one DeSmuME instance allowed per process
- **Threading Limitation**: Creating second instance causes "access violation"
- **Multi-Process Solution**: Use separate processes for multiple emulators

See ``docs/UNIFIED_GUI.md`` for multi-process architecture details.

Platform Support
~~~~~~~~~~~~~~~~

- **Windows**: Full support
- **Linux**: Requires SDL2 libraries
- **macOS**: Limited support (check py-desmume compatibility)
