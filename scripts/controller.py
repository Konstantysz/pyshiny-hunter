import argparse
import os
import logging
from pathlib import Path
from typing import Optional

from desmume.emulator import DeSmuME

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main(rom_path: Path, save_path: Optional[Path] = None):
    if not os.path.exists(rom_path):
        logger.error(f"ROM file '{rom_path}' not found.")
        return

    emu = DeSmuME()
    emu.open(str(rom_path))

    if save_path:
        if os.path.exists(save_path):
            if save_path.suffix == ".sav":
                # Handle "SAV" files
                logger.error(f"NDS memory \".sav\" files are not yet handled.")
            elif save_path.suffix == ".dst":
                emu.savestate.load_file(str(save_path))
                logger.info(f"Loaded save file: {save_path}")
        else:
            logger.warning(f"Save file '{save_path}' not found. Starting a new game.")

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
    parser.add_argument("--state", type=str, default=None, help="Path to the .dst save state file (optional)")
    
    args = parser.parse_args()
    save = Path(args.state) if args.state else Path(args.sav) if args.sav else None  
    main(Path(args.rom), save)
