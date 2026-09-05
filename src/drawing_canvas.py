from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import random
from .voice_commands import VoiceCommandListener
import cv2
import numpy as np
import math

Color = Tuple[int, int, int]
Point = Tuple[int, int]


@dataclass
class Button:
    label: str
    action: str
    rect: Tuple[int, int, int, int]
    color: Color

    def contains(self, point: Point) -> bool:
        x, y = point
        left, top, right, bottom = self.rect
        return left <= x <= right and top <= y <= bottom




class DrawingCanvas:
    def __init__(self, voice: VoiceCommandListener, output_dir: str = "saved_drawings") -> None:
        self.output_dir = Path(output_dir)
        self.voice = voice
        self.output_dir.mkdir(exist_ok=True)
        self.width = 0
        self.height = 0
        self.pages: List[Tuple[np.ndarray, np.ndarray]] = []
        self.page_index = 0
        self.color: Color = (0, 0, 255)
        self.effect = "normal"
        self.tool = "pencil"
        self.prev_point: Optional[Point] = None
        self._rainbow_hue = 0
        self._last_action_frame: Dict[str, int] = {}
        self.buttons: List[Button] = []
        self.undo_stack: List[Tuple[np.ndarray, np.ndarray]] = []
        self.redo_stack: List[Tuple[np.ndarray, np.ndarray]] = []
        self.max_undo = 20
        self.show_color_menu = False
        self.min_brush = 2
        self.max_brush = 50
        self.default_brush = 8
        

    @property
    def canvas(self) -> np.ndarray:
        return self.pages[self.page_index][0]

    @property
    def mask(self) -> np.ndarray:
        return self.pages[self.page_index][1]

    def ensure_size(self, width: int, height: int) -> None:
        if self.width == width and self.height == height:
            return
        self.width = width
        self.height = height
        self.pages = [
            (
                np.zeros((height, width, 3), dtype=np.uint8),
                np.zeros((height, width), dtype=np.uint8),
            )
        ]
        self.page_index = 0
        self.prev_point = None
        self._build_toolbar()

    def save_undo_state(self) -> None:
        self.undo_stack.append((self.canvas.copy(), self.mask.copy()))
        if len(self.undo_stack) > self.max_undo:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self) -> None:
        if not self.undo_stack:
            self.voice.speak("Nothing to undo")
            return
        self.redo_stack.append((self.canvas.copy(), self.mask.copy()))
        prev_canvas, prev_mask = self.undo_stack.pop()
        self.canvas[:] = prev_canvas
        self.mask[:] = prev_mask
        self.prev_point = None
        # self.voice.speak("Undo")

    def redo(self) -> None:
        if not self.redo_stack:
            self.voice.speak("Nothing to redo")
            return
        self.undo_stack.append((self.canvas.copy(), self.mask.copy()))
        next_canvas, next_mask = self.redo_stack.pop()
        self.canvas[:] = next_canvas
        self.mask[:] = next_mask
        self.prev_point = None
        self.voice.speak("Redo")

    def clear(self) -> None:
        self.save_undo_state()
        self.canvas[:] = 0
        self.mask[:] = 0
        self.prev_point = None
        self.voice.speak("Board cleared")

    def draw(self, point: Point, thickness: int) -> None:
        if self.prev_point is None:
            self.save_undo_state()
            self.prev_point = point
            return

        self._draw_effect_line(self.prev_point, point, thickness)
        self.prev_point = point

    def erase(self, point: Point, thickness: int) -> None:
        if self.prev_point is None:
            self.save_undo_state()
        radius = max(24, thickness * 3)
        cv2.line(self.canvas, self.prev_point or point, point, (0, 0, 0), radius)
        cv2.line(self.mask, self.prev_point or point, point, 0, radius)
        self.prev_point = point

    def stop_stroke(self) -> None:
        self.prev_point = None

    def compose(self, frame: np.ndarray) -> np.ndarray:
        output = frame.copy()
        active = self.mask > 0
        output[active] = self.canvas[active]
        return output

    def draw_ui(
        self, frame: np.ndarray, cursor: Optional[Point], gesture: str, brush_size: int
    ) -> None:
        self._draw_toolbar(frame, cursor)
        self._draw_status(frame, gesture, brush_size)
        if cursor:
            cv2.circle(frame, cursor, max(5, brush_size // 2), self._active_color(), 2)
        if self.show_color_menu:
            self.draw_color_palette(frame, cursor)

    def draw_color_palette(
        self, frame: np.ndarray, cursor: Optional[Point]
    ) -> Optional[str]:
        cy, cx = frame.shape[0] // 2, frame.shape[1] // 2
        radius = 45

        colors = [
            ("Red", (0, 0, 255)),
            ("Green", (0, 200, 0)),
            ("Blue", (255, 90, 0)),
            ("Purple", (255, 0, 255)),
            ("Orange", (0, 165, 255)),
            ("Black", (0, 0, 0)),
        ]

        overlay = frame.copy()
        cv2.rectangle(
            overlay, (cx - 320, cy - 120), (cx + 320, cy + 120), (20, 20, 25), -1
        )
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)
        cv2.rectangle(
            frame, (cx - 320, cy - 120), (cx + 320, cy + 120), (255, 255, 255), 2
        )
        cv2.putText(
            frame,
            "SELECT COLOR (Right Index + Middle UP to Select)",
            (cx - 280, cy - 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

        spacing = 100
        start_x = cx - (len(colors) - 1) * spacing // 2

        hovered_color_name = None
        for i, (name, col) in enumerate(colors):
            x = start_x + i * spacing
            y = cy + 20

            hovered = False
            if cursor:
                dist = math.hypot(cursor[0] - x, cursor[1] - y)
                if dist < radius:
                    hovered = True
                    hovered_color_name = name.lower()

            if hovered:
                cv2.circle(frame, (x, y), radius + 8, (255, 255, 255), 2)
                cv2.circle(frame, (x, y), radius, col, -1)
            else:
                cv2.circle(frame, (x, y), radius, col, -1)
                cv2.circle(frame, (x, y), radius, (245, 245, 245), 1)

            cv2.putText(
                frame,
                name,
                (x - 24, y + radius + 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.48,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

        return hovered_color_name

    def handle_toolbar(self, point: Optional[Point], frame_number: int) -> Optional[str]:
        if point is None:
            return None
        for button in self.buttons:
            if button.contains(point):
                last = self._last_action_frame.get(button.action, -999)
                if frame_number - last < 18:
                    return button.action
                self._last_action_frame[button.action] = frame_number
                return self._apply_action(button.action)
        return None

    def apply_voice_command(self, command: str) -> Optional[str]:
        command = command.lower()
        if "clear" in command:
            self.clear()
            return "clear"
        if "save" in command:
            return self.save()
        if "eraser" in command:
            self.tool = "eraser"
            self.voice.speak("Eraser mode")
            return "eraser"
        if "draw" in command:
            self.tool = "pencil"
            self.effect = "normal"
            self.voice.speak("Drawing mode")
            return "draw"
        if 'rainbow' in command:
            self.effect = "rainbow"
            self.tool = "pencil"
            self.voice.speak("Rainbow brush")
            return "rainbow"
        if 'neon' in command:
            self.effect = "neon"
            self.tool = "pencil"
            self.voice.speak("Neon brush")
            return "neon"
        if 'sparkle' in command:
            self.effect = "sparkle"
            self.tool = "pencil"
            self.voice.speak("Sparkle brush")
            return "sparkle"
        if 'fire' in command:
            self.effect = "fire"
            self.tool = "pencil"
            self.voice.speak("Fire brush")
            return "fire"
        if 'glow' in command:
            self.effect = "glow"
            self.tool = "pencil"
            self.voice.speak("Glow brush")
            return "glow"
        if command in {'red', 'green', 'blue', 'black', 'purple', 'orange'}:
            self.color = self._color_actions()[command]
            self.tool = "pencil"
            self.effect = "normal"
            self.voice.speak(f"{command.title()} selected")
            return command
        for name, color in self._color_actions().items():
            if name in command:
                self.color = color
                self.tool = "pencil"
                self.effect = "normal"
                self.voice.speak(f"{name.title()} selected")
                return name

        return None

    def save(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.output_dir / f"drawing_{timestamp}.png"
        white = np.full((self.height, self.width, 3), 255, dtype=np.uint8)
        active = self.mask > 0
        white[active] = self.canvas[active]
        cv2.imwrite(str(path), white)
        self.voice.speak(f"Saved {path.name}")
        return str(path)

    def get_page_on_white(self) -> np.ndarray:
        white = np.full((self.height, self.width, 3), 255, dtype=np.uint8)
        active = self.mask > 0
        white[active] = self.canvas[active]
        return white

    def _apply_action(self, action: str) -> str:
        colors = self._color_actions()
        if action in colors:
            self.color = colors[action]
            self.effect = "normal"
            self.tool = "pencil"
            self.voice.speak(f"{action.title()} selected")
        elif action in {"neon", "rainbow", "sparkle", "fire", "glow"}:
            self.effect = action
            self.tool = "pencil"
            self.voice.speak(f"{action.title()} brush")
        elif action == "eraser":
            self.tool = "eraser"
            self.voice.speak("Eraser selected")
        elif action == "draw":
            self.tool = "pencil"
            self.effect = "normal"
            self.voice.speak("Drawing mode")
        elif action == "clear":
            self.clear()
        elif action == "save":
            self.save()

        self.stop_stroke()
        return action

    def _draw_effect_line(self, start: Point, end: Point, thickness: int) -> None:
        color = self._active_color()

        # ---------------- NORMAL ---------------- #
        if self.effect == "normal":
            cv2.line(self.canvas, start, end, color, thickness, cv2.LINE_AA)
            cv2.line(self.mask, start, end, 255, thickness)

        # ---------------- NEON ---------------- #
        elif self.effect == "neon":
            # Glow is larger than the stroke, but not excessive
            glow_thickness = max(thickness + 8, int(thickness * 2.5))
            blur_sigma = max(4, thickness * 0.8)

            glow = np.zeros_like(self.canvas)

            cv2.line(
                glow,
                start,
                end,
                color,
                glow_thickness,
                cv2.LINE_AA,
            )

            glow = cv2.GaussianBlur(glow, (0, 0), blur_sigma)

            self.canvas[:] = cv2.addWeighted(
                self.canvas,
                1.0,
                glow,
                0.55,
                0,
            )

            # Colored stroke
            cv2.line(
                self.canvas,
                start,
                end,
                color,
                thickness,
                cv2.LINE_AA,
            )

            # White highlight
            cv2.line(
                self.canvas,
                start,
                end,
                (255, 255, 255),
                max(1, thickness // 3),
                cv2.LINE_AA,
            )

            # IMPORTANT: keep mask equal to actual brush size
            cv2.line(
                self.mask,
                start,
                end,
                255,
                thickness,
                cv2.LINE_AA,
            )

        # ---------------- GLOW ---------------- #
        elif self.effect == "glow":

            for scale, alpha in [(5, 0.15), (3, 0.25), (2, 0.35)]:

                glow = np.zeros_like(self.canvas)

                cv2.line(
                    glow,
                    start,
                    end,
                    color,
                    thickness * scale,
                    cv2.LINE_AA,
                )

                glow = cv2.GaussianBlur(glow, (0, 0), scale * 5)

                self.canvas[:] = cv2.addWeighted(
                    self.canvas,
                    1.0,
                    glow,
                    alpha,
                    0,
                )

            cv2.line(
                self.canvas,
                start,
                end,
                color,
                thickness,
                cv2.LINE_AA,
            )

            cv2.line(self.mask, start, end, 255, thickness * 5)

        # ---------------- SPARKLE ---------------- #
        elif self.effect == "sparkle":

            cv2.line(
                self.canvas,
                start,
                end,
                color,
                thickness,
                cv2.LINE_AA,
            )

            cv2.line(self.mask, start, end, 255, thickness)

            dx = end[0] - start[0]
            dy = end[1] - start[1]
            length = max(1, int(math.hypot(dx, dy)))

            for _ in range(length // 4):

                t = random.random()

                x = int(start[0] + dx * t)
                y = int(start[1] + dy * t)

                x += random.randint(-8, 8)
                y += random.randint(-8, 8)

                r = random.randint(1, 3)

                spark = (
                    (
                        255,
                        255,
                        255,
                    )
                    if random.random() < 0.6
                    else color
                )

                cv2.circle(self.canvas, (x, y), r, spark, -1)
                cv2.circle(self.mask, (x, y), r, 255, -1)

                # Star rays
                if random.random() < 0.25:
                    s = random.randint(3, 7)

                    cv2.line(self.canvas, (x - s, y), (x + s, y), spark, 1)
                    cv2.line(self.canvas, (x, y - s), (x, y + s), spark, 1)

        # ---------------- FIRE ---------------- #
        elif self.effect == "fire":

            # Outer flame
            cv2.line(
                self.canvas,
                start,
                end,
                (0, 80, 255),
                thickness + 8,
                cv2.LINE_AA,
            )

            # Middle
            cv2.line(
                self.canvas,
                start,
                end,
                (0, 180, 255),
                thickness + 4,
                cv2.LINE_AA,
            )

            # Hot center
            cv2.line(
                self.canvas,
                start,
                end,
                (180, 255, 255),
                max(2, thickness // 2),
                cv2.LINE_AA,
            )

            cv2.line(self.mask, start, end, 255, thickness + 8)

            dx = end[0] - start[0]
            dy = end[1] - start[1]

            length = max(1, int(math.hypot(dx, dy)))

            for _ in range(length // 3):

                t = random.random()

                x = int(start[0] + dx * t)
                y = int(start[1] + dy * t)

                x += random.randint(-4, 4)
                y -= random.randint(5, 22)

                radius = random.randint(2, 6)

                flame = random.choice(
                    [
                        (0, 100, 255),
                        (0, 180, 255),
                        (0, 255, 255),
                    ]
                )

                cv2.circle(
                    self.canvas,
                    (x, y),
                    radius,
                    flame,
                    -1,
                )

        # ---------------- RAINBOW ---------------- #
        elif self.effect == "rainbow":

            dx = end[0] - start[0]
            dy = end[1] - start[1]

            dist = int(math.hypot(dx, dy))

            if dist == 0:
                return

            for i in range(dist):

                t = i / dist

                x = int(start[0] + dx * t)
                y = int(start[1] + dy * t)

                self._rainbow_hue = (self._rainbow_hue + 2) % 180

                hsv = np.uint8([[[self._rainbow_hue, 255, 255]]])
                rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)[0][0]

                c = (int(rgb[0]), int(rgb[1]), int(rgb[2]))

                cv2.circle(
                    self.canvas,
                    (x, y),
                    thickness // 2 + 1,
                    c,
                    -1,
                )

                cv2.circle(
                    self.mask,
                    (x, y),
                    thickness // 2 + 1,
                    255,
                    -1,
                )

    def _active_color(self) -> Color:
        if self.effect == "rainbow":
            self._rainbow_hue = (self._rainbow_hue + 3) % 180
            hsv = np.uint8([[[self._rainbow_hue, 255, 255]]])
            bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)[0][0]
            return int(bgr[0]), int(bgr[1]), int(bgr[2])
        return self.color

    def _build_toolbar(self) -> None:
        specs = [
            ("DRAW", "draw", (90, 90, 90)),
            ("ERASE", "eraser", (190, 190, 190)),
            ("NEON", "neon", (255, 0, 255)),
            ("RAINBOW", "rainbow", (0, 200, 255)),
            ("SPARK", "sparkle", (255, 255, 255)),
            ("FIRE", "fire", (0, 90, 255)),
            ("GLOW", "glow", (120, 255, 120)),
            ("CLEAR", "clear", (80, 80, 80)),
            ("SAVE", "save", (60, 140, 220)),
        ]
        self._create_buttons(specs)

    def _create_buttons(self, specs):
        self.buttons = []

        margin = 8
        gap = 6
        button_h = 34

        normal_w = 60
        rainbow_w = 75  # Wider button

        x = margin
        y = margin

        for label, action, color in specs:

            # Rainbow button is wider
            width = rainbow_w if action == "rainbow" else normal_w

            self.buttons.append(
                Button(
                    label,
                    action,
                    (
                        x,
                        y,
                        x + width,
                        y + button_h,
                    ),
                    color,
                )
            )

            x += width + gap

    def _draw_toolbar(self, frame: np.ndarray, cursor: Optional[Point]) -> None:
        overlay = frame.copy()
        drawn_buttons = []
        for button in self.buttons:
            left, top, right, bottom = button.rect
            active = (
                button.action == self.tool
                or button.action == self.effect
                or button.action in self._color_actions()
                and self.color == self._color_actions()[button.action]
                and self.effect == "normal"
            )
            fill = (
                button.color
                if active
                else tuple(max(0, channel - 45) for channel in button.color)
            )
            if cursor and button.contains(cursor):
                fill = tuple(min(255, channel + 55) for channel in fill)
            cv2.rectangle(overlay, (left, top), (right, bottom), fill, -1)
            drawn_buttons.append((button, fill))
        cv2.addWeighted(overlay, 0.82, frame, 0.18, 0, frame)
        for button, fill in drawn_buttons:
            left, top, right, bottom = button.rect
            cv2.rectangle(frame, (left, top), (right, bottom), (245, 245, 245), 1)
            text_color = (255, 255, 255) if sum(fill) < 430 else (20, 20, 20)
            cv2.putText(
                frame,
                button.label,
                (left + 5, top + 23),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.46,
                text_color,
                1,
                cv2.LINE_AA,
            )

    def _draw_status(self, frame: np.ndarray, gesture: str, brush_size: int) -> None:
        if self.tool == "pencil":
            status = (
                f"Gesture: {gesture} | "
                f"Brush: {brush_size}px | "
                f"Effect: {self.effect}"
            )

        elif self.tool == "eraser":
            status = f"Gesture: {gesture} | " f"Eraser: {brush_size}px"

        y = self.height - 18
        cv2.rectangle(
            frame, (0, self.height - 42), (self.width, self.height), (0, 0, 0), -1
        )
        cv2.putText(
            frame,
            status,
            (12, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (245, 245, 245),
            1,
            cv2.LINE_AA,
        )
        cv2.circle(
            frame,
            (self.width - 36, self.height - 22),
            min(22, max(4, brush_size // 2)),
            self._active_color(),
            2,
        )

    def _color_actions(self) -> Dict[str, Color]:
        return {
            "red": (0, 0, 255),
            "green": (0, 200, 0),
            "blue": (255, 90, 0),
            "black": (0, 0, 0),
            "purple": (255, 0, 255),
            "orange": (0, 165, 255),
        }
