"""
PyShiny Hunter - Multi-Process GUI Launcher

This script supports two modes:
1. Single mode: Traditional single emulator with GUI (default)
2. Multi mode: Multiple headless worker processes with unified GUI display

Architecture (Multi-mode):
- Main process: Unified GUI displaying all worker streams
- Worker processes: Headless emulators streaming screenshots via Queue
"""

import argparse
import multiprocessing as mp
import sys
import time
from pathlib import Path
from queue import Empty
from typing import Optional

import glfw
import imgui
import numpy as np
import OpenGL.GL as gl
from imgui.integrations.glfw import GlfwRenderer

# Fix Windows console encoding for emoji support
if sys.platform == "win32":
    import os

    os.system("chcp 65001 > nul")  # nosec B605 B607 - Safe Windows console command
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Add the parent directory of pyshiny_hunter to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from pyshiny_hunter import config
from pyshiny_hunter.black2_hunter import Black2Hunter
from pyshiny_hunter.py_desmume_manager import PyDeSmuMEManager
from pyshiny_hunter.utils.gui_utils import (
    glfw_init,
    opengl_create_texture,
    opengl_update_texture,
)


# ==============================================================================
# SINGLE MODE (Original Implementation)
# ==============================================================================


def single_mode_worker(manager: PyDeSmuMEManager):
    """Original single-emulator mode with integrated GUI."""
    num_emulators = len(manager.get_emulators())
    hunters = [Black2Hunter() for _ in range(num_emulators)]
    battle_ready_frame_list = [-1] * num_emulators
    battle_start_frame_list = [-1] * num_emulators

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
                    print("SHINY POKEMON!!!!!!!!!!!!")
                    emulator.emulator.savestate.save_file(
                        f"roms/states/black2/shiny_{battle_ready_frame - battle_start_frame}.dst"
                    )
                else:
                    manager.add_input_to_queue(emulator_id, "touch", x=128, y=180)

                # Reset when back to search
                if hunter.current_state.id == "search":
                    battle_start_frame_list[emulator_id] = -1
                    battle_ready_frame_list[emulator_id] = -1


# ==============================================================================
# MULTI MODE (New Multi-Process Implementation)
# ==============================================================================


def headless_worker(
    worker_id: int,
    rom_path: Path,
    save_path: Optional[Path],
    randomize_start: bool,
    screenshot_queue: mp.Queue,
    control_queue: mp.Queue,
):
    """Headless worker process running emulator and streaming screenshots.

    Args:
        worker_id: Unique identifier for this worker
        rom_path: Path to ROM file
        save_path: Path to save state file
        randomize_start: Whether to randomize starting frame
        screenshot_queue: Queue for sending screenshots to main GUI
        control_queue: Queue for receiving control commands (future use)
    """
    try:
        print(f"[Worker {worker_id}] Starting headless emulator...")

        # Create headless manager (no GUI)
        manager = PyDeSmuMEManager(
            rom_path, save_path, randomize_start, num_emulators=1, headless=True
        )

        # Create hunter
        hunter = Black2Hunter()
        battle_ready_frame = -1
        battle_start_frame = -1

        print(f"[Worker {worker_id}] Initialized, starting main loop...")

        frame_count = 0
        while manager.update_frame(hunter.get_encounters()):
            emulator = manager.get_emulators()[0]
            top_screen, bottom_screen = emulator.get_screens()

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
                    print(f"\n{'='*60}")
                    print(f"[Worker {worker_id}] ⭐ SHINY POKEMON FOUND! ⭐")
                    print(f"{'='*60}\n")

                    save_name = f"roms/states/black2/shiny_worker{worker_id}_{battle_ready_frame - battle_start_frame}.dst"
                    emulator.emulator.savestate.save_file(save_name)
                    print(f"[Worker {worker_id}] Saved to: {save_name}")
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
            }

            # Non-blocking put (drop frame if queue full to avoid backup)
            try:
                screenshot_queue.put_nowait(worker_data)
            except Exception:  # nosec B110 - Intentionally dropping frames if queue full
                pass  # Queue full, skip this frame

            frame_count += 1

    except KeyboardInterrupt:
        print(f"[Worker {worker_id}] Interrupted by user")
    except Exception as e:
        print(f"[Worker {worker_id}] Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        print(f"[Worker {worker_id}] Shutting down...")


def unified_gui_main_process(
    num_workers: int,
    screenshot_queue: mp.Queue,
    control_queues: list,
):
    """Main GUI process displaying all worker streams.

    Args:
        num_workers: Number of worker processes
        screenshot_queue: Queue receiving screenshots from workers
        control_queues: Queues for sending commands to workers (future use)
    """
    print(f"[Main GUI] Initializing unified GUI for {num_workers} workers...")

    # Initialize ImGui
    imgui.create_context()
    window_width = 280 * num_workers  # Fit all workers side-by-side
    window = glfw_init("PyShiny Hunter - Multi Mode", window_width, 550)
    renderer = GlfwRenderer(window)

    # Create textures for each worker
    texture_ids = [opengl_create_texture(256, 384) for _ in range(num_workers)]

    # Worker state tracking
    worker_states = {}
    for i in range(num_workers):
        worker_states[i] = {
            "screenshot": np.zeros((384, 256, 4), dtype=np.uint8),
            "state": "Initializing...",
            "encounters": {},
            "frame": 0,
            "total_encounters": 0,
            "last_update": time.time(),
        }

    print("[Main GUI] GUI initialized, starting render loop...")

    try:
        while not glfw.window_should_close(window):
            glfw.poll_events()
            renderer.process_inputs()

            # Process all available screenshot updates from workers
            updates_processed = 0
            while updates_processed < 100:  # Limit per frame to avoid blocking
                try:
                    data = screenshot_queue.get_nowait()
                    worker_id = data["worker_id"]

                    if worker_id in worker_states:
                        worker_states[worker_id].update(
                            {
                                "screenshot": data["screenshot"],
                                "state": data["state"],
                                "encounters": data["encounters"],
                                "frame": data["frame"],
                                "total_encounters": data["total_encounters"],
                                "last_update": time.time(),
                            }
                        )

                        # Update OpenGL texture
                        opengl_update_texture(data["screenshot"], texture_ids[worker_id])

                    updates_processed += 1
                except Empty:
                    break

            # Render GUI
            imgui.new_frame()

            gl.glClearColor(0.1, 0.1, 0.1, 1)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)

            # Display each worker in its own panel
            for worker_id in range(num_workers):
                state = worker_states[worker_id]

                with imgui.begin(f"Worker {worker_id}"):
                    # Display emulator screen
                    imgui.image(texture_ids[worker_id], 256, 384)

                    # Display stats
                    imgui.separator()
                    imgui.text(f"State: {state['state']}")
                    imgui.text(f"Frame: {state['frame']}")
                    imgui.text(f"Total Encounters: {state['total_encounters']}")

                    # Check if worker is alive
                    time_since_update = time.time() - state["last_update"]
                    if time_since_update > 2.0:
                        imgui.text_colored("Status: STALLED", 1.0, 0.0, 0.0)
                    else:
                        imgui.text_colored("Status: Running", 0.0, 1.0, 0.0)

                    imgui.separator()

                    # Show encounter breakdown
                    if state["encounters"]:
                        imgui.text("Encounters:")
                        for pokemon, count in state["encounters"].items():
                            imgui.text(f"  {pokemon}: {count}")

            # Aggregate stats panel
            with imgui.begin("Aggregate Stats"):
                total_encounters = sum(s["total_encounters"] for s in worker_states.values())
                imgui.text(f"Total Encounters (All Workers): {total_encounters}")

                imgui.separator()
                imgui.text(f"Active Workers: {num_workers}")

                shiny_odds = 1.0 / config.SHINY_ODDS_DENOMINATOR
                imgui.text(f"Shiny odds per encounter: {shiny_odds * 100.0:.3f}%")

                # Probability of at least one shiny across all encounters
                if total_encounters > 0:
                    prob_at_least_one = (1 - (1 - shiny_odds) ** total_encounters) * 100
                    imgui.text(f"Probability of ≥1 shiny: {prob_at_least_one:.2f}%")

                imgui.separator()
                imgui.text(f"FPS: {1 / imgui.get_io().delta_time:.1f}")

            imgui.render()
            renderer.render(imgui.get_draw_data())
            glfw.swap_buffers(window)

    except KeyboardInterrupt:
        print("\n[Main GUI] Interrupted by user")
    finally:
        print("[Main GUI] Shutting down...")
        renderer.shutdown()
        glfw.terminate()


def launch_multi_mode(
    rom_path: Path,
    save_path: Optional[Path],
    num_workers: int,
    randomize_start: bool,
):
    """Launch multi-process mode with unified GUI."""
    print("=" * 60)
    print("🎮 PyShiny Hunter - Multi-Process Mode")
    print("=" * 60)
    print(f"ROM: {rom_path}")
    print(f"Save State: {save_path}")
    print(f"Workers: {num_workers}")
    print(f"Randomize Start: {randomize_start}")
    print("=" * 60 + "\n")

    # Create shared queues
    screenshot_queue = mp.Queue(maxsize=num_workers * 10)  # Buffer 10 frames per worker
    control_queues = [mp.Queue() for _ in range(num_workers)]

    # Launch worker processes
    processes = []
    for i in range(num_workers):
        p = mp.Process(
            target=headless_worker,
            args=(i, rom_path, save_path, randomize_start, screenshot_queue, control_queues[i]),
        )
        p.start()
        processes.append(p)
        time.sleep(0.5)  # Stagger startup

    print(f"\n✅ Launched {num_workers} worker processes!")
    print("Starting unified GUI...\n")

    try:
        # Run main GUI
        unified_gui_main_process(num_workers, screenshot_queue, control_queues)
    except KeyboardInterrupt:
        print("\n🛑 Stopping all workers...")
    finally:
        # Terminate all workers
        for p in processes:
            p.terminate()

        # Wait for cleanup
        for p in processes:
            p.join(timeout=5)

        print("\n👋 All workers stopped. Happy hunting!")


def launch_single_mode(rom_path: Path, save_path: Optional[Path], randomize_start: bool):
    """Launch traditional single-emulator mode."""
    print("=" * 60)
    print("🎮 PyShiny Hunter - Single Mode")
    print("=" * 60)
    print(f"ROM: {rom_path}")
    print(f"Save State: {save_path}")
    print("=" * 60 + "\n")

    manager = PyDeSmuMEManager(rom_path, save_path, randomize_start)
    single_mode_worker(manager)


# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="PyShiny Hunter - Automated shiny Pokemon hunting with DeSmuME"
    )
    parser.add_argument("rom", type=str, help="Path to the .nds ROM file")
    parser.add_argument(
        "--sav", type=str, default=None, help="Path to the .sav save file (optional)"
    )
    parser.add_argument(
        "--state",
        type=str,
        default=None,
        help="Path to the .dst save state file (optional)",
    )
    parser.add_argument("--randomize-start", action="store_true", help="Randomize start frame")
    parser.add_argument(
        "--num-workers",
        type=int,
        default=1,
        help="Number of worker processes (default: 1 = single mode)",
    )

    args = parser.parse_args()

    rom_path = Path(args.rom)
    save_path = Path(args.state) if args.state else Path(args.sav) if args.sav else None

    # Choose mode based on num_workers
    if args.num_workers > 1:
        launch_multi_mode(rom_path, save_path, args.num_workers, args.randomize_start)
    else:
        launch_single_mode(rom_path, save_path, args.randomize_start)


if __name__ == "__main__":
    # Required for Windows multiprocessing
    mp.freeze_support()
    main()
