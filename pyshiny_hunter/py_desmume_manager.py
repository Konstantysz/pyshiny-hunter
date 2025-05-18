import os
from pathlib import Path
from queue import Queue
from typing import Dict, Optional, Tuple

import glfw
import imgui
import numpy as np
import OpenGL.GL as gl
from desmume.controls import Keys, keymask
from desmume.emulator import DeSmuME, DeSmuME_SDL_Window
from imgui.integrations.glfw import GlfwRenderer

from pyshiny_hunter.module_logger import logger
from pyshiny_hunter.utils.gui_utils import (
    glfw_init,
    opengl_create_texture,
    opengl_update_texture,
)


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

        self.frame = 0
        self.input_queue = Queue()

        imgui.create_context()
        self.window = glfw_init("PyShinyHunter")
        self.renderer = GlfwRenderer(self.window)
        self.texture_id = opengl_create_texture(256, 384)

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

        with imgui.begin("DeSmuME"):
            imgui.image(self.texture_id, 256, 384)  # Adjust size as needed

        with imgui.begin("Encounter Info"):
            imgui.separator()
            for encounter, count in encounters.items():
                imgui.text(f"{encounter}: {count}")

        self.__emulator_process_inputs()
        self.__emulator_next_frame()

        opengl_update_texture(
            np.array(self.emulator.screenshot().convert("RGBA")), self.texture_id
        )

        imgui.render()
        self.renderer.render(imgui.get_draw_data())
        glfw.swap_buffers(self.window)

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

    def __emulator_process_inputs(self):
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

    def __emulator_next_frame(self):
        self.emulator.cycle()
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
