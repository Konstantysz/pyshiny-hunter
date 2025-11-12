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

    for gen in generations:
        csv_file = f"gen{gen}.csv"
        file_path = Path(config.POKEMON_DATABASE_PATH) / csv_file

        try:
            with open(file_path, encoding="utf-8") as f:
                next(f)  # Skip header line
                for line in f:
                    parts = line.strip().split(",")
                    if len(parts) >= 2:
                        pokedex_num = int(parts[0].strip())
                        pokemon_name = parts[1].strip()
                        pokemon_db[pokemon_name] = pokedex_num
        except FileNotFoundError:
            logger.warning(f"Pokemon CSV file not found: {file_path}")
        except (ValueError, IndexError) as e:
            logger.warning(f"Error parsing {file_path}: {e}")

    logger.debug(f"Loaded {len(pokemon_db)} Pokemon from {len(generations)} generations")
    return pokemon_db


def get_pokemon_names(generations: list[int] | None = None) -> list[str]:
    """Get sorted list of Pokemon names for autocomplete.

    Args:
        generations: List of generation numbers to load (1-5).
                    If None, loads all generations (1-5).

    Returns:
        Sorted list of Pokemon names.

    Example:
        >>> names = get_pokemon_names([1])
        >>> "Bulbasaur" in names
        True
        >>> "Chikorita" in names
        False
    """
    db = load_pokemon_database(generations)
    return sorted(db.keys())


def validate_pokemon_name(name: str, pokemon_db: dict[str, int] | None = None) -> tuple[bool, str]:
    """Validate Pokemon name (case-insensitive).

    Args:
        name: Pokemon name to validate.
        pokemon_db: Optional pre-loaded Pokemon database.
                   If None, loads all generations.

    Returns:
        Tuple of (is_valid, error_message).
        If valid, error_message is empty string.
        If invalid, error_message contains suggestion or error.

    Example:
        >>> is_valid, error = validate_pokemon_name("Pikachu")
        >>> is_valid
        True
        >>> is_valid, error = validate_pokemon_name("Pikach")
        >>> is_valid
        False
        >>> "Pikachu" in error
        True
    """
    if not name or name.strip() == "":
        return True, ""  # Empty is valid (no target mode)

    if pokemon_db is None:
        pokemon_db = load_pokemon_database()

    # Case-insensitive lookup
    for db_name in pokemon_db.keys():
        if name.strip().lower() == db_name.lower():
            return True, ""

    # Not found - suggest close matches
    try:
        from difflib import get_close_matches

        suggestions = get_close_matches(name, pokemon_db.keys(), n=3, cutoff=0.6)

        if suggestions:
            return False, f"Invalid Pokemon. Did you mean: {', '.join(suggestions)}?"
        else:
            return False, f"Invalid Pokemon name: '{name}'"
    except ImportError:
        return False, f"Invalid Pokemon name: '{name}'"


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
