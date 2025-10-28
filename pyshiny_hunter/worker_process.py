"""Multi-process worker module for headless emulator instances.

This module implements the worker process that runs headless emulators
and streams screenshots to the main GUI process via multiprocessing Queue.
"""

from __future__ import annotations

import datetime
import json
import multiprocessing as mp
import random
import time
import traceback
from multiprocessing.managers import DictProxy, ListProxy
from multiprocessing.synchronize import Barrier
from pathlib import Path
from typing import Any

from pyshiny_hunter import config
from pyshiny_hunter.black2_hunter import Black2Hunter
from pyshiny_hunter.module_logger import logger
from pyshiny_hunter.py_desmume_manager import PyDeSmuMEManager


def build_complete_keymask(pressed_keys: set[str]) -> int:
    """Build complete NDS input bitmask from set of pressed key names.

    This is the CORRECT way to handle input according to DeSmuME architecture analysis.
    Native DeSmuME always sends COMPLETE button state, never additive operations.

    Args:
        pressed_keys: Set of key names (e.g., {"KEY_UP", "KEY_A"})

    Returns:
        Complete 16-bit bitmask representing ALL buttons (0-15)
        Pressed buttons have their bit set to 1, released buttons are 0.

    Reference: DeSmuME_INPUT_ANALYSIS.md - Bit positions from NDSSystem.cpp
    """
    # Bit positions from DeSmuME source (ctrlssdl.h and NDSSystem.cpp)
    KEY_TO_BIT = {
        "KEY_A": 0,
        "KEY_B": 1,
        "KEY_SELECT": 2,
        "KEY_START": 3,
        "KEY_RIGHT": 4,
        "KEY_LEFT": 5,
        "KEY_UP": 6,
        "KEY_DOWN": 7,
        "KEY_R": 8,  # R shoulder
        "KEY_L": 9,  # L shoulder
        "KEY_X": 10,
        "KEY_Y": 11,
        "KEY_DEBUG": 12,
        # Bit 13 unused
        "KEY_LID": 14,
        # Bit 15 unused
    }

    mask = 0
    for key_name in pressed_keys:
        if key_name in KEY_TO_BIT:
            mask |= 1 << KEY_TO_BIT[key_name]

    return mask


def headless_worker(
    worker_id: int,
    rom_path: Path,
    save_path: Path | None,
    randomize_start: bool,
    screenshot_queue: mp.Queue[Any],
    control_queue: mp.Queue[Any],
    shiny_log: ListProxy[Any],
    encounter_stats: DictProxy[Any, Any],
    desync_barrier: Barrier | None = None,
    init_status: DictProxy[Any, Any] | None = None,
    stats_lock: Any | None = None,
) -> None:
    """Headless worker process running emulator and streaming screenshots.

    Args:
        worker_id: Unique identifier for this worker
        rom_path: Path to ROM file
        save_path: Path to save state file
        randomize_start: Whether to randomize starting frame
        screenshot_queue: Queue for sending screenshots to main GUI
        control_queue: Queue for receiving control commands (future use)
        shiny_log: Shared list for centralized shiny logging
        encounter_stats: Shared dict for aggregate encounter statistics
        desync_barrier: Optional multiprocessing.Barrier for synchronizing desync completion
        init_status: Shared dict for reporting initialization progress to GUI
        stats_lock: Optional lock for thread-safe encounter stats updates
    """
    try:
        # Report status: Loading emulator
        if init_status is not None:
            init_status[worker_id] = "loading"

        logger.info(f"[Worker {worker_id}] Starting headless emulator...")

        # Create headless manager (no GUI)
        # NOTE: randomize_start is now IGNORED in PyDeSmuMEManager for multi-process mode
        # We apply RNG desync manually here AFTER emulator creation
        manager = PyDeSmuMEManager(
            rom_path, save_path, randomize_start=False, num_emulators=1, headless=True
        )

        # Apply RNG desynchronization if requested
        # CRITICAL: This MUST happen inside worker process, not in main process!
        # Each worker process has its own emulator instance - offsetting in main process has no effect
        if randomize_start:
            # Report status: Desyncing RNG
            if init_status is not None:
                init_status[worker_id] = "desyncing"

            emulator = manager.get_emulators()[0]

            # Hybrid desync: progressive base + random jitter
            base_offset = worker_id * config.WORKER_RNG_BASE_OFFSET_FRAMES
            jitter = random.randrange(0, config.WORKER_RNG_JITTER_FRAMES + 1)  # nosec B311
            total_offset = base_offset + jitter

            # Advance emulator RNG state
            for _ in range(total_offset):
                emulator.emulator.cycle()

            save_type = save_path.suffix.upper()[1:] if save_path else "NO_SAVE"
            logger.info(
                f"[Worker {worker_id}] ({save_type}) RNG desync offset = {total_offset} frames "
                f"(base: {base_offset} + jitter: {jitter}) = {total_offset / 60:.2f}s - "
                f"guaranteed unique RNG state"
            )

        # Report status: Loading OCR models
        if init_status is not None:
            init_status[worker_id] = "loading_ocr"

        # Create hunter (this starts loading EasyOCR in background)
        hunter = Black2Hunter()

        # Wait for EasyOCR to finish loading before barrier
        # This ensures clean startup without background loading interfering with main loop
        _ = hunter.enhanced_ocr.reader  # Access reader to wait for background load

        # Wait for all workers to complete OCR loading before starting main loop
        # This ensures GUI shows all emulator streams simultaneously (synchronized start)
        if desync_barrier is not None:
            # Report status: Waiting for other workers
            if init_status is not None:
                init_status[worker_id] = "waiting"

            logger.info(f"[Worker {worker_id}] OCR loaded, waiting for other workers...")
            try:
                desync_barrier.wait(timeout=30)  # Max 30s wait for all workers
            except Exception as e:
                logger.error(
                    f"[Worker {worker_id}] Barrier timeout or error: {e}. "
                    f"One or more workers may have failed to initialize."
                )
                # Update status to show failure
                if init_status is not None:
                    init_status[worker_id] = f"failed: {str(e)[:50]}"
                raise RuntimeError(
                    f"Worker {worker_id} failed to synchronize with other workers"
                ) from e
            logger.info(f"[Worker {worker_id}] All workers ready, starting synchronized!")

        battle_ready_frame = -1
        battle_start_frame = -1

        # Manual control state
        paused = False  # When True, hunter state machine is paused for manual control
        active_keys: set[str] = set()  # Track currently pressed keys for manual control

        # Report status: Ready to start
        if init_status is not None:
            init_status[worker_id] = "ready"

        logger.info(f"[Worker {worker_id}] Initialized, starting main loop...")

        frame_count = 0
        last_encounters: dict[str, int] = {}  # Track last known encounter dict for change detection

        while manager.update_frame(hunter.get_encounters()):
            # Process control commands from GUI
            # Monitor queue size for debugging
            queue_size = control_queue.qsize()
            if queue_size > 10:
                logger.warning(f"[Worker {worker_id}] Control queue backing up: {queue_size} items")

            while not control_queue.empty():
                try:
                    command = control_queue.get_nowait()
                    action = command.get("action")
                    logger.debug(f"[Worker {worker_id}] Received command: action={action}")

                    if action == "pause":
                        paused = True
                        active_keys.clear()  # Clear any held keys when pausing
                        logger.info(
                            f"[Worker {worker_id}] 🎮 Manual control activated - hunter paused"
                        )
                    elif action == "resume":
                        paused = False
                        active_keys.clear()  # Clear any held keys when resuming
                        logger.info(
                            f"[Worker {worker_id}] ▶️ Manual control deactivated - resuming hunter"
                        )
                    elif action == "input":
                        input_type = command.get("type")

                        if input_type == "key_state":
                            # Replace active keys with current state from GUI
                            # CRITICAL: Must modify existing set, not create new local variable!
                            keys_received = command.get("keys", [])
                            active_keys.clear()
                            active_keys.update(keys_received)
                            logger.debug(
                                f"[Worker {worker_id}] Updated active_keys: {list(active_keys)} "
                                f"(received {len(keys_received)} keys)"
                            )
                        elif input_type == "touch":
                            # Touch is immediate, not stateful
                            x = command.get("x")
                            y = command.get("y")
                            if x is not None and y is not None:
                                manager.add_input_to_queue(0, "touch", x=x, y=y)
                except Exception as e:  # nosec B110
                    logger.error(
                        f"[Worker {worker_id}] Error processing command: {e}", exc_info=True
                    )

            # Apply all active keys to emulator in manual control mode
            # CORRECT APPROACH per DeSmuME analysis: Send COMPLETE state, not additive!
            emulator = manager.get_emulators()[0]

            if paused:
                # Build COMPLETE keymask representing ALL 14 buttons (pressed + released)
                # This is how native DeSmuME works - always send complete state!
                complete_mask = build_complete_keymask(active_keys)

                # Set COMPLETE button state in one atomic operation
                # This eliminates race conditions and ensures immediate response
                emulator.emulator.input.keypad_update(complete_mask)

                # Debug logging
                if active_keys:
                    logger.debug(
                        f"[Worker {worker_id}] Complete state: {len(active_keys)} keys pressed: "
                        f"{list(active_keys)} (mask=0x{complete_mask:04X})"
                    )
                elif frame_count % 60 == 0:  # Log once per second when no keys
                    logger.debug(
                        f"[Worker {worker_id}] Complete state: all keys released (mask=0x0000)"
                    )
            top_screen, bottom_screen = emulator.get_screens()

            # Update shared encounter stats when new encounters detected
            current_encounters = hunter.get_encounters()
            for pokemon, count in current_encounters.items():
                last_count = last_encounters.get(pokemon, 0)
                if count > last_count:
                    # New encounter(s) of this pokemon!
                    new_encounters = count - last_count

                    # Update stats with lock to prevent race conditions
                    if stats_lock is not None:
                        with stats_lock:
                            # Update total encounters
                            encounter_stats["total_encounters"] = (
                                encounter_stats.get("total_encounters", 0) + new_encounters
                            )

                            # Update per-Pokemon counts
                            if "pokemon_counts" not in encounter_stats:
                                encounter_stats["pokemon_counts"] = {}
                            pokemon_counts = dict(encounter_stats.get("pokemon_counts", {}))
                            pokemon_counts[pokemon] = (
                                pokemon_counts.get(pokemon, 0) + new_encounters
                            )
                            encounter_stats["pokemon_counts"] = pokemon_counts

                            # Update worker contribution
                            if "worker_contributions" not in encounter_stats:
                                encounter_stats["worker_contributions"] = {}
                            worker_contribs = dict(encounter_stats.get("worker_contributions", {}))
                            worker_contribs[worker_id] = sum(current_encounters.values())
                            encounter_stats["worker_contributions"] = worker_contribs
                    else:
                        # Fallback: no lock provided (backward compatibility)
                        encounter_stats["total_encounters"] = (
                            encounter_stats.get("total_encounters", 0) + new_encounters
                        )
                        if "pokemon_counts" not in encounter_stats:
                            encounter_stats["pokemon_counts"] = {}
                        pokemon_counts = dict(encounter_stats.get("pokemon_counts", {}))
                        pokemon_counts[pokemon] = pokemon_counts.get(pokemon, 0) + new_encounters
                        encounter_stats["pokemon_counts"] = pokemon_counts
                        if "worker_contributions" not in encounter_stats:
                            encounter_stats["worker_contributions"] = {}
                        worker_contribs = dict(encounter_stats.get("worker_contributions", {}))
                        worker_contribs[worker_id] = sum(current_encounters.values())
                        encounter_stats["worker_contributions"] = worker_contribs

            last_encounters = dict(current_encounters)

            # State machine logic - skip if paused (manual control active)
            if not paused:
                if hunter.current_state.id == "search":
                    hunter.searching_pokemon(top_screen, bottom_screen)

                    # Automated movement
                    if emulator.frame % 10 == 0:
                        manager.add_input_to_queue(0, "key", key="KEY_LEFT")
                    elif emulator.frame % 10 == 5:
                        manager.add_input_to_queue(0, "key", key="KEY_RIGHT")

                elif hunter.current_state.id == "check_if_shiny":
                    hunter.checking_shiny(top_screen, bottom_screen)
                    if battle_start_frame == -1:
                        battle_start_frame = emulator.frame

                elif hunter.current_state.id == "pre_battle_animation":
                    hunter.waiting_for_battle_start(top_screen, bottom_screen)
                    if battle_ready_frame == -1:
                        battle_ready_frame = emulator.frame

                elif hunter.current_state.id == "in_battle":
                    hunter.running_away(battle_ready_frame - battle_start_frame)

                    if hunter.current_state.id == "found":
                        # SHINY FOUND!
                        logger.info("=" * 60)
                        logger.info(f"[Worker {worker_id}] ⭐ SHINY POKEMON FOUND! ⭐")
                        logger.info("=" * 60)

                        save_name = f"roms/states/black2/shiny_worker{worker_id}_{battle_ready_frame - battle_start_frame}.dst"
                        emulator.emulator.savestate.save_file(save_name)
                        logger.info(f"[Worker {worker_id}] Saved to: {save_name}")

                        # Log to centralized shiny log
                        shiny_entry = {
                            "worker_id": worker_id,
                            "timestamp": datetime.datetime.now().isoformat(),
                            "frame_diff": battle_ready_frame - battle_start_frame,
                            "save_file": save_name,
                            "total_encounters": sum(hunter.get_encounters().values()),
                            "encounters": dict(hunter.get_encounters()),
                        }
                        shiny_log.append(shiny_entry)
                        logger.info(f"[Worker {worker_id}] Logged to centralized shiny log")
                    else:
                        manager.add_input_to_queue(0, "touch", x=128, y=180)

                    # Reset frame counters when back to search
                    if hunter.current_state.id == "search":
                        battle_start_frame = -1
                        battle_ready_frame = -1

            # Stream screenshot to GUI every frame
            screenshot = emulator.take_screenshot()

            worker_data = {
                "worker_id": worker_id,
                "screenshot": screenshot,
                "state": hunter.current_state.id,
                "encounters": dict(hunter.get_encounters()),
                "frame": emulator.frame,
                "total_encounters": sum(hunter.get_encounters().values()),
                "fps": emulator.get_fps(),
                "paused": paused,  # Manual control state
            }

            # Non-blocking put (drop frame if queue full to avoid backup)
            try:
                screenshot_queue.put_nowait(worker_data)
            except Exception:  # nosec B110 - Intentionally dropping frames if queue full
                pass  # Queue full, skip this frame

            frame_count += 1

    except KeyboardInterrupt:
        logger.info(f"[Worker {worker_id}] Interrupted by user")
    except Exception as e:
        logger.error(f"[Worker {worker_id}] Error: {e}")
        traceback.print_exc()
    finally:
        logger.info(f"[Worker {worker_id}] Shutting down...")


def launch_multi_mode(
    rom_path: Path,
    save_path: Path | None,
    num_workers: int,
    randomize_start: bool,
) -> None:
    """Launch multi-process mode with unified GUI.

    Args:
        rom_path: Path to ROM file
        save_path: Path to save state file (optional)
        num_workers: Number of worker processes to spawn
        randomize_start: Whether to randomize starting frame for each worker
    """
    logger.info("=" * 60)
    logger.info("🎮 PyShiny Hunter - Multi-Process Mode")
    logger.info("=" * 60)
    logger.info(f"ROM: {rom_path}")
    logger.info(f"Save State: {save_path}")
    logger.info(f"Workers: {num_workers}")
    logger.info(f"Randomize Start: {randomize_start}")
    logger.info("=" * 60)

    # Create shared data structures
    manager = mp.Manager()
    screenshot_queue: mp.Queue[Any] = mp.Queue(
        maxsize=num_workers * 10
    )  # Buffer 10 frames per worker
    control_queues: list[mp.Queue[Any]] = [mp.Queue() for _ in range(num_workers)]

    # Shared shiny log and encounter statistics
    shiny_log: ListProxy[Any] = manager.list()
    encounter_stats: DictProxy[Any, Any] = manager.dict(
        {
            "total_encounters": 0,
            "pokemon_counts": manager.dict(),
            "worker_contributions": manager.dict(),
            "start_time": datetime.datetime.now().isoformat(),
        }
    )

    # Shared initialization status for GUI progress display
    # Each worker reports: "loading" → "desyncing" → "waiting" → "ready"
    init_status: DictProxy[Any, Any] = manager.dict()

    # Lock for thread-safe encounter stats updates (prevents race conditions)
    stats_lock = manager.Lock()

    # Barrier for synchronizing desync completion
    # All workers wait at barrier after desync, then start streaming simultaneously
    desync_barrier = mp.Barrier(num_workers) if randomize_start else None

    # Launch worker processes
    processes = []
    for i in range(num_workers):
        p = mp.Process(
            target=headless_worker,
            args=(
                i,
                rom_path,
                save_path,
                randomize_start,
                screenshot_queue,
                control_queues[i],
                shiny_log,
                encounter_stats,
                desync_barrier,
                init_status,
                stats_lock,
            ),
        )
        p.start()
        processes.append(p)
        # Stagger worker startup to prevent simultaneous file I/O operations
        # when loading the same ROM/save files (prevents potential file locking issues)
        time.sleep(0.1)

    logger.info(f"\n✅ Launched {num_workers} worker processes!")
    logger.info("Starting unified GUI...\n")

    try:
        # Import here to avoid circular imports
        from pyshiny_hunter.gui_process import unified_gui_main_process

        # Run main GUI with initialization status tracking
        unified_gui_main_process(
            num_workers, screenshot_queue, control_queues, shiny_log, encounter_stats, init_status
        )
    except KeyboardInterrupt:
        logger.info("\n🛑 Stopping all workers...")
    finally:
        # Terminate all workers
        for p in processes:
            p.terminate()

        # Wait for cleanup
        for p in processes:
            p.join(timeout=5)

        # Save shiny log to file
        if len(shiny_log) > 0:
            log_file = Path("shiny_log.json")
            with open(log_file, "w") as f:
                json.dump(list(shiny_log), f, indent=2)
            logger.info(f"\n💾 Saved shiny log to: {log_file} ({len(shiny_log)} entries)")

        # Save encounter stats to file
        total_encounters = int(encounter_stats.get("total_encounters", 0))
        if total_encounters > 0:
            stats_file = Path("encounter_stats.json")
            pokemon_counts_dict = dict(encounter_stats.get("pokemon_counts", {}))
            worker_contribs_dict = dict(encounter_stats.get("worker_contributions", {}))
            stats_data = {
                "total_encounters": total_encounters,
                "pokemon_counts": pokemon_counts_dict,
                "worker_contributions": {str(k): v for k, v in worker_contribs_dict.items()},
                "start_time": encounter_stats.get("start_time"),
                "end_time": datetime.datetime.now().isoformat(),
            }

            with open(stats_file, "w") as f:
                json.dump(stats_data, f, indent=2)
            logger.info(f"💾 Saved encounter stats to: {stats_file}")

        logger.info("\n👋 All workers stopped. Happy hunting!")
