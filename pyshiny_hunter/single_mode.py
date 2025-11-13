"""Single-emulator mode with integrated GUI.

This module implements the original single-emulator mode where
the GUI and emulator run in the same process.
"""

from __future__ import annotations

import datetime
import json
import re
from pathlib import Path

from pyshiny_hunter.black2_hunter import Black2Hunter
from pyshiny_hunter.module_logger import logger
from pyshiny_hunter.py_desmume_manager import PyDeSmuMEManager


def sanitize_pokemon_name_for_path(pokemon_name: str | None) -> str:
    """Sanitize Pokemon name for use in file paths.

    Removes or replaces characters that could cause path traversal or filesystem issues.
    This prevents security vulnerabilities when using OCR-detected Pokemon names in filenames.

    Args:
        pokemon_name: Pokemon name from OCR (potentially untrusted input)

    Returns:
        Sanitized name safe for use in file paths (only alphanumeric, underscore, hyphen)
    """
    if not pokemon_name:
        return "Unknown"

    # Replace any character that's not alphanumeric, underscore, or hyphen with underscore
    # This prevents path traversal (/, \, ..) and special filesystem characters
    safe_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", pokemon_name)

    # Ensure we have a non-empty result
    if not safe_name or safe_name.strip("_") == "":
        return "Unknown"

    return safe_name


def single_mode_worker(
    manager: PyDeSmuMEManager, target_pokemon: str | None = None, target_action: str = "alert"
):
    """Original single-emulator mode with integrated GUI.

    Args:
        manager: PyDeSmuMEManager instance with initialized emulator
        target_pokemon: Optional target Pokemon name for target mode
        target_action: Action for non-target shinies ('alert', 'pause', 'continue')
    """
    num_emulators = len(manager.get_emulators())
    hunters = [Black2Hunter(target_pokemon=target_pokemon) for _ in range(num_emulators)]
    battle_ready_frame_list = [-1] * num_emulators
    battle_start_frame_list = [-1] * num_emulators

    # Logging lists for target mode
    shiny_log: list[dict] = []
    skipped_log: list[dict] = []

    while manager.update_frame(hunters[0].get_encounters()):
        emulators = manager.get_emulators()
        for emulator_id, emulator in enumerate(emulators):
            top_screen, bottom_screen = emulator.get_screens()
            hunter = hunters[emulator_id]
            battle_start_frame = battle_start_frame_list[emulator_id]
            battle_ready_frame = battle_ready_frame_list[emulator_id]

            if hunter.current_state.id == "search":
                hunter.searching_pokemon(top_screen, bottom_screen)

                if emulator.frame % 10 == 0:
                    manager.add_input_to_queue(emulator_id, "key", key="KEY_LEFT")
                elif emulator.frame % 10 == 5:
                    manager.add_input_to_queue(emulator_id, "key", key="KEY_RIGHT")
            elif hunter.current_state.id == "check_if_shiny":
                hunter.checking_shiny(top_screen, bottom_screen)
                if battle_start_frame == -1:
                    battle_start_frame_list[emulator_id] = emulator.frame
            elif hunter.current_state.id == "pre_battle_animation":
                hunter.waiting_for_battle_start(top_screen, bottom_screen)
                if battle_ready_frame == -1:
                    battle_ready_frame_list[emulator_id] = emulator.frame
            elif hunter.current_state.id == "in_battle":
                hunter.running_away(battle_ready_frame - battle_start_frame)
                if hunter.current_state.id == "found":
                    # SHINY FOUND!
                    pokemon_name = hunter.get_last_encountered_pokemon() or "Unknown"
                    is_target = hunter.is_target_match()

                    logger.info("=" * 60)
                    logger.info(f"⭐ SHINY POKEMON FOUND: {pokemon_name} ⭐")
                    if target_pokemon:
                        logger.info(f"Target: {target_pokemon} | Match: {is_target}")
                    logger.info("=" * 60)

                    # ALWAYS save savestate (safety first!)
                    # Sanitize pokemon_name to prevent path traversal vulnerabilities
                    safe_pokemon_name = sanitize_pokemon_name_for_path(pokemon_name)
                    save_dir = Path("roms/states/black2")
                    save_dir.mkdir(parents=True, exist_ok=True)
                    save_name = (
                        save_dir
                        / f"shiny_{safe_pokemon_name}_{battle_ready_frame - battle_start_frame}.dst"
                    )

                    # Validate the resolved path is within save_dir (defense in depth)
                    try:
                        save_name.resolve().relative_to(save_dir.resolve())
                    except ValueError:
                        logger.error(f"Invalid savestate path detected: {save_name}")
                        save_name = (
                            save_dir
                            / f"shiny_invalid_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.dst"
                        )

                    emulator.emulator.savestate.save_file(str(save_name))
                    logger.info(f"💾 Saved to: {save_name}")

                    # Log to shiny log with target info
                    shiny_entry = {
                        "emulator_id": emulator_id,
                        "timestamp": datetime.datetime.now().isoformat(),
                        "pokemon_name": pokemon_name,
                        "frame_diff": battle_ready_frame - battle_start_frame,
                        "save_file": str(save_name),
                        "total_encounters": sum(hunter.get_encounters().values()),
                        "encounters": dict(hunter.get_encounters()),
                        "is_target": is_target,
                        "target_pokemon": target_pokemon,
                    }
                    shiny_log.append(shiny_entry)
                    logger.info("✅ Logged to shiny log")

                    # Target mode logic
                    if target_pokemon and not is_target:
                        # Non-target shiny found!
                        logger.warning(f"⚠️  Non-target shiny: {pokemon_name}")

                        # Log to skipped shinies
                        skipped_entry = {
                            "emulator_id": emulator_id,
                            "timestamp": datetime.datetime.now().isoformat(),
                            "pokemon_name": pokemon_name,
                            "target_pokemon": target_pokemon,
                            "frame_diff": battle_ready_frame - battle_start_frame,
                            "save_file": str(save_name),
                            "total_encounters": sum(hunter.get_encounters().values()),
                            "encounters": dict(hunter.get_encounters()),
                            "action_taken": target_action,
                        }
                        skipped_log.append(skipped_entry)
                        logger.info("📋 Logged to skipped shinies")

                        # Handle based on target_action
                        if target_action in ["alert", "pause"]:
                            logger.warning(
                                f"🚨 ACTION: {target_action} - Pausing (resume manually or close)"
                            )
                            # In single mode, we can't pause programmatically
                            # User needs to manually control or exit
                        elif target_action == "continue":
                            logger.warning(
                                "▶️  ACTION: continue - Auto-skipping (savestate preserved!)"
                            )
                            # Continue hunting automatically
                    else:
                        # Target match or no target mode - this is the shiny we want!
                        if target_pokemon:
                            logger.info(f"🎯 TARGET MATCH! {pokemon_name} found!")
                else:
                    manager.add_input_to_queue(emulator_id, "touch", x=128, y=180)

                # Reset when back to search
                if hunter.current_state.id == "search":
                    battle_start_frame_list[emulator_id] = -1
                    battle_ready_frame_list[emulator_id] = -1

    # Save logs at the end
    if len(shiny_log) > 0:
        log_file = Path("shiny_log.json")
        with open(log_file, "w") as f:
            json.dump(shiny_log, f, indent=2)
        logger.info(f"💾 Saved shiny log to: {log_file} ({len(shiny_log)} entries)")

    if len(skipped_log) > 0:
        skipped_file = Path("skipped_shinies.json")
        with open(skipped_file, "w") as f:
            json.dump(skipped_log, f, indent=2)
        logger.info(f"💾 Saved skipped shinies to: {skipped_file} ({len(skipped_log)} entries)")
        logger.warning("⚠️  Check skipped_shinies.json for non-target shinies that were skipped!")


def launch_single_mode(
    rom_path: Path,
    save_path: Path | None,
    randomize_start: bool,
    target_pokemon: str | None = None,
    target_action: str = "alert",
):
    """Launch traditional single-emulator mode.

    Args:
        rom_path: Path to ROM file
        save_path: Path to save state file (optional)
        randomize_start: Whether to randomize starting frame
        target_pokemon: Optional target Pokemon name for target mode
        target_action: Action for non-target shinies ('alert', 'pause', 'continue')
    """
    logger.info("=" * 60)
    logger.info("🎮 PyShiny Hunter - Single Mode")
    logger.info("=" * 60)
    logger.info(f"ROM: {rom_path}")
    logger.info(f"Save State: {save_path}")
    logger.info("=" * 60)

    manager = PyDeSmuMEManager(rom_path, save_path, randomize_start)
    single_mode_worker(manager, target_pokemon, target_action)
