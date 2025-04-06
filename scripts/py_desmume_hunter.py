import argparse
import sys
from pathlib import Path
from typing import Optional

# Add the parent directory of pyshiny_hunter to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from pyshiny_hunter.black2_hunter import Black2Hunter
from pyshiny_hunter.hunter import HuntState
from pyshiny_hunter.py_desmume_manager import PyDeSmuMEManager


def main(rom_path: Path, save_path: Optional[Path] = None):
    emulator = PyDeSmuMEManager(rom_path, save_path)

    hunter = Black2Hunter()

    while emulator.update_frame(hunter.get_encounters()):
        top_screen, bottom_screen = emulator.get_screens()
        hunter.process_frame(top_screen, bottom_screen, emulator.get_frame_number())

        hunt_state = hunter.get_hunt_state()

        if hunt_state == HuntState.SEARCH:
            if emulator.frame % 10 == 0:
                emulator.add_input_to_queue("key", key="KEY_LEFT")
            elif emulator.frame % 10 == 5:
                emulator.add_input_to_queue("key", key="KEY_RIGHT")
        elif hunt_state == HuntState.BATTLE:
            SHINY_FRAME_COUNT: int = 500
            if (
                hunter.battle_ready_frame - hunter.battle_start_frame
                > SHINY_FRAME_COUNT
            ):
                print("SHINY POKEMON!!!!!!!!!!!!")
                emulator.emulator.savestate.save_file(
                    f"roms/states/black2/shiny_{SHINY_FRAME_COUNT}.dst"
                )
                hunter.hunt_state = HuntState.FOUND
            else:
                emulator.add_input_to_queue("touch", x=128, y=180)
                hunter.hunt_state = HuntState.SEARCH

                print("Encounters:")
                for encounter_name, encounter_count in hunter.encounters.items():
                    print(f"{encounter_name}: {encounter_count}")


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
