import argparse
import sys
from pathlib import Path
from typing import Optional

# Add the parent directory of pyshiny_hunter to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from pyshiny_hunter.black2_hunter import Black2Hunter
from pyshiny_hunter.py_desmume_manager import PyDeSmuMEManager


def emulator_worker(manager: PyDeSmuMEManager):
    hunters = [Black2Hunter(), Black2Hunter()]
    battle_ready_frame_list = [-1, -1]
    battle_start_frame_list = [-1, -1]

    while manager.update_frame(hunters[0].get_encounters()):
        emulators = manager.get_emulators()
        for emulator_id, emulator in enumerate(emulators):
            top_screen, bottom_screen = emulator.get_screens()

            if hunters[emulator_id].current_state.id == "search":
                hunters[emulator_id].searching_pokemon(top_screen, bottom_screen)

                if manager.frame % 10 == 0:
                    manager.add_input_to_queue(emulator_id, "key", key="KEY_LEFT")
                elif manager.frame % 10 == 5:
                    manager.add_input_to_queue(emulator_id, "key", key="KEY_RIGHT")
            elif hunters[emulator_id].current_state.id == "check_if_shiny":
                hunters[emulator_id].checking_shiny(top_screen, bottom_screen)
                if battle_start_frame_list[emulator_id] == -1:
                    battle_start_frame_list[emulator_id] = manager.get_frame_number()
            elif hunters[emulator_id].current_state.id == "pre_battle_animation":
                hunters[emulator_id].waiting_for_battle_start(top_screen, bottom_screen)
                if battle_ready_frame_list[emulator_id] == -1:
                    battle_ready_frame_list[emulator_id] = manager.get_frame_number()
            elif hunters[emulator_id].current_state.id == "in_battle":
                hunters[emulator_id].running_away(
                    battle_ready_frame_list[emulator_id]
                    - battle_start_frame_list[emulator_id]
                )
                if hunters[emulator_id].current_state.id == "found":
                    print("SHINY POKEMON!!!!!!!!!!!!")
                    manager.emulator.savestate.save_file(
                        f"roms/states/black2/shiny_{battle_ready_frame_list[emulator_id] - battle_start_frame_list[emulator_id]}.dst"
                    )
                else:
                    manager.add_input_to_queue(emulator_id, "touch", x=128, y=180)


def main(rom_path: Path, save_path: Optional[Path] = None):
    emulator = PyDeSmuMEManager(rom_path, save_path)
    emulator_worker(emulator)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run DeSmuME emulator with video streaming and custom input handling."
    )
    parser.add_argument("rom", type=str, help="Path to the .nds ROM file")
    parser.add_argument(
        "--sav", type=str, default=None, help="Path to the .sav save file (optional)"
    )
    parser.add_argument(
        "--state",
        type=str,
        default=None,
        help="Path to the .dst save state file (optional)",
    )

    args = parser.parse_args()
    save = Path(args.state) if args.state else Path(args.sav) if args.sav else None
    main(Path(args.rom), save)
