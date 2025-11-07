"""Module for logging skipped shiny Pokemon encounters.

This module provides functionality to track shiny Pokemon that were found but
skipped because they didn't match the target Pokemon. This ensures no shiny
is ever lost and provides a recovery mechanism.

Philosophy: "Shiny = 1/8192 - better safe than sorry"
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pyshiny_hunter.module_logger import logger


class SkippedShinyLogger:
    """Logger for skipped shiny Pokemon encounters.

    Maintains a separate log file (skipped_shinies.json) for all shinies that
    were found but not the target Pokemon. Each entry includes full metadata
    for recovery purposes.

    Attributes:
        log_file: Path to the skipped shinies log file.
        entries: List of skipped shiny entries loaded from disk.
    """

    def __init__(self, log_file: str = "skipped_shinies.json"):
        """Initialize the skipped shiny logger.

        Args:
            log_file: Path to the log file (default: skipped_shinies.json).
        """
        self.log_file = Path(log_file)
        self.entries: list[dict[str, Any]] = []
        self._load_existing_log()

    def _load_existing_log(self) -> None:
        """Load existing skipped shinies from log file if it exists."""
        if self.log_file.exists():
            try:
                with open(self.log_file, encoding="utf-8") as f:
                    self.entries = json.load(f)
                logger.info(
                    f"Loaded {len(self.entries)} skipped shiny entries from {self.log_file}"
                )
            except (json.JSONDecodeError, OSError) as e:
                logger.error(f"Failed to load skipped shinies log: {e}")
                self.entries = []

    def log_skipped_shiny(
        self,
        worker_id: int,
        pokemon_name: str,
        target_pokemon: str,
        frame_diff: int,
        save_file: str,
        total_encounters: int,
        encounters: dict[str, int],
        action_taken: str,
    ) -> None:
        """Log a skipped shiny Pokemon encounter.

        Args:
            worker_id: ID of the worker that found the shiny.
            pokemon_name: Name of the Pokemon that was found.
            target_pokemon: Name of the target Pokemon being hunted.
            frame_diff: Frame difference for shiny animation detection.
            save_file: Path to the savestate file.
            total_encounters: Total encounters across all Pokemon.
            encounters: Dictionary of encounter counts by Pokemon name.
            action_taken: Action taken (e.g., "skipped_auto", "skipped_manual").
        """
        entry = {
            "worker_id": worker_id,
            "timestamp": datetime.now().isoformat(),
            "pokemon_name": pokemon_name,
            "target_pokemon": target_pokemon,
            "frame_diff": frame_diff,
            "save_file": save_file,
            "total_encounters": total_encounters,
            "encounters": encounters,
            "action_taken": action_taken,
            "is_target": False,  # Always False for skipped shinies
        }

        self.entries.append(entry)
        self._save_to_disk()

        logger.warning(
            f"⚠️  SKIPPED SHINY: {pokemon_name} (target: {target_pokemon}) - "
            f"Worker {worker_id}, Savestate: {save_file}"
        )

    def _save_to_disk(self) -> None:
        """Save all entries to disk."""
        try:
            with open(self.log_file, "w", encoding="utf-8") as f:
                json.dump(self.entries, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved {len(self.entries)} skipped shiny entries to {self.log_file}")
        except OSError as e:
            logger.error(f"Failed to save skipped shinies log: {e}")

    def get_entries(self) -> list[dict[str, Any]]:
        """Get all skipped shiny entries.

        Returns:
            List of all skipped shiny entries.
        """
        return self.entries.copy()

    def get_count(self) -> int:
        """Get the total number of skipped shinies.

        Returns:
            Total count of skipped shinies.
        """
        return len(self.entries)
