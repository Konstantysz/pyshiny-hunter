"""Configuration constants for PyShiny Hunter.

This module centralizes all configurable parameters including Computer Vision
thresholds, OCR settings, and game-specific values. These values were empirically
determined through testing and can be adjusted for different games or conditions.
"""

# =============================================================================
# Computer Vision Thresholds (Black 2 specific)
# =============================================================================

# Pixel brightness threshold for detecting shiny sparkles
# Higher values = stricter detection (fewer false positives)
POKEBALL_LIGHT_PIXEL_THRESHOLD: int = 230

# Average pixel value threshold for white flash detection (wild Pokemon appears)
# Both screens must exceed this value to confirm encounter
WHITE_SCREEN_AVERAGE_PIXEL_VALUE: int = 247

# Average pixel value during Pokeball release animation
# Bottom screen should be below this value during sparkle check
POKEBALL_RELEASE_AVERAGE_PIXEL_VALUE: int = 30

# Average pixel value when battle UI is visible on bottom screen
# Values above this indicate battle has started
BATTLE_BOTTOM_SCREEN_AVERAGE_PIXEL_VALUE: int = 55

# Percentage of pixels that must exceed brightness threshold for shiny detection
# Lower values = more sensitive (more false positives)
SPARKLE_PIXEL_PERCENTAGE_THRESHOLD: float = 20.0

# =============================================================================
# Animation Detection
# =============================================================================

# Frame count threshold for shiny detection
# Shiny Pokemon have longer entrance animations (>500 frames at 60 FPS)
# Accuracy: ~95%
SHINY_ANIMATION_FRAME_THRESHOLD: int = 500

# =============================================================================
# OCR Settings
# =============================================================================

# Region of interest for Pokemon name (top screen coordinates)
# Format: [y_start, y_end, x_start, x_end]
OCR_NAME_REGION_Y_START: int = 30
OCR_NAME_REGION_Y_END: int = 40
OCR_NAME_REGION_X_START: int = 10
OCR_NAME_REGION_X_END: int = 75

# OCR preprocessing
# Optimal upscaling: 2× LANCZOS4 achieves 100% accuracy (vs 84.62% with 3× LINEAR)
# Counter-intuitive: smaller upscaling = cleaner edges, less interpolation artifacts
OCR_RESIZE_FACTOR: float = 2.0  # Upscaling factor (benchmarked optimal value)
OCR_BINARY_THRESHOLD: int = 127  # Grayscale threshold for binarization
OCR_BINARY_MAX_VALUE: int = 255  # Max value for binary threshold

# Tesseract settings
TESSERACT_PSM_MODE: int = 7  # Page segmentation mode (7 = single line)

# Fuzzy matching for OCR error correction
FUZZY_MATCH_CUTOFF: float = 0.6  # Minimum similarity ratio (0.0-1.0)
FUZZY_MATCH_TOP_N: int = 1  # Number of matches to return


# =============================================================================
# Pokemon Database
# =============================================================================

# CSV files to load (in order)
POKEMON_CSV_FILES: list[str] = [
    "gen1.csv",
    "gen2.csv",
    "gen3.csv",
    "gen4.csv",
    "gen5.csv",
]

# Path to Pokemon name database
POKEMON_DATABASE_PATH: str = "resources/pokemon_names/"

# =============================================================================
# Shiny Probability
# =============================================================================

# Base shiny odds for Pokemon Black 2 (without Shiny Charm or Masuda Method)
SHINY_ODDS_DENOMINATOR: int = 8192

# =============================================================================
# Benchmark Constants
# =============================================================================

# Average frames per encounter cycle in Pokemon Black 2
# This includes: encounter animation + battle start + identification + reset
# Measured empirically at 60 FPS emulation speed
AVERAGE_ENCOUNTER_CYCLE_FRAMES: int = 450

# =============================================================================
# Screen Region Analysis
# =============================================================================

# Fraction of screen width/height to analyze for sparkles (center region)
SPARKLE_REGION_HEIGHT_FRACTION: float = 2.0 / 3.0  # Top 2/3 of screen
SPARKLE_REGION_WIDTH_START_FRACTION: float = 1.0 / 3.0  # Middle third (horizontal)
SPARKLE_REGION_WIDTH_END_FRACTION: float = 2.0 / 3.0

# =============================================================================
# Worker RNG Desynchronization
# =============================================================================

# DeSmuME has deterministic RNG: same savestate + same inputs = identical encounters
# To guarantee unique RNG states across workers, we offset each worker by N frames
# Hybrid approach: base offset (guarantees uniqueness) + random jitter (adds variety)

# Base offset per worker (frames) - ensures no two workers share RNG state
# 60 frames @ 60 FPS = 1 second per worker
# Worker 0: 0 frames, Worker 1: 60 frames, Worker 2: 120 frames, etc.
WORKER_RNG_BASE_OFFSET_FRAMES: int = 60

# Random jitter range (frames) - adds variety while maintaining uniqueness guarantee
# Each worker gets base + random(0, JITTER) offset
# 30 frames @ 60 FPS = 0-0.5 seconds additional randomization
# Example ranges: Worker 0: [0,30], Worker 1: [60,90], Worker 2: [120,150] (no overlap!)
WORKER_RNG_JITTER_FRAMES: int = 30

# =============================================================================
# Manual Control - Keyboard Mapping
# =============================================================================

# Keyboard mapping for manual emulator control
# Format: ImGui key code -> DeSmuME key name
# Default controls inspired by common emulator layouts:
#   D-Pad: Arrow keys
#   A/B/X/Y: Z/X/A/S (left-hand positioning for right-handed mouse use)
#   L/R: Q/W (above A/S for ergonomic reach)
#   Start/Select: Enter/Shift

MANUAL_CONTROL_KEY_MAP: dict[str, str] = {
    # D-Pad
    "UP": "KEY_UP",
    "DOWN": "KEY_DOWN",
    "LEFT": "KEY_LEFT",
    "RIGHT": "KEY_RIGHT",
    # Face buttons
    "X": "KEY_A",  # A button (primary action)
    "Z": "KEY_B",  # B button (secondary action/back)
    "S": "KEY_X",  # X button
    "A": "KEY_Y",  # Y button
    # Shoulder buttons
    "Q": "KEY_L",  # L trigger
    "W": "KEY_R",  # R trigger
    # System buttons
    "ENTER": "KEY_START",
    "SHIFT": "KEY_SELECT",  # Both left and right shift (detected via io.key_shift)
}

# =============================================================================
# OCR Training Dataset Collection
# =============================================================================

# Enable saving screenshots when OCR fails to recognize Pokemon names
# When enabled, saves cropped regions and metadata for creating training datasets
# Default: False (enable manually when collecting data for model improvement)
SAVE_FAILED_OCR_SCREENSHOTS: bool = False

# Directory path for saving failed OCR screenshots and metadata
# Saved in flat structure: YYYYMMDD_HHMMSS_screenshot.png + metadata.json
OCR_FAILED_SCREENSHOTS_PATH: str = "data/ocr_training_dataset/"

# Minimum confidence threshold for saving failed OCR screenshots
# Only screenshots with fuzzy match confidence below this threshold will be saved
# Range: 0.0-1.0, where 1.0 = perfect match
# Examples:
#   0.8 = Save only low-confidence matches (recommended for collecting problematic cases)
#   0.6 = Save medium-confidence matches (more data, some false positives)
#   1.0 = Save all non-exact matches (maximum dataset size)
OCR_LOW_CONFIDENCE_THRESHOLD: float = 0.8
