"""Pytest configuration and shared fixtures."""

import numpy as np
import pytest
from filelock import FileLock


@pytest.fixture
def white_screen():
    """Create a white screen (255, 255, 255) for testing encounter detection."""
    return np.full((192, 256, 3), 255, dtype=np.uint8)


@pytest.fixture
def black_screen():
    """Create a black screen (0, 0, 0) for testing."""
    return np.zeros((192, 256, 3), dtype=np.uint8)


@pytest.fixture
def gray_screen():
    """Create a gray screen for testing."""
    return np.full((192, 256, 3), 127, dtype=np.uint8)


@pytest.fixture
def bright_top_screen():
    """Create a bright top screen for Pokemon encounter (avg > 247)."""
    return np.full((192, 256, 3), 250, dtype=np.uint8)


@pytest.fixture
def bright_bottom_screen():
    """Create a bright bottom screen for Pokemon encounter (avg > 247)."""
    return np.full((192, 256, 3), 250, dtype=np.uint8)


@pytest.fixture
def dark_bottom_screen():
    """Create a dark bottom screen for pokeball release phase (avg < 30)."""
    return np.full((192, 256, 3), 25, dtype=np.uint8)


@pytest.fixture
def battle_bottom_screen():
    """Create a bottom screen for battle state (avg > 55)."""
    return np.full((192, 256, 3), 60, dtype=np.uint8)


@pytest.fixture
def shiny_sparkle_screen():
    """Create a screen with bright pixels in center region for shiny detection."""
    screen = np.zeros((192, 256, 3), dtype=np.uint8)
    # Add bright pixels in the center region (where sparkles appear)
    screen[64:128, 85:171] = 240  # Center 1/3 width, top 2/3 height
    return screen


@pytest.fixture
def sample_pokemon_names():
    """Sample Pokemon names database for testing."""
    return {
        "Pikachu": 25,
        "Charizard": 6,
        "Mewtwo": 150,
        "Bulbasaur": 1,
        "Squirtle": 7,
        "Eevee": 133,
        "Snorlax": 143,
        "Dragonite": 149,
        "Gengar": 94,
        "Gyarados": 130,
    }


@pytest.fixture
def mock_pokemon_csv_files(tmp_path, sample_pokemon_names):
    """Create temporary CSV files with Pokemon data."""
    resources_dir = tmp_path / "resources" / "pokemon_names"
    resources_dir.mkdir(parents=True)

    # Create gen1.csv
    gen1_file = resources_dir / "gen1.csv"
    with open(gen1_file, "w", encoding="utf-8") as f:
        f.write("number,name\n")
        for name, number in sample_pokemon_names.items():
            f.write(f"{number},{name}\n")

    return tmp_path


@pytest.fixture(scope="session")
def easyocr_model_lock(tmp_path_factory):
    """Ensure only one test process downloads EasyOCR models at a time.

    This prevents race conditions on Windows CI where multiple test processes
    try to download the same EasyOCR model file simultaneously, causing
    PermissionError: [WinError 32] file locking conflicts.

    The lock file is placed in the pytest temp directory and shared across
    all test workers when running with pytest-xdist.
    """
    lock_file = tmp_path_factory.getbasetemp().parent / "easyocr_download.lock"
    return FileLock(str(lock_file))
