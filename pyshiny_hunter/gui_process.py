"""Main GUI process for displaying multiple worker streams.

This module implements the unified GUI that displays all worker emulator
streams in a single window with aggregate statistics and shiny log.
"""

import datetime
import multiprocessing as mp
import time
from queue import Empty

import glfw
import imgui
import numpy as np
import OpenGL.GL as gl
from imgui.integrations.glfw import GlfwRenderer

from pyshiny_hunter import config
from pyshiny_hunter.module_logger import logger
from pyshiny_hunter.utils.gui_utils import (
    glfw_init,
    opengl_create_texture,
    opengl_update_texture,
)


def unified_gui_main_process(
    num_workers: int,
    screenshot_queue: mp.Queue,
    control_queues: list,
    shiny_log: list,
    encounter_stats: dict,
):
    """Main GUI process displaying all worker streams.

    Args:
        num_workers: Number of worker processes
        screenshot_queue: Queue receiving screenshots from workers
        control_queues: Queues for sending commands to workers (future use)
        shiny_log: Shared list for centralized shiny logging
        encounter_stats: Shared dict for aggregate encounter statistics
    """
    logger.info(f"[Main GUI] Initializing unified GUI for {num_workers} workers...")

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

    logger.info("[Main GUI] GUI initialized, starting render loop...")

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

            # Aggregate stats panel (ENHANCED with shared encounter stats)
            with imgui.begin("Aggregate Stats"):
                # Use shared encounter stats instead of per-worker sum
                total_encounters = encounter_stats.get("total_encounters", 0)
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

                # Encounters per minute
                start_time_str = encounter_stats.get("start_time")
                if start_time_str and total_encounters > 0:
                    start_time = datetime.datetime.fromisoformat(start_time_str)
                    elapsed_minutes = (datetime.datetime.now() - start_time).total_seconds() / 60.0
                    if elapsed_minutes > 0:
                        encounters_per_min = total_encounters / elapsed_minutes
                        imgui.text(f"Encounters/min: {encounters_per_min:.1f}")

                imgui.separator()
                imgui.text(f"FPS: {1 / imgui.get_io().delta_time:.1f}")

                imgui.separator()

                # Per-Pokemon breakdown (from shared stats)
                imgui.text("Pokemon Breakdown:")
                pokemon_counts = dict(encounter_stats.get("pokemon_counts", {}))
                if pokemon_counts:
                    for pokemon, count in sorted(
                        pokemon_counts.items(), key=lambda x: x[1], reverse=True
                    ):
                        imgui.text(f"  {pokemon}: {count}")
                else:
                    imgui.text_colored("  No encounters yet...", 0.7, 0.7, 0.7)

                imgui.separator()

                # Worker contributions
                imgui.text("Worker Contributions:")
                worker_contribs = dict(encounter_stats.get("worker_contributions", {}))
                if worker_contribs and total_encounters > 0:
                    for worker_id in sorted(worker_contribs.keys()):
                        count = worker_contribs[worker_id]
                        percentage = (count / total_encounters * 100) if total_encounters > 0 else 0
                        imgui.text(f"  Worker {worker_id}: {count} ({percentage:.1f}%)")
                else:
                    imgui.text_colored("  No contributions yet...", 0.7, 0.7, 0.7)

            # Shiny Log panel
            with imgui.begin("Shiny Log"):
                imgui.text(f"Shinies Found: {len(shiny_log)}")
                imgui.separator()

                if len(shiny_log) == 0:
                    imgui.text_colored("No shinies found yet...", 0.7, 0.7, 0.7)
                else:
                    # Display most recent first
                    for i, entry in enumerate(reversed(list(shiny_log))):
                        imgui.text(f"#{len(shiny_log) - i}:")
                        imgui.text(f"  Worker: {entry['worker_id']}")

                        # Format timestamp nicely
                        timestamp = entry["timestamp"]
                        if "T" in timestamp:
                            timestamp = timestamp.split("T")[1].split(".")[0]  # Extract time only
                        imgui.text(f"  Time: {timestamp}")

                        imgui.text(f"  Frame Diff: {entry['frame_diff']}")
                        imgui.text(f"  Total Encounters: {entry['total_encounters']}")

                        # Truncate save file path for display
                        save_file = entry["save_file"]
                        if len(save_file) > 30:
                            save_file = "..." + save_file[-27:]
                        imgui.text(f"  Save: {save_file}")

                        imgui.separator()

                        # Limit display to last 5 shinies to avoid clutter
                        if i >= 4:
                            if len(shiny_log) > 5:
                                imgui.text_colored(
                                    f"... and {len(shiny_log) - 5} more", 0.5, 0.5, 0.5
                                )
                            break

            imgui.render()
            renderer.render(imgui.get_draw_data())
            glfw.swap_buffers(window)

    except KeyboardInterrupt:
        logger.info("\n[Main GUI] Interrupted by user")
    finally:
        logger.info("[Main GUI] Shutting down...")
        renderer.shutdown()
        glfw.terminate()
