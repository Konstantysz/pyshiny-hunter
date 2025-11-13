import sys

import glfw
import numpy as np
import OpenGL.GL as gl

from pyshiny_hunter.module_logger import logger


def glfw_init(
    window_name: str = "GLFW window", width: int = 1600, height: int = 900
) -> glfw._GLFWwindow:
    """Initialize GLFW window."""
    if not glfw.init():
        logger.error("Could not initialize OpenGL context")
        sys.exit(1)

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, gl.GL_TRUE)

    window = glfw.create_window(int(width), int(height), window_name, None, None)

    if not window:
        glfw.terminate()
        logger.error("Could not initialize Window")
        sys.exit(1)

    glfw.make_context_current(window)

    return window


def opengl_create_texture(width: int, height: int) -> int:
    """Create OpenGL texture for rendering."""
    texture_id: int = int(gl.glGenTextures(1))
    gl.glBindTexture(gl.GL_TEXTURE_2D, texture_id)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
    gl.glTexImage2D(
        gl.GL_TEXTURE_2D,
        0,
        gl.GL_RGBA,
        width,
        height,
        0,
        gl.GL_RGBA,
        gl.GL_UNSIGNED_BYTE,
        None,
    )
    return texture_id


def opengl_update_texture(image_data: np.ndarray, texture_id: int) -> None:
    gl.glBindTexture(gl.GL_TEXTURE_2D, texture_id)
    gl.glTexImage2D(
        gl.GL_TEXTURE_2D,
        0,
        gl.GL_RGBA,
        image_data.shape[1],
        image_data.shape[0],
        0,
        gl.GL_RGBA,
        gl.GL_UNSIGNED_BYTE,
        image_data,
    )
