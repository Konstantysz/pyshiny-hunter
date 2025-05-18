from abc import ABCMeta, abstractmethod
from typing import Dict, List, Optional

import numpy as np
from statemachine import State, StateMachine


class HunterMeta(type(StateMachine), ABCMeta):
    pass


class Hunter(StateMachine, metaclass=HunterMeta):
    encounters: Dict[str, int]

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

    def __init__(self, hunted_pokemon: Optional[List[str] | str] = None):
        self.encounters = dict()
        super().__init__()

    @abstractmethod
    def _found_pokemon(self, top_screen: np.ndarray, bottom_screen: np.ndarray) -> bool:
        pass

    @abstractmethod
    def _checked_shiny(self, top_screen: np.ndarray, bottom_screen: np.ndarray) -> bool:
        pass

    @abstractmethod
    def _battle_started(
        self, top_screen: np.ndarray, bottom_screen: np.ndarray
    ) -> bool:
        pass

    @abstractmethod
    def _is_pokemon_shiny(self, wild_pokemon_animation_length: int) -> bool:
        pass

    def get_encounters(self) -> Dict[str, int]:
        return self.encounters
