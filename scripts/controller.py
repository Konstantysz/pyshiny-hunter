import argparse
import os

from desmume.emulator import DeSmuME
from pathlib import Path
from typing import Optional

def main(rom_path: Path, sav_path: Optional[Path] = None):
    if not os.path.exists(rom_path):
        print(f"Error: ROM file '{rom_path}' not found.")
        return

    emu = DeSmuME()
    emu.open(str(rom_path))

    if sav_path:
        if os.path.exists(sav_path):
            emu.savestate.load_file(sav_path)
            print(f"Loaded save file: {sav_path}")
        else:
            print(f"Warning: Save file '{sav_path}' not found. Starting a new game.")

    window = emu.create_sdl_window()

    while not window.has_quit():
        window.process_input()
        emu.cycle()
        window.draw()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run DeSmuME emulator with video streaming and custom input handling."
    )
    parser.add_argument("rom", type=str, help="Path to the .nds ROM file")
    parser.add_argument("--sav", type=str, default=None, help="Path to the .sav save file (optional)")
    
    args = parser.parse_args()
    main(args.rom, args.sav)
