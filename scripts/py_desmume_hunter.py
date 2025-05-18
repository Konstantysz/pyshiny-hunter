import argparse
import sys
from pathlib import Path
from typing import Optional

# Add the parent directory of pyshiny_hunter to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from pyshiny_hunter.black2_hunter import Black2Hunter
from pyshiny_hunter.py_desmume_manager import PyDeSmuMEManager


def emulator_worker(emulator: PyDeSmuMEManager):
    hunter = Black2Hunter()
    battle_ready_frame = -1
    battle_start_frame = -1

    while emulator.update_frame(hunter.get_encounters()):
        top_screen, bottom_screen = emulator.get_screens()

        if hunter.current_state.id == "search":
            hunter.searching_pokemon(top_screen, bottom_screen)

            if emulator.frame % 10 == 0:
                emulator.add_input_to_queue("key", key="KEY_LEFT")
            elif emulator.frame % 10 == 5:
                emulator.add_input_to_queue("key", key="KEY_RIGHT")
        elif hunter.current_state.id == "check_if_shiny":
            hunter.checking_shiny(top_screen, bottom_screen)
            if battle_start_frame == -1:
                battle_start_frame = emulator.get_frame_number()
        elif hunter.current_state.id == "pre_battle_animation":
            hunter.waiting_for_battle_start(top_screen, bottom_screen)
            if battle_ready_frame == -1:
                battle_ready_frame = emulator.get_frame_number()
        elif hunter.current_state.id == "in_battle":
            hunter.running_away(battle_ready_frame - battle_start_frame)
            if hunter.current_state.id == "found":
                print("SHINY POKEMON!!!!!!!!!!!!")
                emulator.emulator.savestate.save_file(
                    f"roms/states/black2/shiny_{battle_ready_frame - battle_start_frame}.dst"
                )
            else:
                emulator.add_input_to_queue("touch", x=128, y=180)


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
