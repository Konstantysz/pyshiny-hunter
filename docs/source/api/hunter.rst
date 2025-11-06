hunter - Abstract Hunter Base Class
====================================

.. automodule:: pyshiny_hunter.hunter
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Overview
--------

The ``hunter`` module provides the abstract base class for all game-specific hunters. It implements a state machine pattern using the ``python-statemachine`` library to manage the hunting workflow.

State Machine
-------------

The hunter state machine transitions through the following states:

1. **Search** - Searching for wild Pokémon encounters
2. **Check Shiny** - Checking if the encountered Pokémon is shiny
3. **Pre-Battle** - Transitioning to battle screen
4. **Battle** - In battle with the Pokémon
5. **Found** - Shiny Pokémon found (terminal state)

Classes
-------

.. autoclass:: pyshiny_hunter.hunter.Hunter
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   .. automethod:: __init__
   .. automethod:: update
   .. automethod:: check_if_shiny
   .. automethod:: get_pokemon_name
   .. automethod:: is_in_battle
   .. automethod:: is_battle_over

State Transitions
-----------------

.. autoattribute:: pyshiny_hunter.hunter.Hunter.search_to_check_shiny
.. autoattribute:: pyshiny_hunter.hunter.Hunter.check_shiny_to_pre_battle
.. autoattribute:: pyshiny_hunter.hunter.Hunter.pre_battle_to_battle
.. autoattribute:: pyshiny_hunter.hunter.Hunter.battle_to_found
.. autoattribute:: pyshiny_hunter.hunter.Hunter.battle_to_search

Usage Example
-------------

.. code-block:: python

   from pyshiny_hunter.hunter import Hunter

   class MyGameHunter(Hunter):
       def check_if_shiny(self, frame: np.ndarray) -> bool:
           # Implement shiny detection logic
           pass

       def get_pokemon_name(self, frame: np.ndarray) -> str:
           # Implement OCR logic
           pass

       def is_in_battle(self, frame: np.ndarray) -> bool:
           # Implement battle detection
           pass

       def is_battle_over(self, frame: np.ndarray) -> bool:
           # Implement battle end detection
           pass
