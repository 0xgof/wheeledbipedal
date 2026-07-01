"""Gymnasium-compatible RGB array rendering for visualization states."""

from __future__ import annotations

import math

import numpy as np

from wheeled_biped_rl.visualization.render_state import RenderState


class RgbArrayRenderer:
    """Render ``RenderState`` frames into deterministic RGB arrays."""

    def __init__(self,
                 width_px: int = 320,
                 height_px: int = 240,
                 pixels_per_meter: float = 180.0) -> None:
        """Create a lightweight raster renderer with fixed frame dimensions."""

        self.width_px = width_px
        self.height_px = height_px
        self.pixels_per_meter = pixels_per_meter

    def render(self, render_state: RenderState) -> np.ndarray:
        """Render one backend-neutral state to an ``uint8`` RGB array."""

        image = np.full((self.height_px, self.width_px, 3), 245, dtype=np.uint8)
        ground_y = self._world_to_pixel_y(0.0)
        _draw_line(image, 0, ground_y, self.width_px - 1, ground_y, (90, 90, 90))
        self._draw_leg(image, render_state.left_leg)
        self._draw_leg(image, render_state.right_leg)
        self._draw_wheel(image, render_state.left_wheel.x_m,
                         render_state.left_wheel.z_m,
                         render_state.left_wheel.radius_m)
        self._draw_wheel(image, render_state.right_wheel.x_m,
                         render_state.right_wheel.z_m,
                         render_state.right_wheel.radius_m)
        self._draw_body(image, render_state)
        return image

    def _draw_body(self,
                   image: np.ndarray,
                   render_state: RenderState) -> None:
        """Draw a small pitched body segment."""

        body = render_state.body
        half_length = body.size_x_m * 0.5
        dx = half_length * math.cos(body.pitch_rad)
        dz = half_length * math.sin(body.pitch_rad)
        x1 = self._world_to_pixel_x(body.x_m - dx)
        y1 = self._world_to_pixel_y(body.z_m - dz)
        x2 = self._world_to_pixel_x(body.x_m + dx)
        y2 = self._world_to_pixel_y(body.z_m + dz)
        _draw_line(image, x1, y1, x2, y2, (35, 80, 150), thickness=4)

    def _draw_leg(self,
                  image: np.ndarray,
                  leg_state: object) -> None:
        """Draw one reduced leg as a line from hip to contact point."""

        x1 = self._world_to_pixel_x(leg_state.hip_x_m)
        y1 = self._world_to_pixel_y(leg_state.hip_z_m)
        x2 = self._world_to_pixel_x(leg_state.contact_x_m)
        y2 = self._world_to_pixel_y(leg_state.contact_z_m)
        color = (40, 130, 80) if leg_state.contact else (150, 120, 40)
        _draw_line(image, x1, y1, x2, y2, color, thickness=2)

    def _draw_wheel(self,
                    image: np.ndarray,
                    x_m: float,
                    z_m: float,
                    radius_m: float) -> None:
        """Draw a wheel as a filled disk."""

        center_x = self._world_to_pixel_x(x_m)
        center_y = self._world_to_pixel_y(z_m)
        radius_px = max(2, int(radius_m * self.pixels_per_meter))
        _draw_disk(image, center_x, center_y, radius_px, (45, 45, 45))

    def _world_to_pixel_x(self, x_m: float) -> int:
        """Map world x coordinate to image x pixel."""

        pixel_x = int(round(self.width_px * 0.5 + x_m * self.pixels_per_meter))
        return pixel_x

    def _world_to_pixel_y(self, z_m: float) -> int:
        """Map world z coordinate to image y pixel."""

        pixel_y = int(round(self.height_px * 0.82 - z_m * self.pixels_per_meter))
        return pixel_y


def render_rollout_frames(render_states: list[RenderState],
                          width_px: int = 320,
                          height_px: int = 240) -> list[np.ndarray]:
    """Render a list of render states into RGB arrays."""

    renderer = RgbArrayRenderer(width_px=width_px, height_px=height_px)
    frames = [renderer.render(render_state) for render_state in render_states]
    return frames


def _draw_disk(image: np.ndarray,
               center_x: int,
               center_y: int,
               radius_px: int,
               color: tuple[int, int, int]) -> None:
    """Draw a filled disk into an RGB array."""

    height, width, _ = image.shape
    y_min = max(0, center_y - radius_px)
    y_max = min(height - 1, center_y + radius_px)
    x_min = max(0, center_x - radius_px)
    x_max = min(width - 1, center_x + radius_px)
    for y_px in range(y_min, y_max + 1):
        for x_px in range(x_min, x_max + 1):
            dx = x_px - center_x
            dy = y_px - center_y
            if dx * dx + dy * dy <= radius_px * radius_px:
                image[y_px, x_px] = color


def _draw_line(image: np.ndarray,
               x1: int,
               y1: int,
               x2: int,
               y2: int,
               color: tuple[int, int, int],
               thickness: int = 1) -> None:
    """Draw a clipped integer line into an RGB array."""

    steps = max(abs(x2 - x1), abs(y2 - y1), 1)
    for step in range(steps + 1):
        ratio = step / steps
        x_px = int(round(x1 + (x2 - x1) * ratio))
        y_px = int(round(y1 + (y2 - y1) * ratio))
        _draw_point(image, x_px, y_px, color, thickness)


def _draw_point(image: np.ndarray,
                x_px: int,
                y_px: int,
                color: tuple[int, int, int],
                thickness: int) -> None:
    """Draw one square point with clipping."""

    height, width, _ = image.shape
    radius = max(0, thickness // 2)
    for yy in range(y_px - radius, y_px + radius + 1):
        for xx in range(x_px - radius, x_px + radius + 1):
            if 0 <= xx < width and 0 <= yy < height:
                image[yy, xx] = color
