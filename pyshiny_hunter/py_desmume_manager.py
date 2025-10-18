import os
import random
from pathlib import Path
from queue import Queue
from typing import Dict, List, Optional, Tuple

import glfw
import imgui
import numpy as np
import OpenGL.GL as gl
from desmume.controls import Keys, keymask
from desmume.emulator import DeSmuME, DeSmuME_SDL_Window
from imgui.integrations.glfw import GlfwRenderer

from pyshiny_hunter import config
from pyshiny_hunter.module_logger import logger
from pyshiny_hunter.utils.gui_utils import (
    glfw_init,
    opengl_create_texture,
    opengl_update_texture,
)


class DeSmuMEWrapper:
    def __init__(self, rom_path: Path, save_path: Optional[Path] = None):
        self.emulator = DeSmuME()
        self.emulator.open(str(rom_path))
        self.emulator.volume_set(0)

        if save_path:
            self.__load_save(save_path)

    def step(self):
        # Obsługa wejść i przejście do następnej klatki
        pass

    def take_screenshot(self) -> np.ndarray:
        return np.array(self.emulator.screenshot().convert("RGBA"))

    def get_screens(self) -> Tuple[np.ndarray, np.ndarray]:
        screen = self.take_screenshot()[:, :, ::-1].copy()
        top_screen = screen[: int(screen.shape[0] / 2), :, 1:]
        bottom_screen = screen[int(screen.shape[0] / 2) :, :, 1:]
        return (top_screen, bottom_screen)

    def __load_save(self, save_path: Path) -> None:
        if os.path.exists(save_path):
            if save_path.suffix == ".sav":
                logger.error('NDS memory ".sav" files are not yet handled.')
            elif save_path.suffix == ".dst":
                self.emulator.savestate.load_file(str(save_path))
                logger.info(f"Loaded save file: {save_path}")
        else:
            logger.warning(f"Save file '{save_path}' not found. Starting a new game.")


class PyDeSmuMEManager:
    emulators: List[DeSmuMEWrapper]
    window: DeSmuME_SDL_Window
    frame: int
    input_queue: Queue
    renderer: GlfwRenderer
    texture_ids: List[int]

    def __init__(
        self,
        rom_path: Path,
        save_path: Optional[Path] = None,
        randomize_start: bool = False,
    ):
        assert os.path.exists(rom_path), f"ROM file '{rom_path}' not found."
        assert rom_path.suffix == ".nds", f"ROM file '{rom_path}' has not supported file type."

        self.emulator = DeSmuME()
        self.emulator.open(str(rom_path))
        self.emulator.volume_set(0)

        if save_path:
            self.__load_save(save_path)

        if randomize_start:
            random_frame = random.randrange(
                0, config.SHINY_ODDS_DENOMINATOR
            )  # nosec B311 - Not used for security
            for _ in range(random_frame):
                self.emulator.cycle()
            print(f"Randomized start frame: {random_frame}")

        self.frame = 0
        self.input_queue = Queue()

        imgui.create_context()
        self.window = glfw_init("PyShinyHunter", 300, 700)
        self.renderer = GlfwRenderer(self.window)
        self.texture_ids = [
            opengl_create_texture(256, 384),
            # opengl_create_texture(256, 384),
        ]

    def __del__(self):
        self.renderer.shutdown()
        glfw.terminate()

    def update_frame(self, encounters: Dict[str, int]) -> bool:
        if glfw.window_should_close(self.window):
            return False

        glfw.poll_events()
        self.renderer.process_inputs()
        imgui.new_frame()

        gl.glClearColor(0.1, 0.1, 0.1, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        for texture_id in self.texture_ids:
            with imgui.begin("DeSmuME"):
                imgui.image(texture_id, 256, 384)

        with imgui.begin("Encounter Info"):
            imgui.text(f"FPS: {1 / imgui.get_io().delta_time:.2f}")
            imgui.separator()
            imgui.text(f"Encounters: {sum([encounters[key] for key in encounters])}")
            shiny_odds = 1.0 / config.SHINY_ODDS_DENOMINATOR
            imgui.text(f"Shiny odds: {shiny_odds * 100.0:.3f}%")
            imgui.text(
                f"At least one shiny probability: {(1 - (1 - shiny_odds) ** len(encounters.items())):.3f}%"
            )
            imgui.separator()
            for encounter, count in encounters.items():
                imgui.text(f"{encounter}: {count}")

        self.__emulators_process_inputs()
        self.__emulators_next_frame()

        opengl_update_texture(self.emulators[0].take_screenshot(), self.texture_ids[0])
        # opengl_update_texture(self.emulators[1].take_screenshot(), self.texture_ids[1])

        imgui.render()
        self.renderer.render(imgui.get_draw_data())
        glfw.swap_buffers(self.window)

        return True

    def get_emulators(self) -> List[DeSmuMEWrapper]:
        return self.emulators

    def get_screens(self) -> Tuple[np.ndarray, np.ndarray]:
        return self.emulators[0].get_screens()

    def get_frame_number(self) -> int:
        return self.frame

    def add_input_to_queue(self, emulator_id: int, action_type: str, **kwargs):
        self.input_queue.put({"emulator_id": emulator_id, "type": action_type, "params": kwargs})

    def __emulators_process_inputs(self):
        for emulator in self.emulators:
            emulator.emulator.input.keypad_rm_key(Keys.KEY_NONE)
            emulator.emulator.input.touch_release()

        while not self.input_queue.empty():
            action = self.input_queue.get()
            emulator_id = action["emulator_id"]
            action_type = action["type"]
            params = action["params"]

            if action_type == "key":
                key = params.get("key")
                if key:
                    self.emulators[emulator_id].emulator.input.keypad_add_key(
                        keymask(getattr(Keys, key))
                    )
            elif action_type == "touch":
                x = params.get("x")
                y = params.get("y")
                if x is not None and y is not None:
                    self.emulators[emulator_id].emulator.input.touch_set_pos(x, y)
            elif action_type == "release_touch":
                self.emulators[emulator_id].emulator.input.touch_release()

    def __emulators_next_frame(self):
        for emulator in self.emulators:
            emulator.emulator.cycle()
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
