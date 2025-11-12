"""GUI configuration dialog for target Pokemon selection.

This module provides a pre-launch configuration dialog that allows users
to select target Pokemon, action mode, and number of workers interactively.
"""

from __future__ import annotations

from dataclasses import dataclass

import glfw
import imgui
from imgui.integrations.glfw import GlfwRenderer

from pyshiny_hunter.module_logger import logger
from pyshiny_hunter.pokemon_database import (
    filter_pokemon_names,
    load_pokemon_database,
    validate_pokemon_name,
)
from pyshiny_hunter.utils.gui_utils import glfw_init


@dataclass
class ConfigResult:
    """Result from configuration dialog.

    Attributes:
        target_pokemon: Selected target Pokemon name (None if no target).
        target_action: Selected action mode ('alert', 'pause', 'continue').
        num_workers: Number of worker processes.
        cancelled: True if user cancelled the dialog.
    """

    target_pokemon: str | None
    target_action: str
    num_workers: int
    cancelled: bool


def show_config_dialog(default_num_workers: int = 4) -> ConfigResult:
    """Show configuration dialog for target Pokemon selection.

    This function creates a modal dialog window that allows the user to:
    - Enter or select a target Pokemon (with autocomplete)
    - Choose action mode for non-target shinies
    - Set number of workers
    - Start hunting or cancel

    Args:
        default_num_workers: Default number of workers to show.

    Returns:
        ConfigResult with user selections or cancelled=True if user cancelled.

    Example:
        >>> result = show_config_dialog(num_workers=4)
        >>> if not result.cancelled:
        ...     print(f"Hunting {result.target_pokemon} with {result.num_workers} workers")
    """
    logger.info("Showing configuration dialog...")

    # Initialize ImGui
    imgui.create_context()
    window = glfw_init("PyShiny Hunter - Configuration", 600, 700)
    renderer = GlfwRenderer(window)

    # Load Pokemon database
    pokemon_db = load_pokemon_database()
    all_pokemon_names = sorted(pokemon_db.keys())
    logger.info(f"Loaded {len(all_pokemon_names)} Pokemon for autocomplete")

    # Dialog state
    pokemon_input = ""
    selected_pokemon = ""
    filtered_matches: list[str] = []
    action_mode = 0  # 0=alert, 1=pause, 2=continue
    num_workers = default_num_workers
    error_message = ""
    result: ConfigResult | None = None

    # Main render loop
    while not glfw.window_should_close(window):
        glfw.poll_events()
        renderer.process_inputs()

        imgui.new_frame()

        # Center the dialog window
        io = imgui.get_io()
        window_width = 580
        window_height = 680
        imgui.set_next_window_position(
            (io.display_size.x - window_width) * 0.5, (io.display_size.y - window_height) * 0.5
        )
        imgui.set_next_window_size(window_width, window_height)

        # Main configuration window
        imgui.begin(
            "Configuration",
            flags=imgui.WINDOW_NO_RESIZE
            | imgui.WINDOW_NO_MOVE
            | imgui.WINDOW_NO_COLLAPSE
            | imgui.WINDOW_NO_TITLE_BAR,
        )

        # Title
        imgui.text("PyShiny Hunter - Configuration")
        imgui.separator()
        imgui.spacing()

        # === TARGET POKEMON SECTION ===
        imgui.text("Target Pokemon (optional):")
        imgui.text("Leave empty to hunt for ANY shiny Pokemon")
        imgui.spacing()

        # Pokemon input field
        imgui.push_item_width(400)
        changed, pokemon_input = imgui.input_text(
            "##pokemon_input", pokemon_input, 256, imgui.INPUT_TEXT_CHARS_NO_BLANK
        )
        imgui.pop_item_width()

        imgui.same_line()
        if imgui.button("Clear"):
            pokemon_input = ""
            selected_pokemon = ""
            filtered_matches = []
            error_message = ""

        # Update filtered matches on input change
        if changed:
            if pokemon_input:
                filtered_matches = filter_pokemon_names(
                    pokemon_input, all_pokemon_names, max_results=10
                )
            else:
                filtered_matches = []
            error_message = ""  # Clear error on new input

        # Autocomplete suggestions
        if filtered_matches:
            imgui.text("Suggestions (click to select):")
            imgui.begin_child("suggestions", 400, 150, border=True)

            for pokemon_name in filtered_matches:
                if imgui.selectable(pokemon_name)[0]:
                    selected_pokemon = pokemon_name
                    pokemon_input = pokemon_name
                    filtered_matches = []
                    error_message = ""

            imgui.end_child()
        elif pokemon_input and not filtered_matches and changed:
            # Only show "no matches" if user just typed something
            imgui.text_colored("No matches found", 1.0, 0.5, 0.0)

        imgui.spacing()
        imgui.separator()
        imgui.spacing()

        # === ACTION MODE SECTION ===
        imgui.text("Action when non-target shiny found:")
        imgui.text("(Only applies if target Pokemon is set)")
        imgui.spacing()

        # Radio buttons for action mode
        if imgui.radio_button("Alert - Pause all workers + show GUI warning", action_mode == 0):
            action_mode = 0
        imgui.same_line()
        imgui.text_colored("(Safest)", 0.0, 1.0, 0.0)

        if imgui.radio_button("Pause - Pause all workers until manual resume", action_mode == 1):
            action_mode = 1
        imgui.same_line()
        imgui.text_colored("(Safe)", 0.5, 1.0, 0.5)

        if imgui.radio_button("Continue - Auto-skip and keep hunting", action_mode == 2):
            action_mode = 2
        imgui.same_line()
        imgui.text_colored("(Risky!)", 1.0, 0.5, 0.0)

        # Warning for "continue" mode
        if action_mode == 2:
            imgui.spacing()
            imgui.push_text_wrap_pos(550)
            imgui.text_colored(
                "WARNING: Continue mode will automatically skip non-target shinies. "
                "Savestates are still saved, but the hunt continues without confirmation.",
                1.0,
                0.0,
                0.0,
            )
            imgui.pop_text_wrap_pos()

        imgui.spacing()
        imgui.separator()
        imgui.spacing()

        # === NUMBER OF WORKERS SECTION ===
        imgui.text("Number of Workers:")
        imgui.text("(More workers = faster, but higher CPU usage)")
        imgui.spacing()

        imgui.push_item_width(100)
        changed_workers, num_workers = imgui.input_int("##num_workers", num_workers, step=1)
        imgui.pop_item_width()

        # Clamp workers to valid range
        if num_workers < 1:
            num_workers = 1
        elif num_workers > 12:
            num_workers = 12

        imgui.same_line()
        imgui.text("(1-12 workers, recommended: 4)")

        imgui.spacing()
        imgui.separator()
        imgui.spacing()

        # === ERROR MESSAGE ===
        if error_message:
            imgui.push_text_wrap_pos(550)
            imgui.text_colored(error_message, 1.0, 0.0, 0.0)
            imgui.pop_text_wrap_pos()
            imgui.spacing()

        # === BUTTONS ===
        imgui.spacing()

        # Start button (green, full width)
        imgui.push_style_color(imgui.COLOR_BUTTON, 0.0, 0.6, 0.0)
        imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 0.0, 0.7, 0.0)
        imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, 0.0, 0.5, 0.0)

        if imgui.button("Start Hunting", width=-1, height=40):
            # Validate Pokemon name if provided
            if pokemon_input.strip():
                is_valid, validation_error = validate_pokemon_name(pokemon_input, pokemon_db)

                if is_valid:
                    # Find exact match (case-insensitive)
                    for db_name in pokemon_db.keys():
                        if pokemon_input.strip().lower() == db_name.lower():
                            selected_pokemon = db_name
                            break

                    # Create result
                    action_str = ["alert", "pause", "continue"][action_mode]
                    result = ConfigResult(
                        target_pokemon=selected_pokemon if selected_pokemon else None,
                        target_action=action_str,
                        num_workers=num_workers,
                        cancelled=False,
                    )
                    logger.info(
                        f"Configuration confirmed: target={result.target_pokemon}, "
                        f"action={result.target_action}, workers={result.num_workers}"
                    )
                else:
                    error_message = validation_error
            else:
                # No target Pokemon - proceed without target mode
                action_str = ["alert", "pause", "continue"][action_mode]
                result = ConfigResult(
                    target_pokemon=None,
                    target_action=action_str,
                    num_workers=num_workers,
                    cancelled=False,
                )
                logger.info(
                    f"Configuration confirmed: no target, "
                    f"action={result.target_action}, workers={result.num_workers}"
                )

        imgui.pop_style_color(3)

        imgui.spacing()

        # Cancel button (red)
        imgui.push_style_color(imgui.COLOR_BUTTON, 0.6, 0.0, 0.0)
        imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 0.7, 0.0, 0.0)
        imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, 0.5, 0.0, 0.0)

        if imgui.button("Cancel", width=-1, height=30):
            logger.info("Configuration cancelled by user")
            result = ConfigResult(
                target_pokemon=None, target_action="alert", num_workers=1, cancelled=True
            )

        imgui.pop_style_color(3)

        imgui.end()

        # Render
        imgui.render()
        imgui.end_frame()

        # OpenGL rendering
        import OpenGL.GL as gl

        gl.glClearColor(0.1, 0.1, 0.1, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        renderer.render(imgui.get_draw_data())

        glfw.swap_buffers(window)

        # Exit loop if result is set
        if result is not None:
            break

    # Cleanup
    renderer.shutdown()
    glfw.terminate()

    # Return result or default cancelled result
    if result is None:
        logger.info("Configuration window closed without selection")
        return ConfigResult(
            target_pokemon=None, target_action="alert", num_workers=1, cancelled=True
        )

    return result
