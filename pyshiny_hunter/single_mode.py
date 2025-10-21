"""Single-emulator mode with integrated GUI.

This module implements the original single-emulator mode where
the GUI and emulator run in the same process.
"""

from pathlib import Path
from typing import Optional

from pyshiny_hunter.black2_hunter import Black2Hunter
from pyshiny_hunter.module_logger import logger
from pyshiny_hunter.py_desmume_manager import PyDeSmuMEManager


def single_mode_worker(manager: PyDeSmuMEManager):
    """Original single-emulator mode with integrated GUI.

    Args:
        manager: PyDeSmuMEManager instance with initialized emulator
    """
    num_emulators = len(manager.get_emulators())
    hunters = [Black2Hunter() for _ in range(num_emulators)]
    battle_ready_frame_list = [-1] * num_emulators
    battle_start_frame_list = [-1] * num_emulators

    while manager.update_frame(hunters[0].get_encounters()):
        emulators = manager.get_emulators()
        for emulator_id, emulator in enumerate(emulators):
            top_screen, bottom_screen = emulator.get_screens()
            hunter = hunters[emulator_id]
            battle_start_frame = battle_start_frame_list[emulator_id]
            battle_ready_frame = battle_ready_frame_list[emulator_id]

            if hunter.current_state.id == "search":
                hunter.searching_pokemon(top_screen, bottom_screen)

                if emulator.frame % 10 == 0:
                    manager.add_input_to_queue(emulator_id, "key", key="KEY_LEFT")
                elif emulator.frame % 10 == 5:
                    manager.add_input_to_queue(emulator_id, "key", key="KEY_RIGHT")
            elif hunter.current_state.id == "check_if_shiny":
                hunter.checking_shiny(top_screen, bottom_screen)
                if battle_start_frame == -1:
                    battle_start_frame_list[emulator_id] = emulator.frame
            elif hunter.current_state.id == "pre_battle_animation":
                hunter.waiting_for_battle_start(top_screen, bottom_screen)
                if battle_ready_frame == -1:
                    battle_ready_frame_list[emulator_id] = emulator.frame
            elif hunter.current_state.id == "in_battle":
                hunter.running_away(battle_ready_frame - battle_start_frame)
                if hunter.current_state.id == "found":
                    logger.info("🎉 SHINY POKEMON FOUND! 🎉")
                    emulator.emulator.savestate.save_file(
                        f"roms/states/black2/shiny_{battle_ready_frame - battle_start_frame}.dst"
                    )
                else:
                    manager.add_input_to_queue(emulator_id, "touch", x=128, y=180)

                # Reset when back to search
                if hunter.current_state.id == "search":
                    battle_start_frame_list[emulator_id] = -1
                    battle_ready_frame_list[emulator_id] = -1


def launch_single_mode(rom_path: Path, save_path: Optional[Path], randomize_start: bool):
    """Launch traditional single-emulator mode.

    Args:
        rom_path: Path to ROM file
        save_path: Path to save state file (optional)
        randomize_start: Whether to randomize starting frame
    """
    logger.info("=" * 60)
    logger.info("🎮 PyShiny Hunter - Single Mode")
    logger.info("=" * 60)
    logger.info(f"ROM: {rom_path}")
    logger.info(f"Save State: {save_path}")
    logger.info("=" * 60)

    manager = PyDeSmuMEManager(rom_path, save_path, randomize_start)
    single_mode_worker(manager)
