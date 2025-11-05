utils - Utility Modules
========================

.. automodule:: pyshiny_hunter.utils
   :members:
   :undoc-members:
   :show-inheritance:

Overview
--------

The ``utils`` package provides utility functions and helper classes used throughout PyShiny Hunter.

Modules
-------

gui_utils - GUI Utilities
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: pyshiny_hunter.utils.gui_utils
   :members:
   :undoc-members:
   :show-inheritance:

GUI helper functions for texture management and rendering.

Functions
^^^^^^^^^

.. autofunction:: pyshiny_hunter.utils.gui_utils.create_texture_from_frame

   Creates an OpenGL texture from a NumPy frame array.

   :param frame: BGR image array from OpenCV (height, width, 3)
   :type frame: numpy.ndarray
   :return: OpenGL texture ID
   :rtype: int

   **Implementation:**

   1. Convert BGR → RGB
   2. Flip image vertically (OpenGL coordinates)
   3. Create OpenGL texture
   4. Set texture parameters (LINEAR filtering, CLAMP wrapping)
   5. Upload texture data

   **Usage:**

   .. code-block:: python

      import cv2
      from pyshiny_hunter.utils.gui_utils import create_texture_from_frame

      # Capture frame from emulator
      frame = emulator.get_screenshot()  # (384, 256, 3) BGR

      # Create OpenGL texture
      texture_id = create_texture_from_frame(frame)

      # Render in ImGui
      imgui.image(texture_id, 256, 384)

.. autofunction:: pyshiny_hunter.utils.gui_utils.delete_texture

   Deletes an OpenGL texture to free GPU memory.

   :param texture_id: OpenGL texture ID to delete
   :type texture_id: int

   **Usage:**

   .. code-block:: python

      # Clean up texture when done
      delete_texture(texture_id)

pokemon_loader - Pokémon Name Database
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: pyshiny_hunter.utils.pokemon_loader
   :members:
   :undoc-members:
   :show-inheritance:

Loads Pokémon names from JSON databases.

Functions
^^^^^^^^^

.. autofunction:: pyshiny_hunter.utils.pokemon_loader.load_all_pokemon_names

   Loads all Pokémon names from Gen 1-9 JSON files.

   :return: List of Pokémon names
   :rtype: list[str]

   **Returns:**

   - List of 890+ Pokémon names (English)
   - Names from resources/pokemon_names/ directory
   - Generations 1-9 included

   **Usage:**

   .. code-block:: python

      from pyshiny_hunter.utils.pokemon_loader import load_all_pokemon_names

      # Load all Pokémon names
      pokemon_names = load_all_pokemon_names()

      print(f"Loaded {len(pokemon_names)} Pokémon names")
      print(pokemon_names[:5])  # ['Bulbasaur', 'Ivysaur', 'Venusaur', ...]

.. autofunction:: pyshiny_hunter.utils.pokemon_loader.load_generation

   Loads Pokémon names from a specific generation.

   :param generation: Generation number (1-9)
   :type generation: int
   :return: List of Pokémon names from that generation
   :rtype: list[str]

   **Generations:**

   - Gen 1: Kanto (001-151)
   - Gen 2: Johto (152-251)
   - Gen 3: Hoenn (252-386)
   - Gen 4: Sinnoh (387-493)
   - Gen 5: Unova (494-649) - Black 2 coverage
   - Gen 6: Kalos (650-721)
   - Gen 7: Alola (722-809)
   - Gen 8: Galar (810-905)
   - Gen 9: Paldea (906-1025)

   **Usage:**

   .. code-block:: python

      from pyshiny_hunter.utils.pokemon_loader import load_generation

      # Load only Gen 5 (Black 2 encounters)
      gen5_pokemon = load_generation(5)

      print(f"Gen 5 Pokémon: {len(gen5_pokemon)}")
      print(gen5_pokemon[:3])  # ['Victini', 'Snivy', 'Servine', ...]

logger - Module Logger
~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: pyshiny_hunter.module_logger
   :members:
   :undoc-members:
   :show-inheritance:

Provides consistent logging across all modules.

Functions
^^^^^^^^^

.. autofunction:: pyshiny_hunter.module_logger.get_logger

   Gets or creates a logger for a module.

   :param name: Module name (usually __name__)
   :type name: str
   :return: Configured logger instance
   :rtype: logging.Logger

   **Configuration:**

   - Format: ``[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s``
   - Level: INFO (default)
   - Handler: StreamHandler (console output)

   **Usage:**

   .. code-block:: python

      from pyshiny_hunter.module_logger import get_logger

      logger = get_logger(__name__)

      logger.info("Starting shiny hunt...")
      logger.debug("Frame 12345 processed")
      logger.error("Failed to load ROM")

Utility Classes
---------------

TextureManager
~~~~~~~~~~~~~~

Helper class for managing OpenGL textures (if implemented):

.. code-block:: python

   class TextureManager:
       """Manages OpenGL texture lifecycle"""

       def __init__(self):
           self.textures = {}

       def create_or_update(self, key, frame):
           """Create new texture or update existing"""
           if key in self.textures:
               delete_texture(self.textures[key])
           self.textures[key] = create_texture_from_frame(frame)
           return self.textures[key]

       def cleanup(self):
           """Delete all managed textures"""
           for texture_id in self.textures.values():
               delete_texture(texture_id)
           self.textures.clear()

Common Patterns
---------------

Frame Processing
~~~~~~~~~~~~~~~~

.. code-block:: python

   import cv2
   import numpy as np
   from pyshiny_hunter.utils.gui_utils import create_texture_from_frame

   # Capture and display frame
   frame = emulator.get_screenshot()  # (384, 256, 3) BGR

   # Option 1: Direct display
   texture_id = create_texture_from_frame(frame)
   imgui.image(texture_id, 256, 384)

   # Option 2: Process first, then display
   gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
   processed = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)[1]
   colored = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)
   texture_id = create_texture_from_frame(colored)
   imgui.image(texture_id, 256, 384)

Pokémon Name Lookup
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pyshiny_hunter.utils.pokemon_loader import load_all_pokemon_names
   from rapidfuzz import fuzz

   # Load database once
   pokemon_names = load_all_pokemon_names()

   # Fuzzy match OCR result
   ocr_result = "Wotchog"  # OCR error
   best_match = max(
       pokemon_names,
       key=lambda name: fuzz.ratio(ocr_result.lower(), name.lower())
   )

   print(f"OCR: '{ocr_result}' → Match: '{best_match}'")
   # Output: OCR: 'Wotchog' → Match: 'Watchog'

Logging Best Practices
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pyshiny_hunter.module_logger import get_logger

   logger = get_logger(__name__)

   # Use appropriate levels
   logger.debug("Detailed info for debugging")
   logger.info("General information")
   logger.warning("Something unexpected happened")
   logger.error("Error occurred, but program continues")
   logger.critical("Critical error, program may crash")

   # Include context in messages
   logger.info(f"Processed {frame_count} frames in {elapsed:.2f}s")
   logger.error(f"Failed to load ROM: {rom_path}")

   # Use structured logging
   logger.info(
       "Encounter detected",
       extra={"pokemon": "Watchog", "frame": 12345}
   )

Performance Tips
----------------

Texture Management
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Bad: Creates new texture every frame (memory leak!)
   for frame in frames:
       texture_id = create_texture_from_frame(frame)
       imgui.image(texture_id, 256, 384)

   # Good: Reuse texture ID
   texture_id = None
   for frame in frames:
       if texture_id:
           delete_texture(texture_id)
       texture_id = create_texture_from_frame(frame)
       imgui.image(texture_id, 256, 384)

   # Better: Use TextureManager
   manager = TextureManager()
   for i, frame in enumerate(frames):
       texture_id = manager.create_or_update(f"worker_{i}", frame)
       imgui.image(texture_id, 256, 384)
   manager.cleanup()

Pokémon Name Loading
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Bad: Load names every time
   def match_pokemon(ocr_result):
       names = load_all_pokemon_names()  # Slow!
       return fuzzy_match(ocr_result, names)

   # Good: Load once, reuse
   POKEMON_NAMES = load_all_pokemon_names()

   def match_pokemon(ocr_result):
       return fuzzy_match(ocr_result, POKEMON_NAMES)

See Also
--------

- :doc:`gui_process` - Uses gui_utils for texture rendering
- :doc:`enhanced_ocr` - Uses pokemon_loader for name database
- Python logging documentation: https://docs.python.org/3/library/logging.html
