"""Multi-process worker module for headless emulator instances.

This module implements the worker process that runs headless emulators
and streams screenshots to the main GUI process via multiprocessing Queue.
"""

import datetime
import json
import multiprocessing as mp
import time
import traceback
from pathlib import Path
from typing import Optional

from pyshiny_hunter.black2_hunter import Black2Hunter
from pyshiny_hunter.module_logger import logger
from pyshiny_hunter.py_desmume_manager import PyDeSmuMEManager


def headless_worker(
    worker_id: int,
    rom_path: Path,
    save_path: Optional[Path],
    randomize_start: bool,
    screenshot_queue: mp.Queue,
    control_queue: mp.Queue,
    shiny_log: list,
    encounter_stats: dict,
):
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
    """
    try:
        logger.info(f"[Worker {worker_id}] Starting headless emulator...")

        # Create headless manager (no GUI)
        manager = PyDeSmuMEManager(
            rom_path, save_path, randomize_start, num_emulators=1, headless=True
        )

        # Create hunter
        hunter = Black2Hunter()
        battle_ready_frame = -1
        battle_start_frame = -1

        logger.info(f"[Worker {worker_id}] Initialized, starting main loop...")

        frame_count = 0
        last_encounters = {}  # Track last known encounter dict for change detection

        while manager.update_frame(hunter.get_encounters()):
            emulator = manager.get_emulators()[0]
            top_screen, bottom_screen = emulator.get_screens()

            # Update shared encounter stats when new encounters detected
            current_encounters = hunter.get_encounters()
            for pokemon, count in current_encounters.items():
                last_count = last_encounters.get(pokemon, 0)
                if count > last_count:
                    # New encounter(s) of this pokemon!
                    new_encounters = count - last_count

                    # Update total encounters
                    encounter_stats["total_encounters"] = (
                        encounter_stats.get("total_encounters", 0) + new_encounters
                    )

                    # Update per-Pokemon counts
                    if "pokemon_counts" not in encounter_stats:
                        encounter_stats["pokemon_counts"] = {}
                    pokemon_counts = dict(encounter_stats.get("pokemon_counts", {}))
                    pokemon_counts[pokemon] = pokemon_counts.get(pokemon, 0) + new_encounters
                    encounter_stats["pokemon_counts"] = pokemon_counts

                    # Update worker contribution
                    if "worker_contributions" not in encounter_stats:
                        encounter_stats["worker_contributions"] = {}
                    worker_contribs = dict(encounter_stats.get("worker_contributions", {}))
                    worker_contribs[worker_id] = sum(current_encounters.values())
                    encounter_stats["worker_contributions"] = worker_contribs

            last_encounters = dict(current_encounters)

            # State machine logic
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
    save_path: Optional[Path],
    num_workers: int,
    randomize_start: bool,
):
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
    screenshot_queue = mp.Queue(maxsize=num_workers * 10)  # Buffer 10 frames per worker
    control_queues = [mp.Queue() for _ in range(num_workers)]

    # Shared shiny log and encounter statistics
    shiny_log = manager.list()
    encounter_stats = manager.dict(
        {
            "total_encounters": 0,
            "pokemon_counts": manager.dict(),
            "worker_contributions": manager.dict(),
            "start_time": datetime.datetime.now().isoformat(),
        }
    )

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
            ),
        )
        p.start()
        processes.append(p)
        time.sleep(0.5)  # Stagger startup

    logger.info(f"\n✅ Launched {num_workers} worker processes!")
    logger.info("Starting unified GUI...\n")

    try:
        # Import here to avoid circular imports
        from pyshiny_hunter.gui_process import unified_gui_main_process

        # Run main GUI
        unified_gui_main_process(
            num_workers, screenshot_queue, control_queues, shiny_log, encounter_stats
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
        if encounter_stats.get("total_encounters", 0) > 0:
            stats_file = Path("encounter_stats.json")
            stats_data = {
                "total_encounters": encounter_stats.get("total_encounters", 0),
                "pokemon_counts": dict(encounter_stats.get("pokemon_counts", {})),
                "worker_contributions": {
                    str(k): v for k, v in encounter_stats.get("worker_contributions", {}).items()
                },
                "start_time": encounter_stats.get("start_time"),
                "end_time": datetime.datetime.now().isoformat(),
            }

            with open(stats_file, "w") as f:
                json.dump(stats_data, f, indent=2)
            logger.info(f"💾 Saved encounter stats to: {stats_file}")

        logger.info("\n👋 All workers stopped. Happy hunting!")
