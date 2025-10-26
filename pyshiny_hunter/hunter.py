from __future__ import annotations

from abc import ABCMeta, abstractmethod

import numpy as np
from statemachine import State, StateMachine


class HunterMeta(type(StateMachine), ABCMeta):  # type: ignore[misc]
    """Metaclass combining StateMachine and ABC for multiple inheritance."""

    pass


class Hunter(StateMachine, metaclass=HunterMeta):  # type: ignore[misc,metaclass]
    """Abstract base class for automated shiny Pokemon hunting using state machines.

    This class defines a 5-state finite state machine for shiny hunting automation:
    1. Search - Looking for wild Pokemon encounters
    2. Check Shiny - Analyzing if encountered Pokemon is shiny
    3. Pre-Battle - Waiting for battle to start
    4. Battle - In battle (run if not shiny, stop if shiny)
    5. Found - Shiny Pokemon found (final state)

    State transitions are driven by Computer Vision condition methods that
    subclasses must implement for game-specific detection logic.

    Attributes:
        encounters: Dictionary tracking encounter counts by Pokemon name.
        current_state: Current state machine state (inherited from StateMachine).

    States:
        search: Initial state, searching for wild Pokemon.
        check_if_shiny: Checking if the encountered Pokemon is shiny.
        pre_battle_animation: Waiting for battle to start.
        in_battle: Battle started, deciding to run or stay.
        found: Final state, shiny Pokemon found.

    Transitions:
        searching_pokemon: search → check_if_shiny (when Pokemon found)
        checking_shiny: check_if_shiny → pre_battle_animation (if sparkles detected)
        waiting_for_battle_start: pre_battle_animation → in_battle (when battle starts)
        running_away: in_battle → found (if shiny) or in_battle → search (if not shiny)

    Example:
        >>> class MyGameHunter(Hunter):
        ...     def _found_pokemon(self, top, bottom): return detect_encounter(top, bottom)
        ...     def _checked_shiny(self, top, bottom): return detect_sparkles(top, bottom)
        ...     def _battle_started(self, top, bottom): return detect_battle_ui(bottom)
        ...     def _is_pokemon_shiny(self, frames): return frames > 500
        >>> hunter = MyGameHunter()
        >>> hunter.send("searching_pokemon", top_screen, bottom_screen)
    """

    encounters: dict[str, int]

    search = State("Searching for shiny Pokemon...", initial=True)
    check_if_shiny = State("Checking if Pokemon is shiny")
    pre_battle_animation = State("Pre-battle animation")
    in_battle = State("In battle")
    found = State("Found shiny Pokemon", final=True)

    searching_pokemon = search.to(check_if_shiny, cond="_found_pokemon") | search.to(
        search, unless="_found_pokemon"
    )
    checking_shiny = check_if_shiny.to(
        pre_battle_animation, cond="_checked_shiny"
    ) | check_if_shiny.to(check_if_shiny, unless="_checked_shiny")
    waiting_for_battle_start = pre_battle_animation.to(
        in_battle, cond="_battle_started"
    ) | pre_battle_animation.to(pre_battle_animation, unless="_battle_started")
    running_away = in_battle.to(found, cond="_is_pokemon_shiny") | in_battle.to(
        search, unless="_is_pokemon_shiny"
    )

    def __init__(self, hunted_pokemon: list[str] | str | None = None):
        """Initialize Hunter with empty encounter tracker.

        Args:
            hunted_pokemon: Optional Pokemon name(s) to hunt for. Reserved for
                future use (currently unused). Can be a single string or list.
        """
        self.encounters = {}
        super().__init__()

    @abstractmethod
    def _found_pokemon(self, top_screen: np.ndarray, bottom_screen: np.ndarray) -> bool:
        """Detect if a wild Pokemon encounter has occurred.

        This method is called during the "search" state to determine if a wild
        Pokemon has appeared. Implement game-specific detection logic (e.g.,
        screen flash, pixel analysis).

        Args:
            top_screen: Top game screen as BGR numpy array.
            bottom_screen: Bottom game screen as BGR numpy array.

        Returns:
            True if wild Pokemon found, False otherwise.
        """
        pass

    @abstractmethod
    def _checked_shiny(self, top_screen: np.ndarray, bottom_screen: np.ndarray) -> bool:
        """Detect if shiny animation/sparkles are visible.

        This method is called during the "check_if_shiny" state to determine if
        the encountered Pokemon is shiny. Implement sparkle/animation detection
        (e.g., bright pixel analysis).

        Args:
            top_screen: Top game screen as BGR numpy array.
            bottom_screen: Bottom game screen as BGR numpy array.

        Returns:
            True if shiny sparkles detected, False otherwise.
        """
        pass

    @abstractmethod
    def _battle_started(self, top_screen: np.ndarray, bottom_screen: np.ndarray) -> bool:
        """Detect if the battle has started.

        This method is called during the "pre_battle_animation" state to determine
        when the battle UI appears. Implement UI detection logic.

        Args:
            top_screen: Top game screen as BGR numpy array.
            bottom_screen: Bottom game screen as BGR numpy array.

        Returns:
            True if battle started, False otherwise.
        """
        pass

    @abstractmethod
    def _is_pokemon_shiny(self, wild_pokemon_animation_length: int) -> bool:
        """Determine if Pokemon is shiny based on animation length.

        This method is called during the "in_battle" state to make the final
        shiny determination. Implement animation frame counting or other
        temporal analysis.

        Args:
            wild_pokemon_animation_length: Number of frames counted during
                Pokemon entrance animation.

        Returns:
            True if Pokemon is shiny, False otherwise.
        """
        pass

    def get_encounters(self) -> dict[str, int]:
        """Get dictionary of encountered Pokemon and their counts.

        Returns:
            Dictionary mapping Pokemon names to encounter counts.
        """
        return self.encounters
