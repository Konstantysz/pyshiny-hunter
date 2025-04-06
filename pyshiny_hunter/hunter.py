from abc import ABC, abstractmethod
from enum import Enum
import numpy as np
from typing import Dict


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

    def __init__(self):
        super().__init__()
        
        self.hunt_state = HuntState.SEARCH
        self.encounters = {}

    @abstractmethod
    def process_frame(
        self, top_screen: np.ndarray, bottom_screen: np.ndarray
    ) -> bool: ...
    
    def get_hunt_state(self) -> HuntState:
        return self.hunt_state
