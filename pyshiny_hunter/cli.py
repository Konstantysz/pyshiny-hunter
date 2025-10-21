"""Command-line interface for PyShiny Hunter.

Entry point for running the shiny hunter from the command line.
Supports both single-emulator and multi-process modes.

Example:
    Single mode:
        $ pyshiny-hunter roms/black2.nds --state savestate.dst

    Multi-process mode:
        $ pyshiny-hunter roms/black2.nds --state savestate.dst --num-workers 4
"""

import argparse
import multiprocessing as mp
import sys
from pathlib import Path
from typing import Optional

from pyshiny_hunter.module_logger import logger


def main() -> None:
    """Main CLI entry point.

    Parses command-line arguments and launches either single-emulator mode
    or multi-process mode based on --num-workers argument.
    """
    # Fix Windows console encoding for emoji support
    if sys.platform == "win32":
        import os

        os.system("chcp 65001 > nul")  # nosec B605 B607 - Safe Windows console command
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="PyShiny Hunter - Automated shiny Pokemon hunting with DeSmuME",
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
    parser.add_argument(
        "--randomize-start",
        action="store_true",
        help="Randomize start frame (for increased shiny odds variation)",
    )
    parser.add_argument(
        "--num-workers",
        type=int,
        default=1,
        help="Number of worker processes (default: 1 = single mode, >1 = multi mode)",
    )

    args = parser.parse_args()

    rom_path = Path(args.rom)
    save_path: Optional[Path] = None
    if args.state:
        save_path = Path(args.state)
    elif args.sav:
        save_path = Path(args.sav)

    # Choose mode based on num_workers
    if args.num_workers > 1:
        logger.info(f"Launching multi-process mode with {args.num_workers} workers...")
        from pyshiny_hunter.worker_process import launch_multi_mode

        launch_multi_mode(rom_path, save_path, args.num_workers, args.randomize_start)
    else:
        logger.info("Launching single-emulator mode...")
        from pyshiny_hunter.single_mode import launch_single_mode

        launch_single_mode(rom_path, save_path, args.randomize_start)


if __name__ == "__main__":
    # Required for Windows multiprocessing
    mp.freeze_support()
    main()
