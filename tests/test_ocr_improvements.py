"""Tests for OCR improvements (upscaling optimization + format helpers)."""

import pytest

from pyshiny_hunter.black2_hunter import Black2Hunter


class TestOCRHelperMethods:
    """Test new OCR helper methods in Black2Hunter."""

    def test_format_pokemon_name_uppercase(self, mock_pokemon_csv_files, monkeypatch):
        """Test formatting all-uppercase OCR output."""
        monkeypatch.chdir(mock_pokemon_csv_files)
        hunter = Black2Hunter()

        result = hunter._format_pokemon_name("PIKACHU")
        assert result == "Pikachu"

    def test_format_pokemon_name_lowercase(self, mock_pokemon_csv_files, monkeypatch):
        """Test formatting all-lowercase OCR output."""
        monkeypatch.chdir(mock_pokemon_csv_files)
        hunter = Black2Hunter()

        result = hunter._format_pokemon_name("pikachu")
        assert result == "Pikachu"

    def test_format_pokemon_name_mixed_case(self, mock_pokemon_csv_files, monkeypatch):
        """Test formatting mixed-case OCR output."""
        monkeypatch.chdir(mock_pokemon_csv_files)
        hunter = Black2Hunter()

        result = hunter._format_pokemon_name("pIkAcHu")
        assert result == "Pikachu"

    def test_format_pokemon_name_with_punctuation(self, mock_pokemon_csv_files, monkeypatch):
        """Test formatting names with special characters (Mr. Mime, Porygon-Z)."""
        monkeypatch.chdir(mock_pokemon_csv_files)
        hunter = Black2Hunter()

        # Test "Mr. Mime" formatting
        result = hunter._format_pokemon_name("mr. mime")
        assert result == "Mr. Mime"

        # Test "Porygon-Z" formatting
        result = hunter._format_pokemon_name("porygon-z")
        assert result == "Porygon-Z"
