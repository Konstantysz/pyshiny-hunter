import cv2 as cv
import numpy as np
import pytesseract

from pyshiny_hunter.hunter import Hunter, HuntState
from pyshiny_hunter.module_logger import logger


POKEBALL_LIGHT_PIXEL_THRESHOLD: int = 230
WHITE_SCREEN_AVERAGE_PIXEL_VALUE: int = 247
POKEBALL_RELEASE_AVERAGE_PIXEL_VALUE: int = 30
BATTLE_BOTTOM_SCREEN_AVERAGE_PIXEL_VALUE: int = 55


class Black2Hunter(Hunter):
    def __init__(self):
        Hunter.__init__(self)

    def process_frame(
        self, top_screen: np.ndarray, bottom_screen: np.ndarray, frame: int
    ) -> bool:
        bottom_screen_pixel_average = int(np.sum(bottom_screen) / bottom_screen.size)

        if (
            self.hunt_state == HuntState.SEARCH
            and bottom_screen_pixel_average > WHITE_SCREEN_AVERAGE_PIXEL_VALUE
        ):
            self.hunt_state = HuntState.CHECK_SHINY
            self.battle_start_frame = frame
            return

        if (
            self.hunt_state == HuntState.CHECK_SHINY
            and bottom_screen_pixel_average < POKEBALL_RELEASE_AVERAGE_PIXEL_VALUE
            and self.__is_pokemon_released(top_screen)
        ):
            self.hunt_state = HuntState.BATTLE_LOADING
            self.__determine_encounter(top_screen)
            self.battle_ready_frame = frame
            return

        if (
            self.hunt_state == HuntState.BATTLE_LOADING
            and bottom_screen_pixel_average > BATTLE_BOTTOM_SCREEN_AVERAGE_PIXEL_VALUE
        ):
            self.hunt_state = HuntState.BATTLE
            return

    def __is_pokemon_released(self, top_screen: np.ndarray) -> bool:
        AVERAGE_PIXEL_THRESHOLD = 20.0
        screen_height, screen_width, _ = top_screen.shape
        pixels_above_threshold = (
            np.sum(
                top_screen[
                    0 : int(2 * screen_height / 3),
                    int(screen_width / 3) : int(2 * screen_width / 3),
                ]
                > POKEBALL_LIGHT_PIXEL_THRESHOLD
            )
            / (top_screen.size / 3)
            * 100.0
        )

        return pixels_above_threshold > AVERAGE_PIXEL_THRESHOLD

    def __determine_encounter(self, top_screen: np.ndarray) -> str:
        encounter_name = pytesseract.image_to_string(
            cv.resize(top_screen[30:40, 10:75], (0, 0), fx=3.0, fy=3.0)
        ).replace("\n", "")

        if encounter_name in self.encounters.keys():
            self.encounters[encounter_name] += 1
        else:
            self.encounters[encounter_name] = 1
