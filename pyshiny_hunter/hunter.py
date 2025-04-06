from abc import ABC, abstractmethod
from enum import Enum
import numpy as np
from typing import Dict, Optional, List, Set, Tuple


class HuntState(Enum):
    SEARCH = 0
    CHECK_SHINY = 1
    BATTLE_LOADING = 2
    BATTLE = 3
    RUN = 4
    FOUND = 5


class Hunter(ABC):
    hunt_state: HuntState
    encounters: Dict[str, int]
    hunted_pokemon: Optional[List[str]]
    pokemon_database: Set[Tuple[str, int]]

    def __init__(self, hunted_pokemon: Optional[List[str] | str] = None):
        super().__init__()
        
        self.hunt_state = HuntState.SEARCH
        self.encounters = {}
        
        if hunted_pokemon is not None:
            if isinstance(hunted_pokemon, str):
                self.hunted_pokemon = [hunted_pokemon]
            elif isinstance(hunted_pokemon, list):
                self.hunted_pokemon = hunted_pokemon
            else:
                raise ValueError("hunted_pokemon must be a string or a list of strings")
        else:
            self.hunted_pokemon = None
            
        pokemon_database = {}

    @abstractmethod
    def process_frame(
        self, top_screen: np.ndarray, bottom_screen: np.ndarray
    ) -> bool: ...
    
    def get_hunt_state(self) -> HuntState:
        return self.hunt_state
