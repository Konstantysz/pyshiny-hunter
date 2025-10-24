"""Main GUI process for displaying multiple worker streams.

This module implements the unified GUI that displays all worker emulator
streams in a single window with aggregate statistics and shiny log.
"""

import datetime
import multiprocessing as mp
import time
from queue import Empty
from typing import Optional

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
    init_status: Optional[dict] = None,
):
    """Main GUI process displaying all worker streams.

    Args:
        num_workers: Number of worker processes
        screenshot_queue: Queue receiving screenshots from workers
        control_queues: Queues for sending commands to workers (future use)
        shiny_log: Shared list for centralized shiny logging
        encounter_stats: Shared dict for aggregate encounter statistics
        init_status: Shared dict tracking worker initialization progress
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
    base_worker_panel_width = 256 + 150 + 20  # Video + stats + padding = 426px
    worker_panel_height = 384 + 30  # Video height + header/padding = 414px
    sidebar_width = 350  # For aggregate stats and shiny log
    window_width = (base_worker_panel_width * cols) + sidebar_width + 40  # Add padding
    window_height = max(600, (worker_panel_height * rows) + 100)

    logger.info(
        f"[Main GUI] Layout: {rows} rows × {cols} cols = {num_workers} workers "
        f"(window: {window_width}×{window_height})"
    )

    # Initialize ImGui
    imgui.create_context()
    window = glfw_init("PyShiny Hunter - Multi Mode", window_width, window_height)
    renderer = GlfwRenderer(window)

    # DISABLE ImGui keyboard navigation GLOBALLY - we need arrow keys for game control!
    io = imgui.get_io()
    io.config_flags &= ~imgui.CONFIG_NAV_ENABLE_KEYBOARD  # Turn OFF keyboard nav

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
            "fps": 0.0,
            "paused": False,
        }

    logger.info("[Main GUI] GUI initialized, starting render loop...")

    # Maximize window on startup for better fullscreen experience
    glfw.maximize_window(window)

    try:
        # Track which worker is under manual control (need to persist across frames)
        controlled_worker = None
        frame_count = 0  # For throttling debug logs
        prev_key_state = set()  # Track previous key state to only send changes

        while not glfw.window_should_close(window):
            glfw.poll_events()
            renderer.process_inputs()

            # Get current window size (handles maximization/resize)
            current_width, current_height = glfw.get_window_size(window)
            frame_count += 1

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
                                "fps": data.get("fps", 0.0),
                                "paused": data.get("paused", False),
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

            # Calculate dynamic worker panel width to fit in available space
            available_width = workers_width - 20  # Account for padding
            worker_panel_width = (available_width / cols) - 10  # Distribute evenly across columns

            # Check if all workers are ready (initialization complete)
            # Workers are considered "ready" when they reach "waiting" or "ready" status
            # "waiting" = finished desync, waiting at barrier for others
            # "ready" = passed barrier, started main loop
            # Convert init_status once per frame to avoid redundant dict conversions
            init_status_snapshot = dict(init_status) if init_status is not None else {}
            all_workers_ready = False
            if init_status_snapshot:
                # Count workers that are either waiting at barrier OR fully ready
                workers_at_barrier_or_ready = sum(
                    1 for s in init_status_snapshot.values() if s in ("waiting", "ready")
                )
                all_workers_ready = workers_at_barrier_or_ready == num_workers
            else:
                # No init tracking, assume ready immediately
                all_workers_ready = True

            imgui.set_next_window_position(0, 0)
            imgui.set_next_window_size(workers_width, current_height)

            # Allow resize during initialization, lock during normal operation
            window_flags = (
                imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_COLLAPSE
            )
            if all_workers_ready:
                window_flags |= imgui.WINDOW_NO_RESIZE

            with imgui.begin("Workers", flags=window_flags):
                if not all_workers_ready:
                    # Show initialization progress instead of worker cards
                    imgui.text("")
                    imgui.text("")
                    imgui.text("")
                    imgui.text("")
                    imgui.spacing()
                    imgui.spacing()

                    # Center the progress display
                    imgui.set_cursor_pos_x(workers_width / 2 - 200)
                    imgui.text("Initializing Emulators...")
                    imgui.spacing()
                    imgui.spacing()

                    # Use the snapshot we already created at start of frame
                    # (no need to convert dict again)

                    # Count workers by status
                    ready_count = sum(1 for s in init_status_snapshot.values() if s == "ready")
                    waiting_count = sum(1 for s in init_status_snapshot.values() if s == "waiting")

                    # Progress bar - count workers that finished desync (waiting + ready)
                    finished_desync_count = waiting_count + ready_count
                    progress = finished_desync_count / num_workers if num_workers > 0 else 0.0
                    imgui.set_cursor_pos_x(workers_width / 2 - 200)
                    imgui.progress_bar(progress, (400, 30))

                    imgui.spacing()
                    imgui.set_cursor_pos_x(workers_width / 2 - 200)
                    imgui.text(f"Desynchronized: {finished_desync_count}/{num_workers}")

                    imgui.spacing()
                    imgui.spacing()

                    # Show status for each worker
                    imgui.set_cursor_pos_x(workers_width / 2 - 200)
                    imgui.begin_child("worker_status", 400, 200, border=True)
                    for worker_id in range(num_workers):
                        status = init_status_snapshot.get(worker_id, "pending...")

                        # Color-code status
                        if status == "ready":
                            imgui.text_colored(f"Worker {worker_id}: Ready", 0.0, 1.0, 0.0)
                        elif status == "waiting":
                            imgui.text_colored(
                                f"Worker {worker_id}: Waiting for others...", 1.0, 1.0, 0.0
                            )
                        elif status == "desyncing":
                            imgui.text_colored(
                                f"Worker {worker_id}: Desyncing RNG...", 0.0, 0.5, 1.0
                            )
                        elif status == "loading":
                            imgui.text_colored(
                                f"Worker {worker_id}: Loading emulator...", 0.5, 0.5, 1.0
                            )
                        else:
                            imgui.text(f"Worker {worker_id}: {status}")
                    imgui.end_child()
                else:
                    # Show normal worker grid layout
                    for worker_id in range(num_workers):
                        state = worker_states[worker_id]

                        # Calculate grid position
                        col = worker_id % cols

                        # Start new row if needed (imgui.same_line() keeps on same row)
                        if col > 0:
                            imgui.same_line()

                        # Worker panel with dynamic width - horizontal layout
                        imgui.begin_child(
                            f"worker_{worker_id}",
                            worker_panel_width,
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

                        # Manual control buttons
                        imgui.separator()
                        imgui.spacing()

                        if state["paused"]:
                            # Show "Resume Hunter" button when paused
                            imgui.push_style_color(imgui.COLOR_BUTTON, 0.0, 0.6, 0.0)
                            if imgui.button(f"Resume##w{worker_id}", width=140):
                                # Send resume command to worker
                                control_queues[worker_id].put({"action": "resume"})
                                controlled_worker = None
                            imgui.pop_style_color()
                        else:
                            # Show "Take Control" button when running
                            imgui.push_style_color(imgui.COLOR_BUTTON, 0.6, 0.4, 0.0)
                            disabled = (
                                controlled_worker is not None and controlled_worker != worker_id
                            )
                            if disabled:
                                imgui.push_style_color(imgui.COLOR_BUTTON, 0.3, 0.3, 0.3)
                                imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 0.3, 0.3, 0.3)
                                imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, 0.3, 0.3, 0.3)

                            if imgui.button(f"Take Control##w{worker_id}", width=140):
                                if not disabled:
                                    # Send pause command to worker
                                    control_queues[worker_id].put({"action": "pause"})
                                    controlled_worker = worker_id

                            if disabled:
                                imgui.pop_style_color(3)
                            imgui.pop_style_color()

                        imgui.end_child()
                        imgui.end_child()

            # Manual Control Modal Window
            if controlled_worker is not None and worker_states[controlled_worker]["paused"]:
                # Show modal window for manual control
                imgui.open_popup("Manual Control")

                # Center the modal window - size based on 1.5× emulator display
                modal_width = 400
                modal_height = 750
                imgui.set_next_window_size(modal_width, modal_height)
                imgui.set_next_window_position(
                    (current_width - modal_width) // 2, (current_height - modal_height) // 2
                )

                if imgui.begin_popup_modal(
                    "Manual Control",
                    flags=imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_COLLAPSE,
                )[0]:
                    state = worker_states[controlled_worker]

                    # Title
                    imgui.text(f"Manual Control - Worker {controlled_worker}")
                    imgui.separator()
                    imgui.spacing()

                    # Emulator display (1.5× size: 384×576)
                    imgui.text("Emulator Screen:")
                    imgui.image(texture_ids[controlled_worker], 384, 576)
                    imgui.spacing()

                    # Keyboard controls help
                    imgui.separator()
                    imgui.text("Keyboard Controls:")
                    imgui.spacing()
                    imgui.columns(2, "controls")
                    imgui.text("D-Pad: Arrow Keys")
                    imgui.text("A Button: Z")
                    imgui.text("B Button: X")
                    imgui.text("X Button: A")
                    imgui.next_column()
                    imgui.text("Y Button: S")
                    imgui.text("L Trigger: Q")
                    imgui.text("R Trigger: W")
                    imgui.text("Start: Enter, Select: Shift")
                    imgui.columns(1)
                    imgui.spacing()

                    imgui.separator()
                    imgui.spacing()

                    # Resume button
                    imgui.push_style_color(imgui.COLOR_BUTTON, 0.0, 0.6, 0.0)
                    if imgui.button("Resume Hunter", width=380):
                        control_queues[controlled_worker].put({"action": "resume"})
                        controlled_worker = None
                        prev_key_state.clear()  # Reset key state tracking
                        imgui.close_current_popup()
                    imgui.pop_style_color()

                    # Send complete keyboard state every frame (simple & reliable)
                    io = imgui.get_io()

                    # DEBUG: Log arrow key state when pressed (not every frame to reduce spam)
                    arrow_debug = []
                    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
                        arrow_debug.append("UP")
                    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
                        arrow_debug.append("DOWN")
                    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
                        arrow_debug.append("LEFT")
                    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
                        arrow_debug.append("RIGHT")
                    if arrow_debug:
                        logger.debug(f"[GUI] Arrow keys via GLFW: {arrow_debug}")

                    # Build list of currently pressed keys using config mapping
                    pressed_keys = []

                    # Arrow keys: Use GLFW directly (GlfwRenderer blocks them from ImGui)
                    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
                        pressed_keys.append(config.MANUAL_CONTROL_KEY_MAP["UP"])
                    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
                        pressed_keys.append(config.MANUAL_CONTROL_KEY_MAP["DOWN"])
                    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
                        pressed_keys.append(config.MANUAL_CONTROL_KEY_MAP["LEFT"])
                    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
                        pressed_keys.append(config.MANUAL_CONTROL_KEY_MAP["RIGHT"])

                    # Face buttons and other keys from ImGui
                    if io.keys_down[ord("Z")]:
                        pressed_keys.append(config.MANUAL_CONTROL_KEY_MAP["Z"])
                    if io.keys_down[ord("X")]:
                        pressed_keys.append(config.MANUAL_CONTROL_KEY_MAP["X"])
                    if io.keys_down[ord("A")]:
                        pressed_keys.append(config.MANUAL_CONTROL_KEY_MAP["A"])
                    if io.keys_down[ord("S")]:
                        pressed_keys.append(config.MANUAL_CONTROL_KEY_MAP["S"])
                    if io.keys_down[ord("Q")]:
                        pressed_keys.append(config.MANUAL_CONTROL_KEY_MAP["Q"])
                    if io.keys_down[ord("W")]:
                        pressed_keys.append(config.MANUAL_CONTROL_KEY_MAP["W"])
                    if io.keys_down[imgui.KEY_ENTER]:
                        pressed_keys.append(config.MANUAL_CONTROL_KEY_MAP["ENTER"])
                    if io.key_shift:
                        pressed_keys.append(config.MANUAL_CONTROL_KEY_MAP["SHIFT"])

                    # DEBUG: Show currently pressed keys
                    imgui.spacing()
                    imgui.separator()
                    imgui.text("Debug - Currently Pressed:")
                    if pressed_keys:
                        for key in pressed_keys:
                            imgui.text(f"  {key}")
                    else:
                        imgui.text_colored("  (none)", 0.5, 0.5, 0.5)

                    # Only send keyboard state when it CHANGES (eliminates queue flooding)
                    current_key_state = set(pressed_keys)
                    if current_key_state != prev_key_state:
                        control_queues[controlled_worker].put(
                            {"action": "input", "type": "key_state", "keys": pressed_keys}
                        )
                        logger.debug(
                            f"[GUI] Key state changed: {list(prev_key_state)} → {pressed_keys}"
                        )
                        prev_key_state = current_key_state

                    imgui.end_popup()

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

                # Calculate average FPS across all workers
                worker_fps_values = [
                    state["fps"] for state in worker_states.values() if state["fps"] > 0
                ]
                if worker_fps_values:
                    avg_fps = sum(worker_fps_values) / len(worker_fps_values)
                    imgui.text(f"Average Worker FPS: {avg_fps:.1f}")

                    # Show individual FPS for each worker
                    imgui.text("Worker FPS:")
                    for worker_id in range(num_workers):
                        fps = worker_states[worker_id]["fps"]
                        imgui.text(f"  Worker {worker_id}: {fps:.1f}")
                else:
                    imgui.text("Average Worker FPS: calculating...")

                imgui.text(f"GUI FPS: {1 / imgui.get_io().delta_time:.1f}")

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
