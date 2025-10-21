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
from pyshiny_hunter.utils.gui_utils import glfw_init, opengl_create_texture, opengl_update_texture


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

    # Calculate optimal grid layout
    # For 1-2 workers: 1 row
    # For 3-4 workers: 2 rows, 2 cols
    # For 5-6 workers: 2 rows, 3 cols
    # For 7-9 workers: 3 rows, 3 cols
    # For 10-12 workers: 3 rows, 4 cols
    import math

    cols = min(4, max(1, math.ceil(math.sqrt(num_workers))))
    rows = math.ceil(num_workers / cols)

    # Calculate window size based on grid layout
    # Each worker panel: video (256px) + stats column (150px) + padding
    worker_panel_width = 256 + 150 + 20  # Video + stats + padding = 426px
    worker_panel_height = 384 + 30  # Video height + header/padding = 414px
    sidebar_width = 350  # For aggregate stats and shiny log
    window_width = (worker_panel_width * cols) + sidebar_width + 40  # Add padding
    window_height = max(600, (worker_panel_height * rows) + 100)

    logger.info(
        f"[Main GUI] Layout: {rows} rows × {cols} cols = {num_workers} workers "
        f"(window: {window_width}×{window_height})"
    )

    # Initialize ImGui
    imgui.create_context()
    window = glfw_init("PyShiny Hunter - Multi Mode", window_width, window_height)
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

    # Maximize window on startup for better fullscreen experience
    glfw.maximize_window(window)

    try:
        while not glfw.window_should_close(window):
            glfw.poll_events()
            renderer.process_inputs()

            # Get current window size (handles maximization/resize)
            current_width, current_height = glfw.get_window_size(window)

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

            # Main window with grid layout for workers (uses actual window size)
            workers_width = current_width - sidebar_width
            imgui.set_next_window_position(0, 0)
            imgui.set_next_window_size(workers_width, current_height)
            with imgui.begin(
                "Workers",
                flags=imgui.WINDOW_NO_TITLE_BAR
                | imgui.WINDOW_NO_RESIZE
                | imgui.WINDOW_NO_MOVE
                | imgui.WINDOW_NO_COLLAPSE,
            ):
                # Display workers in a grid layout
                for worker_id in range(num_workers):
                    state = worker_states[worker_id]

                    # Calculate grid position
                    col = worker_id % cols

                    # Start new row if needed (imgui.same_line() keeps on same row)
                    if col > 0:
                        imgui.same_line()

                    # Worker panel with fixed size - horizontal layout
                    imgui.begin_child(
                        f"worker_{worker_id}",
                        worker_panel_width - 10,
                        worker_panel_height - 10,
                        border=True,
                    )

                    # Left side: Video feed
                    imgui.begin_child(f"video_{worker_id}", 256, 384, border=False)
                    imgui.image(texture_ids[worker_id], 256, 384)
                    imgui.end_child()

                    # Right side: Stats (next to video)
                    imgui.same_line()
                    imgui.begin_child(f"stats_{worker_id}", 150, 384, border=False)

                    # Worker header
                    imgui.text(f"Worker {worker_id}")
                    imgui.separator()

                    # Status indicator
                    time_since_update = time.time() - state["last_update"]
                    if time_since_update > 2.0:
                        imgui.text_colored("STALLED", 1.0, 0.0, 0.0)
                    else:
                        imgui.text_colored("Running", 0.0, 1.0, 0.0)

                    imgui.separator()

                    # State and frame info
                    imgui.text("State:")
                    imgui.text_wrapped(state["state"])
                    imgui.spacing()

                    imgui.text("Frame:")
                    imgui.text(f"{state['frame']}")
                    imgui.spacing()

                    imgui.text("Encounters:")
                    imgui.text(f"{state['total_encounters']}")
                    imgui.spacing()

                    # Show encounter breakdown
                    if state["encounters"]:
                        imgui.separator()
                        imgui.text("Pokemon:")
                        for pokemon, count in list(state["encounters"].items())[:5]:
                            imgui.text(f"{pokemon}: {count}")
                        if len(state["encounters"]) > 5:
                            imgui.text_colored("...", 0.5, 0.5, 0.5)

                    imgui.end_child()
                    imgui.end_child()

            # Sidebar with Aggregate Stats and Shiny Log (uses actual window size)
            imgui.set_next_window_position(current_width - sidebar_width, 0)
            imgui.set_next_window_size(sidebar_width, current_height // 2)
            with imgui.begin(
                "Aggregate Stats",
                flags=imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_COLLAPSE,
            ):
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
                    imgui.text(f"Probability of at least one shiny: {prob_at_least_one:.2f}%")

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

            # Shiny Log panel (bottom half of sidebar, uses actual window size)
            imgui.set_next_window_position(current_width - sidebar_width, current_height // 2)
            imgui.set_next_window_size(sidebar_width, current_height // 2)
            with imgui.begin(
                "Shiny Log",
                flags=imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_COLLAPSE,
            ):
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
