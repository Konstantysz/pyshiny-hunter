import argparse
import sys

from pathlib import Path
from typing import Optional

# Add the parent directory of pyshiny_hunter to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from pyshiny_hunter.hunter import Hunter

def main(rom_path: Path, save_path: Optional[Path] = None):
    hunter = Hunter(rom_path, save_path)
    hunter.run()
    
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
