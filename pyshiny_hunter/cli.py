"""Command-line interface for PyShiny Hunter.

This module provides the CLI entry point for automated shiny Pokemon hunting.
It parses command-line arguments and launches the hunter with the specified
ROM file and optional save files.

Example:
    $ pyshiny-hunter roms/pokemon_black2.nds
    $ pyshiny-hunter roms/pokemon_black2.nds --sav roms/saves/game.sav
    $ pyshiny-hunter roms/pokemon_black2.nds --randomize-start
"""

import argparse
import sys
from pathlib import Path


def main():
    """Main entry point for the pyshiny-hunter CLI.

    Parses command-line arguments and launches the shiny hunter with the
    DeSmuME emulator. Supports ROM files, save files, save states, and
    randomization options.

    Returns:
        int: Exit code from the hunter script (0 for success, non-zero for error).

    Raises:
        SystemExit: If argument parsing fails or hunter encounters an error.
    """
    parser = argparse.ArgumentParser(
        description="Automated shiny Pokemon hunting using Computer Vision",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "rom",
        type=Path,
        help="Path to the .nds ROM file",
    )

    parser.add_argument(
        "--sav",
        type=Path,
        help="Path to the .sav save file (optional)",
        default=None,
    )

    parser.add_argument(
        "--state",
        type=Path,
        help="Path to the .dst save state file (optional)",
        default=None,
    )

    parser.add_argument(
        "--randomize-start",
        action="store_true",
        help="Randomize starting position (optional)",
        default=False,
    )

    args = parser.parse_args()

    # Import here to avoid circular imports and speed up CLI
    from scripts.py_desmume_hunter import main as hunter_main

    # Call the actual hunter script
    sys.exit(hunter_main(args))


if __name__ == "__main__":
    main()
