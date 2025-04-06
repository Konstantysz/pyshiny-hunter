import re
from difflib import get_close_matches
from typing import List, Optional

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
    def __init__(self, hunted_pokemon: Optional[List[str] | str] = None):
        Hunter.__init__(self, hunted_pokemon)

        self.pokemon_database = dict()
        for gen_file in ["gen1.csv", "gen2.csv", "gen3.csv", "gen4.csv", "gen5.csv"]:
            try:
                with open(f"resources/pokemon_names/{gen_file}", "r") as file:
                    next(file)  # Skip the first line of the file as it is header.
                    self.pokemon_database.update(
                        (
                            (
                                line.split(",")[1].strip(),
                                int(line.split(",")[0].strip()),
                            )
                            if len(line.split(",")) > 1
                            else None
                        )
                        for line in file
                        if line.strip()
                        and "," in line
                        and not line.startswith("number")
                    )
            except FileNotFoundError:
                logger.warning(f"File {gen_file} not found. Skipping.")

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
        cropped_region = top_screen[30:40, 10:75]
        resized_region = cv.resize(cropped_region, (0, 0), fx=3.0, fy=3.0)
        gray_region = cv.cvtColor(resized_region, cv.COLOR_BGR2GRAY)
        _, thresholded_region = cv.threshold(gray_region, 127, 255, cv.THRESH_BINARY)
        tesseract_config = "--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-."
        raw_name = pytesseract.image_to_string(
            thresholded_region, config=tesseract_config
        ).strip()

        formatted_name = re.sub(
            r"(?<!^)(?<![-. ])[A-Z]",  # Matches uppercase letters not preceded by start, "-", ".", or space
            lambda match: match.group(0).lower(),  # Convert to lowercase
            raw_name,
        )

        encounter_name = re.sub(
            r"(?:^|[-. ])[a-z]",  # Matches lowercase letters at the start or after "-", ".", or space
            lambda match: match.group(0).upper(),  # Convert to uppercase
            formatted_name,
        )

        if encounter_name in self.pokemon_database:
            if encounter_name in self.encounters.keys():
                self.encounters[encounter_name] += 1
            else:
                self.encounters[encounter_name] = 1
            return encounter_name

        probable_matches = get_close_matches(
            encounter_name, self.pokemon_database, n=1, cutoff=0.6
        )
        if probable_matches:
            corrected_name = probable_matches[0]
            if corrected_name in self.encounters.keys():
                self.encounters[corrected_name] += 1
            else:
                self.encounters[corrected_name] = 1
            return corrected_name

        logger.warning(
            f"Encounter name '{encounter_name}' not recognized and no close match found."
        )

        if encounter_name in self.encounters.keys():
            self.encounters[encounter_name] += 1
        else:
            self.encounters[encounter_name] = 1

        return encounter_name
        return encounter_name
