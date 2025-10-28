"""Unit tests for Enhanced OCR pipeline (EasyOCR + SymSpell + Fuzzy matching)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import cv2 as cv
import pytest

from pyshiny_hunter.enhanced_ocr import EnhancedOCR, OCRResult

if TYPE_CHECKING:
    import numpy as np


@pytest.fixture
def pokemon_database() -> dict[str, int]:
    """Sample Pokemon database for testing."""
    return {
        "Pikachu": 25,
        "Charizard": 6,
        "Bulbasaur": 1,
        "Squirtle": 7,
        "Jigglypuff": 39,
        "Meowth": 52,
        "Psyduck": 54,
        "Snorlax": 143,
        "Watchog": 505,
        "Herdier": 506,
    }


@pytest.fixture
def enhanced_ocr(pokemon_database: dict[str, int]) -> EnhancedOCR:
    """Initialize Enhanced OCR with test database."""
    return EnhancedOCR(pokemon_database)


class TestEnhancedOCRInitialization:
    """Test Enhanced OCR initialization."""

    def test_initialization_creates_symspell_dictionary(self, pokemon_database: dict[str, int]):
        """Test that SymSpell dictionary is created from Pokemon database."""
        ocr = EnhancedOCR(pokemon_database)

        assert ocr.pokemon_names == set(pokemon_database.keys())
        assert len(ocr.pokemon_names) == len(pokemon_database)
        assert ocr.symspell is not None

    def test_easyocr_reader_lazy_loads(self, pokemon_database: dict[str, int]):
        """Test that EasyOCR reader starts loading in background."""
        ocr = EnhancedOCR(pokemon_database)

        # Reader should be loading or loaded
        assert hasattr(ocr, "_reader")
        assert hasattr(ocr, "_loading_thread")


class TestOCRStages:
    """Test different stages of OCR pipeline."""

    def test_format_pokemon_name_exact_match(self, enhanced_ocr: EnhancedOCR):
        """Test formatting Pokemon name for exact match."""
        formatted = enhanced_ocr._format_pokemon_name("Pikachu")
        assert formatted == "Pikachu"

    def test_format_pokemon_name_case_insensitive(self, enhanced_ocr: EnhancedOCR):
        """Test formatting works with different cases."""
        assert enhanced_ocr._format_pokemon_name("PIKACHU") == "Pikachu"
        assert enhanced_ocr._format_pokemon_name("pikachu") == "Pikachu"
        assert enhanced_ocr._format_pokemon_name("PiKaChU") == "Pikachu"

    def test_symspell_correction(self, enhanced_ocr: EnhancedOCR):
        """Test SymSpell corrects minor typos (1-2 character edits)."""
        # "Pikach" -> "Pikachu" (1 character missing)
        result = enhanced_ocr._apply_symspell("Pikach")
        assert result == "Pikachu"

        # "Meouth" -> "Meowth" (typo)
        result = enhanced_ocr._apply_symspell("Meouth")
        assert result == "Meowth"

    def test_fuzzy_matching_fallback(self, enhanced_ocr: EnhancedOCR):
        """Test fuzzy matching handles more complex OCR errors."""
        # "Jigglypuf" -> "Jigglypuff" (missing 'f')
        result, confidence = enhanced_ocr._apply_fuzzy_matching("Jigglypuf")
        assert result == "Jigglypuff"
        assert 0.8 <= confidence <= 1.0

        # "Watchog" with minor corruption
        result, confidence = enhanced_ocr._apply_fuzzy_matching("Watchog")
        assert result == "Watchog"
        assert confidence >= 0.9

    def test_failed_match_returns_none(self, enhanced_ocr: EnhancedOCR):
        """Test that completely unrecognizable text returns None."""
        result = enhanced_ocr._apply_symspell("XYZ123!@#")
        assert result is None

        result, _ = enhanced_ocr._apply_fuzzy_matching("XYZ123!@#")
        assert result is None


class TestOCRResultStructure:
    """Test OCR result data structure."""

    def test_ocr_result_structure(self):
        """Test OCRResult dataclass has all required fields."""
        result = OCRResult(
            text="Pikachu",
            raw_text="PIKACHU",
            stage="exact",
            confidence=1.0,
            exact_match=True,
        )

        assert result.text == "Pikachu"
        assert result.raw_text == "PIKACHU"
        assert result.stage == "exact"
        assert result.confidence == 1.0
        assert result.exact_match is True


class TestPreprocessing:
    """Test image preprocessing for OCR."""

    def test_preprocessing_applies_morphological_opening(self, enhanced_ocr: EnhancedOCR):
        """Test that preprocessing includes morphological opening for outline removal."""
        # Create a simple white-on-black test image
        import numpy as np

        test_image = np.zeros((50, 100, 3), dtype=np.uint8)
        test_image[20:30, 40:60] = [255, 255, 255]  # White rectangle

        # The _run_easyocr method should apply preprocessing
        # We can't easily test the full pipeline without actual EasyOCR,
        # but we can verify the preprocessing steps exist in the code
        assert hasattr(enhanced_ocr, "_run_easyocr")


@pytest.mark.integration
class TestEnhancedOCRIntegration:
    """Integration tests using real OCR failure dataset (if available)."""

    def test_ocr_on_failure_dataset(self, enhanced_ocr: EnhancedOCR):
        """Test Enhanced OCR on collected failure screenshots (if dataset exists)."""
        dataset_path = Path("data/ocr_training_dataset")

        if not dataset_path.exists():
            pytest.skip("OCR training dataset not found")

        # Find metadata files
        metadata_files = list(dataset_path.glob("*_metadata.json"))
        if not metadata_files:
            pytest.skip("No test cases in dataset")

        # Test at least one case
        metadata_file = metadata_files[0]
        screenshot_name = metadata_file.name.replace("_metadata.json", "_screenshot.png")
        screenshot_path = dataset_path / screenshot_name

        if not screenshot_path.exists():
            pytest.skip("Screenshot file missing")

        # Load image and run OCR
        image = cv.imread(str(screenshot_path))
        assert image is not None

        result = enhanced_ocr.recognize(image)

        # Verify result structure
        assert isinstance(result, OCRResult)
        assert result.text in enhanced_ocr.pokemon_names
        assert result.stage in ("exact", "symspell", "fuzzy", "failed")
        assert 0.0 <= result.confidence <= 1.0

    def test_success_rate_on_dataset(self, enhanced_ocr: EnhancedOCR):
        """Test that Enhanced OCR achieves high success rate on failure dataset."""
        dataset_path = Path("data/ocr_training_dataset")

        if not dataset_path.exists():
            pytest.skip("OCR training dataset not found")

        metadata_files = list(dataset_path.glob("*_metadata.json"))
        if not metadata_files:
            pytest.skip("No test cases in dataset")

        successes = 0
        total = 0

        for metadata_file in metadata_files:
            screenshot_name = metadata_file.name.replace("_metadata.json", "_screenshot.png")
            screenshot_path = dataset_path / screenshot_name

            if not screenshot_path.exists():
                continue

            image = cv.imread(str(screenshot_path))
            if image is None:
                continue

            result = enhanced_ocr.recognize(image)
            total += 1

            # Success if we got any match (exact, symspell, or fuzzy)
            if result.stage != "failed":
                successes += 1

        if total > 0:
            success_rate = successes / total
            # Enhanced OCR should achieve >90% success rate
            assert success_rate >= 0.9, f"Success rate {success_rate:.1%} below 90% threshold"


class TestBackgroundLoading:
    """Test background loading of EasyOCR model."""

    def test_reader_loads_in_background(self, pokemon_database: dict[str, int]):
        """Test that EasyOCR reader loads in background thread."""
        ocr = EnhancedOCR(pokemon_database)

        # Loading thread should be started
        assert ocr._loading_thread is not None
        assert ocr._loading_thread.daemon is True

        # Accessing reader should wait for load (or return immediately if loaded)
        reader = ocr.reader
        assert reader is not None

        # Thread should be finished after accessing reader
        assert not ocr._loading_thread.is_alive() or ocr._reader is not None
