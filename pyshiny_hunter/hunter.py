import cv2 as cv
import numpy as np
import os

from desmume.emulator import DeSmuME, DeSmuME_SDL_Window
from desmume.controls import keymask, Keys
from enum import Enum
from pathlib import Path
from typing import Optional

from pyshiny_hunter.module_logger import logger


class EncounterType(Enum):
    GRASS = 0
    STATIC = 1


class HuntState(Enum):
    SEARCH = 0
    CHECK_SHINY = 1
    BATTLE_LOADING = 2
    BATTLE = 3
    RUN = 4
    FOUND = 5


class Hunter:
    emulator: DeSmuME
    window: DeSmuME_SDL_Window
    frame: int
    encounter_count: int
    hunt_state: HuntState
    battle_start_frame: int
    battle_ready_frame: int

    def __init__(self, rom_path: Path, save_path: Optional[Path] = None):
        assert (os.path.exists(rom_path), f"ROM file '{rom_path}' not found.")
        assert (
            rom_path.suffix == ".nds",
            f"ROM file '{rom_path}' has not supported file type.",
        )

        self.emulator = DeSmuME()
        self.emulator.open(str(rom_path))

        if save_path:
            self.__load_save(save_path)

        self.window = self.emulator.create_sdl_window()
        self.frame = 0
        self.encounter_count = 0
        self.hunt_state = HuntState.SEARCH

        self.battle_start_frame = -1
        self.battle_ready_frame = -1

    def run(self) -> None:
        while not self.window.has_quit():
            self.__pre_frame()

            if self.frame % 10 == 0:
                self.__process_screen_frame()

            if self.hunt_state == HuntState.SEARCH:
                self.__search_grass_pokemon()
            elif self.hunt_state == HuntState.BATTLE:
                SHINY_FRAME_COUNT: int = 500
                if (
                    self.battle_ready_frame - self.battle_start_frame
                    > SHINY_FRAME_COUNT
                ):
                    logger.info("SHINY POKEMON!!!!!!!!!!!!")
                    self.emulator.savestate.save_file(
                        f"roms/states/black2/shiny_{SHINY_FRAME_COUNT}.dst"
                    )
                    self.hunt_state = HuntState.FOUND
                else:
                    self.emulator.input.touch_set_pos(128, 180)
                    self.hunt_state = HuntState.SEARCH
                    self.encounter_count += 1
                    logger.info(f"Encounter count: {self.encounter_count}")

            self.__draw_frame()

    def __process_screen_frame(self):
        top_screen, bottom_screen = self.__extract_screens()

        bottom_screen_average_pixel_value = int(
            np.sum(bottom_screen) / bottom_screen.size
        )

        POKEBALL_LIGHT_PIXEL_THRESHOLD: int = 230
        _, screen_width, _ = top_screen.shape
        pixels_above_threshold = (
            np.sum(
                top_screen[:, int(screen_width / 3) : int(2 * screen_width / 3)]
                > POKEBALL_LIGHT_PIXEL_THRESHOLD
            )
            / (top_screen.size / 3)
            * 100.0
        )

        WHITE_SCREEN_AVERAGE_PIXEL_VALUE: int = 247
        if (
            self.hunt_state == HuntState.SEARCH
            and bottom_screen_average_pixel_value > WHITE_SCREEN_AVERAGE_PIXEL_VALUE
        ):
            self.hunt_state = HuntState.CHECK_SHINY
            self.battle_start_frame = self.frame
            return

        POKEBALL_RELEASE_AVERAGE_PIXEL_VALUE: int = 30
        if (
            self.hunt_state == HuntState.CHECK_SHINY
            and bottom_screen_average_pixel_value < POKEBALL_RELEASE_AVERAGE_PIXEL_VALUE
            and pixels_above_threshold > 5.0
        ):
            self.hunt_state = HuntState.BATTLE_LOADING
            self.battle_ready_frame = self.frame
            return

        BATTLE_BOTTOM_SCREEN_AVERAGE_PIXEL_VALUE: int = 55
        if (
            self.hunt_state == HuntState.BATTLE_LOADING
            and bottom_screen_average_pixel_value
            > BATTLE_BOTTOM_SCREEN_AVERAGE_PIXEL_VALUE
        ):
            self.hunt_state = HuntState.BATTLE
            return

    def __extract_screens(self):
        screenshot = self.emulator.screenshot().convert("RGB")
        screen = np.array(screenshot)[:, :, ::-1].copy()
        top_screen = screen[: int(screen.shape[0] / 2)]
        bottom_screen = screen[int(screen.shape[0] / 2) :]
        return (top_screen, bottom_screen)

    def __draw_frame(self):
        self.emulator.cycle()
        self.window.draw()
        self.frame += 1

    def __pre_frame(self):
        self.window.process_input()
        self.emulator.input.keypad_rm_key(Keys.KEY_NONE)
        self.emulator.input.touch_release()

    def __search_grass_pokemon(self):
        if self.frame % 4 == 1:
            self.emulator.input.keypad_add_key(keymask(Keys.KEY_LEFT))
        if self.frame % 4 == 3:
            self.emulator.input.keypad_add_key(keymask(Keys.KEY_RIGHT))

    def __load_save(self, save_path: Path) -> None:
        if os.path.exists(save_path):
            if save_path.suffix == ".sav":
                # Handle "SAV" files
                logger.error(f'NDS memory ".sav" files are not yet handled.')
            elif save_path.suffix == ".dst":
                self.emulator.savestate.load_file(str(save_path))
                logger.info(f"Loaded save file: {save_path}")
        else:
            logger.warning(f"Save file '{save_path}' not found. Starting a new game.")
