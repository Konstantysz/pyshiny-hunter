"""Centralized Pokemon database loading utility.

This module provides shared functions for loading Pokemon names and data
from CSV files, avoiding duplication across the codebase.
"""

from __future__ import annotations

from pathlib import Path

from pyshiny_hunter import config
from pyshiny_hunter.module_logger import logger


def load_pokemon_database(generations: list[int] | None = None) -> dict[str, int]:
    """Load Pokemon names and Pokedex numbers from CSV files.

    Args:
        generations: List of generation numbers to load (1-5).
                    If None, loads all generations (1-5).

    Returns:
        Dictionary mapping Pokemon name (str) to Pokedex number (int).

    Example:
        >>> db = load_pokemon_database([1, 2])
        >>> db["Pikachu"]
        25
        >>> db["Chikorita"]
        152
    """
    if generations is None:
        generations = [1, 2, 3, 4, 5]

    pokemon_db: dict[str, int] = {}

    # Validate database path exists
    if not hasattr(config, "POKEMON_DATABASE_PATH") or config.POKEMON_DATABASE_PATH is None:
        logger.error("POKEMON_DATABASE_PATH not configured")
        return pokemon_db

    database_path = Path(config.POKEMON_DATABASE_PATH)
    if not database_path.exists():
        logger.warning(f"Pokemon database directory not found: {database_path}")
        return pokemon_db

    if not database_path.is_dir():
        logger.error(f"Pokemon database path is not a directory: {database_path}")
        return pokemon_db

    for gen in generations:
        csv_file = f"gen{gen}.csv"
        file_path = database_path / csv_file

        try:
            with open(file_path, encoding="utf-8") as f:
                next(f)  # Skip header line
                for line_num, line in enumerate(f, start=2):  # Start at 2 since we skip header
                    parts = line.strip().split(",")
                    if len(parts) >= 2:
                        try:
                            pokedex_num = int(parts[0].strip())
                            pokemon_name = parts[1].strip()

                            # Validate Pokedex number range (Gen 1-5: 1-649)
                            if not (1 <= pokedex_num <= 649):
                                logger.warning(
                                    f"Invalid Pokedex number {pokedex_num} at {file_path}:{line_num}, skipping"
                                )
                                continue

                            # Validate Pokemon name (reasonable length, safe characters)
                            if not pokemon_name or len(pokemon_name) > 50:
                                logger.warning(
                                    f"Invalid Pokemon name length at {file_path}:{line_num}, skipping"
                                )
                                continue

                            # Check for path traversal attempts or invalid characters in name
                            if any(
                                c in pokemon_name
                                for c in ["/", "\\", "\0", "..", "<", ">", "|", "*", "?"]
                            ):
                                logger.warning(
                                    f"Invalid characters in Pokemon name at {file_path}:{line_num}, skipping"
                                )
                                continue

                            pokemon_db[pokemon_name] = pokedex_num

                        except ValueError as e:
                            logger.warning(
                                f"Error parsing Pokedex number at {file_path}:{line_num}: {e}"
                            )
                            continue
        except FileNotFoundError:
            logger.warning(f"Pokemon CSV file not found: {file_path}")
        except (IndexError, UnicodeDecodeError) as e:
            logger.warning(f"Error parsing {file_path}: {e}")

    logger.debug(f"Loaded {len(pokemon_db)} Pokemon from {len(generations)} generations")
    return pokemon_db


def validate_pokemon_name(
    name: str, pokemon_db: dict[str, int] | None = None
) -> tuple[bool, str, str]:
    """Validate Pokemon name (case-insensitive).

    Args:
        name: Pokemon name to validate.
        pokemon_db: Optional pre-loaded Pokemon database.
                   If None, loads all generations.

    Returns:
        Tuple of (is_valid, error_message, canonical_name).
        canonical_name is the correctly-cased name from database, or empty string if invalid.
        If valid, error_message is empty string.
        If invalid, error_message contains suggestion or error.

    Example:
        >>> is_valid, error, canonical = validate_pokemon_name("Pikachu")
        >>> is_valid
        True
        >>> canonical
        'Pikachu'
        >>> is_valid, error, canonical = validate_pokemon_name("Pikach")
        >>> is_valid
        False
        >>> "Pikachu" in error
        True
    """
    if not name or name.strip() == "":
        return True, "", ""  # Empty is valid (no target mode)

    if pokemon_db is None:
        pokemon_db = load_pokemon_database()

    # Build lowercase lookup map for O(1) validation (more efficient than O(n) loop)
    name_lower = name.strip().lower()
    lowercase_map = {db_name.lower(): db_name for db_name in pokemon_db.keys()}

    if name_lower in lowercase_map:
        return True, "", lowercase_map[name_lower]  # Return canonical name

    # Not found - suggest close matches
    try:
        from difflib import get_close_matches

        suggestions = get_close_matches(name, pokemon_db.keys(), n=3, cutoff=0.6)

        if suggestions:
            return False, f"Invalid Pokemon. Did you mean: {', '.join(suggestions)}?", ""
        else:
            return False, f"Invalid Pokemon name: '{name}'", ""
    except ImportError:
        return False, f"Invalid Pokemon name: '{name}'", ""


def filter_pokemon_names(query: str, pokemon_names: list[str], max_results: int = 10) -> list[str]:
    """Filter Pokemon names by query string (case-insensitive substring match).

    Args:
        query: Search query (partial Pokemon name).
        pokemon_names: List of all Pokemon names to search.
        max_results: Maximum number of results to return.

    Returns:
        List of matching Pokemon names (up to max_results).

    Example:
        >>> names = ["Bulbasaur", "Ivysaur", "Venusaur", "Charmander"]
        >>> filter_pokemon_names("saur", names)
        ['Bulbasaur', 'Ivysaur', 'Venusaur']
        >>> filter_pokemon_names("char", names, max_results=1)
        ['Charmander']
    """
    if not query or query.strip() == "":
        return []

    query_lower = query.strip().lower()
    matches = [name for name in pokemon_names if query_lower in name.lower()]

    return matches[:max_results]
