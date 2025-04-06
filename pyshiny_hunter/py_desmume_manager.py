import os
from pathlib import Path
from queue import Queue
from typing import Optional, Tuple

import numpy as np
from desmume.controls import Keys, keymask
from desmume.emulator import DeSmuME, DeSmuME_SDL_Window

from pyshiny_hunter.module_logger import logger


class PyDeSmuMEManager:
    emulator: DeSmuME
    window: DeSmuME_SDL_Window
    frame: int
    input_queue: Queue

    def __init__(self, rom_path: Path, save_path: Optional[Path] = None):
        assert (os.path.exists(rom_path), f"ROM file '{rom_path}' not found.")
        assert (
            rom_path.suffix == ".nds",
            f"ROM file '{rom_path}' has not supported file type.",
        )

        self.emulator = DeSmuME()
        self.emulator.open(str(rom_path))
        self.emulator.volume_set(0)

        if save_path:
            self.__load_save(save_path)

        self.window = self.emulator.create_sdl_window()
        self.frame = 0
        self.input_queue = Queue()

    def update_frame(self) -> bool:
        if self.window.has_quit():
            return False

        self.__process_inputs()

        self.__draw_frame()

        return True

    def get_screens(self) -> Tuple[np.ndarray, np.ndarray]:
        screenshot = self.emulator.screenshot().convert("RGB")
        screen = np.array(screenshot)[:, :, ::-1].copy()
        top_screen = screen[: int(screen.shape[0] / 2)]
        bottom_screen = screen[int(screen.shape[0] / 2) :]
        return (top_screen, bottom_screen)

    def get_frame_number(self) -> int:
        return self.frame

    def add_input_to_queue(self, action_type: str, **kwargs):
        self.input_queue.put({"type": action_type, "params": kwargs})

    def __process_inputs(self):
        self.emulator.input.keypad_rm_key(Keys.KEY_NONE)
        self.emulator.input.touch_release()

        while not self.input_queue.empty():
            action = self.input_queue.get()
            action_type = action["type"]
            params = action["params"]

            if action_type == "key":
                key = params.get("key")
                if key:
                    self.emulator.input.keypad_add_key(keymask(getattr(Keys, key)))
            elif action_type == "touch":
                x = params.get("x")
                y = params.get("y")
                if x is not None and y is not None:
                    self.emulator.input.touch_set_pos(x, y)
            elif action_type == "release_touch":
                self.emulator.input.touch_release()

    def __draw_frame(self):
        self.emulator.cycle()
        self.window.draw()
        self.frame += 1

    def __load_save(self, save_path: Path) -> None:
        if os.path.exists(save_path):
            if save_path.suffix == ".sav":
                logger.error('NDS memory ".sav" files are not yet handled.')
            elif save_path.suffix == ".dst":
                self.emulator.savestate.load_file(str(save_path))
                logger.info(f"Loaded save file: {save_path}")
        else:
            logger.warning(f"Save file '{save_path}' not found. Starting a new game.")
            logger.warning(f"Save file '{save_path}' not found. Starting a new game.")
