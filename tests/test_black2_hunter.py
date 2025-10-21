"""Tests for Black2Hunter class."""

from unittest.mock import patch

import numpy as np

from pyshiny_hunter.black2_hunter import Black2Hunter


class TestBlack2HunterInit:
    """Test Black2Hunter initialization."""

    def test_init_without_hunted_pokemon(self, mock_pokemon_csv_files, monkeypatch):
        """Test initialization without specifying hunted Pokemon."""
        monkeypatch.chdir(mock_pokemon_csv_files)
        hunter = Black2Hunter()
        assert hunter.encounters == {}
        assert len(hunter.pokemon_database) > 0
        assert "Pikachu" in hunter.pokemon_database

    def test_init_loads_pokemon_database(self, mock_pokemon_csv_files, monkeypatch):
        """Test that Pokemon database is loaded correctly from CSV files."""
        monkeypatch.chdir(mock_pokemon_csv_files)
        hunter = Black2Hunter()
        assert "Pikachu" in hunter.pokemon_database
        assert hunter.pokemon_database["Pikachu"] == 25
        assert "Charizard" in hunter.pokemon_database
        assert hunter.pokemon_database["Charizard"] == 6

    def test_init_creates_character_whitelist(self, mock_pokemon_csv_files, monkeypatch):
        """Test that character whitelist is created from Pokemon names."""
        monkeypatch.chdir(mock_pokemon_csv_files)
        hunter = Black2Hunter()
        # Should contain letters from Pokemon names
        assert "P" in hunter.characters_in_pokemon_names
        assert "i" in hunter.characters_in_pokemon_names
        assert "k" in hunter.characters_in_pokemon_names
        # Should not contain special characters
        assert "'" not in hunter.characters_in_pokemon_names
        assert " " not in hunter.characters_in_pokemon_names

    def test_init_handles_missing_csv_files(self, tmp_path, monkeypatch):
        """Test initialization when CSV files are missing (should not crash)."""
        # Create empty resources directory
        resources_dir = tmp_path / "resources" / "pokemon_names"
        resources_dir.mkdir(parents=True)
        monkeypatch.chdir(tmp_path)

        # Should not raise exception even with missing files
        hunter = Black2Hunter()
        assert hunter.pokemon_database == {}


class TestFoundPokemon:
    """Test _found_pokemon method."""

    def test_found_pokemon_with_bright_screens(
        self, mock_pokemon_csv_files, monkeypatch, bright_top_screen, bright_bottom_screen
    ):
        """Test Pokemon detection when both screens are bright (encounter flash)."""
        monkeypatch.chdir(mock_pokemon_csv_files)
        hunter = Black2Hunter()
        assert hunter._found_pokemon(bright_top_screen, bright_bottom_screen) is True

    def test_not_found_pokemon_with_dark_top_screen(
        self, mock_pokemon_csv_files, monkeypatch, black_screen, bright_bottom_screen
    ):
        """Test no Pokemon detection when top screen is dark."""
        monkeypatch.chdir(mock_pokemon_csv_files)
        hunter = Black2Hunter()
        assert hunter._found_pokemon(black_screen, bright_bottom_screen) is False

    def test_not_found_pokemon_with_dark_bottom_screen(
        self, mock_pokemon_csv_files, monkeypatch, bright_top_screen, black_screen
    ):
        """Test no Pokemon detection when bottom screen is dark."""
        monkeypatch.chdir(mock_pokemon_csv_files)
        hunter = Black2Hunter()
        assert hunter._found_pokemon(bright_top_screen, black_screen) is False

    def test_not_found_pokemon_with_both_dark_screens(
        self, mock_pokemon_csv_files, monkeypatch, black_screen
    ):
        """Test no Pokemon detection when both screens are dark."""
        monkeypatch.chdir(mock_pokemon_csv_files)
        hunter = Black2Hunter()
        assert hunter._found_pokemon(black_screen, black_screen) is False

    def test_found_pokemon_threshold_boundary(self, mock_pokemon_csv_files, monkeypatch):
        """Test Pokemon detection at threshold boundary (247)."""
        monkeypatch.chdir(mock_pokemon_csv_files)
        hunter = Black2Hunter()

        # Just below threshold - should not detect
        screen_246 = np.full((192, 256, 3), 246, dtype=np.uint8)
        assert hunter._found_pokemon(screen_246, screen_246) is False

        # At threshold - should not detect (uses > not >=)
        screen_247 = np.full((192, 256, 3), 247, dtype=np.uint8)
        assert hunter._found_pokemon(screen_247, screen_247) is False

        # Above threshold - should detect
        screen_248 = np.full((192, 256, 3), 248, dtype=np.uint8)
        assert hunter._found_pokemon(screen_248, screen_248) is True


class TestCheckedShiny:
    """Test _checked_shiny method."""

    def test_checked_shiny_with_sparkles(
        self, mock_pokemon_csv_files, monkeypatch, shiny_sparkle_screen, dark_bottom_screen
    ):
        """Test shiny check returns True when sparkle pixels detected."""
        monkeypatch.chdir(mock_pokemon_csv_files)
        hunter = Black2Hunter()
        with patch.object(hunter, "_Black2Hunter__determine_encounter", return_value="Pikachu"):
            result = hunter._checked_shiny(shiny_sparkle_screen, dark_bottom_screen)
            assert result is True

    def test_checked_shiny_returns_false_when_bottom_screen_too_bright(
        self, mock_pokemon_csv_files, monkeypatch, shiny_sparkle_screen, bright_bottom_screen
    ):
        """Test shiny check returns False during pokeball release (bright bottom)."""
        monkeypatch.chdir(mock_pokemon_csv_files)
        hunter = Black2Hunter()
        # Bottom screen too bright means we're still in pokeball release phase
        result = hunter._checked_shiny(shiny_sparkle_screen, bright_bottom_screen)
        assert result is False

    def test_checked_shiny_returns_false_without_sparkles(
        self, mock_pokemon_csv_files, monkeypatch, black_screen, dark_bottom_screen
    ):
        """Test shiny check returns False when no sparkle pixels detected."""
        monkeypatch.chdir(mock_pokemon_csv_files)
        hunter = Black2Hunter()
        result = hunter._checked_shiny(black_screen, dark_bottom_screen)
        assert result is False

    def test_checked_shiny_calls_determine_encounter(
        self, mock_pokemon_csv_files, monkeypatch, shiny_sparkle_screen, dark_bottom_screen
    ):
        """Test that _checked_shiny calls __determine_encounter when shiny detected."""
        monkeypatch.chdir(mock_pokemon_csv_files)
        hunter = Black2Hunter()
        with patch.object(
            hunter, "_Black2Hunter__determine_encounter", return_value="Pikachu"
        ) as mock_determine:
            hunter._checked_shiny(shiny_sparkle_screen, dark_bottom_screen)
            mock_determine.assert_called_once()


class TestBattleStarted:
    """Test _battle_started method."""

    def test_battle_started_with_battle_screen(
        self, mock_pokemon_csv_files, monkeypatch, black_screen, battle_bottom_screen
    ):
        """Test battle detection when bottom screen shows battle UI."""
        monkeypatch.chdir(mock_pokemon_csv_files)
        hunter = Black2Hunter()
        assert hunter._battle_started(black_screen, battle_bottom_screen) is True

    def test_battle_not_started_with_dark_screen(
        self, mock_pokemon_csv_files, monkeypatch, black_screen, dark_bottom_screen
    ):
        """Test no battle detection when bottom screen is dark."""
        monkeypatch.chdir(mock_pokemon_csv_files)
        hunter = Black2Hunter()
        assert hunter._battle_started(black_screen, dark_bottom_screen) is False

    def test_battle_started_threshold_boundary(self, mock_pokemon_csv_files, monkeypatch):
        """Test battle detection at threshold boundary (55)."""
        monkeypatch.chdir(mock_pokemon_csv_files)
        hunter = Black2Hunter()
        black_screen = np.zeros((192, 256, 3), dtype=np.uint8)

        # Just below threshold
        screen_54 = np.full((192, 256, 3), 54, dtype=np.uint8)
        assert hunter._battle_started(black_screen, screen_54) is False

        # At threshold (uses > not >=)
        screen_55 = np.full((192, 256, 3), 55, dtype=np.uint8)
        assert hunter._battle_started(black_screen, screen_55) is False

        # Above threshold
        screen_56 = np.full((192, 256, 3), 56, dtype=np.uint8)
        assert hunter._battle_started(black_screen, screen_56) is True


class TestIsPokemonShiny:
    """Test _is_pokemon_shiny method."""

    def test_is_shiny_with_long_animation(self, mock_pokemon_csv_files, monkeypatch):
        """Test shiny detection with animation longer than threshold (>500 frames)."""
        monkeypatch.chdir(mock_pokemon_csv_files)
        hunter = Black2Hunter()
        assert hunter._is_pokemon_shiny(501) is True
        assert hunter._is_pokemon_shiny(600) is True
        assert hunter._is_pokemon_shiny(1000) is True

    def test_not_shiny_with_short_animation(self, mock_pokemon_csv_files, monkeypatch):
        """Test non-shiny detection with animation shorter than threshold (<=500)."""
        monkeypatch.chdir(mock_pokemon_csv_files)
        hunter = Black2Hunter()
        assert hunter._is_pokemon_shiny(499) is False
        assert hunter._is_pokemon_shiny(400) is False
        assert hunter._is_pokemon_shiny(100) is False

    def test_is_shiny_threshold_boundary(self, mock_pokemon_csv_files, monkeypatch):
        """Test shiny detection at exact threshold (500 frames)."""
        monkeypatch.chdir(mock_pokemon_csv_files)
        hunter = Black2Hunter()
        # At threshold (uses > not >=)
        assert hunter._is_pokemon_shiny(500) is False
        # Just above threshold
        assert hunter._is_pokemon_shiny(501) is True


class TestDetermineEncounter:
    """Test __determine_encounter method (OCR pipeline)."""

    @patch("pyshiny_hunter.black2_hunter.pytesseract.image_to_string")
    def test_determine_encounter_exact_match(
        self, mock_tesseract, mock_pokemon_csv_files, monkeypatch, bright_top_screen
    ):
        """Test encounter determination with exact OCR match."""
        monkeypatch.chdir(mock_pokemon_csv_files)
        mock_tesseract.return_value = "Pikachu"
        hunter = Black2Hunter()

        result = hunter._Black2Hunter__determine_encounter(bright_top_screen)

        assert result == "Pikachu"
        assert hunter.encounters["Pikachu"] == 1
        mock_tesseract.assert_called_once()

    @patch("pyshiny_hunter.black2_hunter.pytesseract.image_to_string")
    def test_determine_encounter_fuzzy_match(
        self, mock_tesseract, mock_pokemon_csv_files, monkeypatch, bright_top_screen
    ):
        """Test encounter determination with fuzzy matching (OCR error correction)."""
        monkeypatch.chdir(mock_pokemon_csv_files)
        # OCR returns slightly wrong name
        mock_tesseract.return_value = "Pikachu"  # Close to "Pikachu"
        hunter = Black2Hunter()

        result = hunter._Black2Hunter__determine_encounter(bright_top_screen)

        # Should fuzzy match to "Pikachu"
        assert result == "Pikachu"
        assert hunter.encounters["Pikachu"] == 1

    @patch("pyshiny_hunter.black2_hunter.pytesseract.image_to_string")
    def test_determine_encounter_no_match(
        self, mock_tesseract, mock_pokemon_csv_files, monkeypatch, bright_top_screen
    ):
        """Test encounter determination when OCR returns unrecognizable text."""
        monkeypatch.chdir(mock_pokemon_csv_files)
        mock_tesseract.return_value = "XYZ123"  # Gibberish
        hunter = Black2Hunter()

        result = hunter._Black2Hunter__determine_encounter(bright_top_screen)

        # Should return the unrecognized name
        assert result == "Xyz123"  # Formatted as title case
        assert hunter.encounters["Xyz123"] == 1

    @patch("pyshiny_hunter.black2_hunter.pytesseract.image_to_string")
    def test_determine_encounter_increments_counter(
        self, mock_tesseract, mock_pokemon_csv_files, monkeypatch, bright_top_screen
    ):
        """Test that encounter counter increments for repeated encounters."""
        monkeypatch.chdir(mock_pokemon_csv_files)
        mock_tesseract.return_value = "Pikachu"
        hunter = Black2Hunter()

        # First encounter
        hunter._Black2Hunter__determine_encounter(bright_top_screen)
        assert hunter.encounters["Pikachu"] == 1

        # Second encounter
        hunter._Black2Hunter__determine_encounter(bright_top_screen)
        assert hunter.encounters["Pikachu"] == 2

        # Third encounter
        hunter._Black2Hunter__determine_encounter(bright_top_screen)
        assert hunter.encounters["Pikachu"] == 3

    @patch("pyshiny_hunter.black2_hunter.pytesseract.image_to_string")
    def test_determine_encounter_uses_character_whitelist(
        self, mock_tesseract, mock_pokemon_csv_files, monkeypatch, bright_top_screen
    ):
        """Test that OCR uses character whitelist from Pokemon names."""
        monkeypatch.chdir(mock_pokemon_csv_files)
        mock_tesseract.return_value = "Pikachu"
        hunter = Black2Hunter()

        hunter._Black2Hunter__determine_encounter(bright_top_screen)

        # Check that tesseract was called with whitelist config
        call_args = mock_tesseract.call_args
        config = call_args.kwargs["config"]
        assert "tessedit_char_whitelist" in config
        assert "Pikachu"[0] in hunter.characters_in_pokemon_names


class TestEncounterTracking:
    """Test encounter tracking functionality."""

    def test_get_encounters_empty(self, mock_pokemon_csv_files, monkeypatch):
        """Test getting encounters when none have been recorded."""
        monkeypatch.chdir(mock_pokemon_csv_files)
        hunter = Black2Hunter()
        assert hunter.get_encounters() == {}

    @patch("pyshiny_hunter.black2_hunter.pytesseract.image_to_string")
    def test_get_encounters_with_multiple_pokemon(
        self, mock_tesseract, mock_pokemon_csv_files, monkeypatch, bright_top_screen
    ):
        """Test getting encounters after detecting multiple Pokemon."""
        monkeypatch.chdir(mock_pokemon_csv_files)
        hunter = Black2Hunter()

        # Encounter Pikachu twice
        mock_tesseract.return_value = "Pikachu"
        hunter._Black2Hunter__determine_encounter(bright_top_screen)
        hunter._Black2Hunter__determine_encounter(bright_top_screen)

        # Encounter Charizard once
        mock_tesseract.return_value = "Charizard"
        hunter._Black2Hunter__determine_encounter(bright_top_screen)

        encounters = hunter.get_encounters()
        assert encounters["Pikachu"] == 2
        assert encounters["Charizard"] == 1
