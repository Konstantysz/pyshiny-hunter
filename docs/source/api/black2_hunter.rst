black2_hunter - Pokémon Black 2 Implementation
==============================================

.. automodule:: pyshiny_hunter.black2_hunter
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Overview
--------

The ``black2_hunter`` module implements the game-specific hunting logic for Pokémon Black 2. It extends the abstract ``Hunter`` class with Computer Vision and OCR techniques tailored for this specific game.

Key Features
------------

- **Shiny Detection**: Analyzes animation frame counts and sparkle effects
- **OCR Pipeline**: Enhanced 3-stage OCR (EasyOCR → SymSpell → Fuzzy matching)
- **Animation Analysis**: Tracks frame differences to detect encounter animations
- **Battle Detection**: Monitors specific screen regions to detect battle state

Classes
-------

.. autoclass:: pyshiny_hunter.black2_hunter.Black2Hunter
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   .. automethod:: __init__
   .. automethod:: check_if_shiny
   .. automethod:: get_pokemon_name
   .. automethod:: is_in_battle
   .. automethod:: is_battle_over

Computer Vision Methods
-----------------------

Region Extraction
~~~~~~~~~~~~~~~~~

.. automethod:: pyshiny_hunter.black2_hunter.Black2Hunter._extract_name_region
.. automethod:: pyshiny_hunter.black2_hunter.Black2Hunter._extract_center_region

Animation Analysis
~~~~~~~~~~~~~~~~~~

.. automethod:: pyshiny_hunter.black2_hunter.Black2Hunter._analyze_animation
.. automethod:: pyshiny_hunter.black2_hunter.Black2Hunter._calculate_brightness

OCR Methods
-----------

.. automethod:: pyshiny_hunter.black2_hunter.Black2Hunter._preprocess_for_ocr
.. automethod:: pyshiny_hunter.black2_hunter.Black2Hunter._perform_ocr

Detection Algorithms
--------------------

Shiny Detection Algorithm
~~~~~~~~~~~~~~~~~~~~~~~~~~

The shiny detection combines two approaches:

1. **Animation Frame Counting** (Primary, ~95% accuracy)

   - Shiny encounters have longer entry animations (>500 frames)
   - Non-shiny encounters are shorter (<500 frames)
   - Threshold: ``SHINY_FRAME_DIFF_THRESHOLD = 500``

2. **Sparkle Detection** (Secondary, exploratory)

   - Analyzes brightness in center region during animation
   - Shiny Pokémon have distinctive sparkle effect
   - Threshold: ``SHINY_SPARKLE_BRIGHTNESS_THRESHOLD = 247``
   - Min area: ``SHINY_SPARKLE_MIN_AREA_PCT = 0.2`` (20% of region)

Battle Detection
~~~~~~~~~~~~~~~~

Monitors specific screen regions to detect:

- Battle start: Menu region changes color
- Battle end: Screen returns to overworld state

Configuration
-------------

All thresholds and parameters are defined in ``config.py``:

.. code-block:: python

   # Shiny detection thresholds
   SHINY_FRAME_DIFF_THRESHOLD = 500
   SHINY_SPARKLE_BRIGHTNESS_THRESHOLD = 247
   SHINY_SPARKLE_MIN_AREA_PCT = 0.2

   # OCR settings
   OCR_UPSCALE_FACTOR = 2
   OCR_BINARY_THRESHOLD = 128

Usage Example
-------------

.. code-block:: python

   from pyshiny_hunter.black2_hunter import Black2Hunter
   import numpy as np

   # Initialize hunter
   hunter = Black2Hunter()

   # Process frame
   frame = np.array(...)  # 256x384x3 BGR image
   hunter.update(frame)

   # Check current state
   print(hunter.current_state)  # e.g., "search", "battle", etc.

   # Access encounter statistics
   print(f"Total encounters: {hunter.total_encounters}")
   print(f"Encounters: {hunter.encounters}")
