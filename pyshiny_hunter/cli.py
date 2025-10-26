"""Command-line interface for PyShiny Hunter.

Entry point for running the shiny hunter from the command line.
Supports both single-emulator and multi-process modes.

Multi-worker mode automatically applies RNG desynchronization to ensure
each worker has unique encounter sequences (prevents deterministic RNG issues).

Example:
    Single mode:
        $ pyshiny-hunter roms/black2.nds --state savestate.dst

    Multi-process mode (auto RNG desync):
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
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

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
        "--num-workers",
        type=int,
        default=1,
        help="Number of worker processes (default: 1 = single mode, >1 = multi mode with auto RNG desync)",
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
        logger.info("RNG desynchronization: ENABLED (always on for multi-worker mode)")
        from pyshiny_hunter.worker_process import launch_multi_mode

        # Multi-worker mode ALWAYS uses RNG desync to prevent identical encounters
        # DeSmuME has deterministic RNG - without desync, all workers see identical Pokemon
        MULTI_WORKER_RNG_DESYNC = True
        launch_multi_mode(
            rom_path, save_path, args.num_workers, randomize_start=MULTI_WORKER_RNG_DESYNC
        )
    else:
        logger.info("Launching single-emulator mode...")
        from pyshiny_hunter.single_mode import launch_single_mode

        # Single mode doesn't need desync (only one emulator)
        launch_single_mode(rom_path, save_path, randomize_start=False)


if __name__ == "__main__":
    # Required for Windows multiprocessing
    mp.freeze_support()
    main()
