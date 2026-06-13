from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import random

import cv2
import numpy as np


Color = Tuple[int, int, int]
Point = Tuple[int, int]


MENU_OPTIONS = (
    ("draw", "Drawing"),
    ("piano", "Piano"),
    ("game", "Game"),
    ("ocr", "OCR Mode"),
    ("voice", "Voice Mode"),
)


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


class DrawingBoard:
    def __init__(self, output_dir: str = "saved_drawings") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.pages: List[Tuple[np.ndarray, np.ndarray]] = []
        self.page_index = 0
        self.width = 0
        self.height = 0
        self.color: Color = (0, 0, 255)
        self.effect = "normal"
        self.mode = "draw"
        self.prev_point: Optional[Point] = None
        self.message = "Ready"
        self.message_frames = 0
        self._rainbow_hue = 0
        self._last_action_frame: Dict[str, int] = {}
        self.buttons: List[Button] = []
        self.undo_stack: List[Tuple[np.ndarray, np.ndarray]] = []
        self.redo_stack: List[Tuple[np.ndarray, np.ndarray]] = []
        self.max_undo = 20
        self.show_color_menu = False

    @property
    def canvas(self) -> np.ndarray:
        return self.pages[self.page_index][0]

    @property
    def mask(self) -> np.ndarray:
        return self.pages[self.page_index][1]

    def ensure_size(self, width: int, height: int) -> None:
        if self.width == width and self.height == height and self.pages:
            return
        self.width = width
        self.height = height
        self.pages = [(np.zeros((height, width, 3), dtype=np.uint8), np.zeros((height, width), dtype=np.uint8))]
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
            self.say("Nothing to undo")
            return
        self.redo_stack.append((self.canvas.copy(), self.mask.copy()))
        prev_canvas, prev_mask = self.undo_stack.pop()
        self.canvas[:] = prev_canvas
        self.mask[:] = prev_mask
        self.prev_point = None
        self.say("Undo")

    def redo(self) -> None:
        if not self.redo_stack:
            self.say("Nothing to redo")
            return
        self.undo_stack.append((self.canvas.copy(), self.mask.copy()))
        next_canvas, next_mask = self.redo_stack.pop()
        self.canvas[:] = next_canvas
        self.mask[:] = next_mask
        self.prev_point = None
        self.say("Redo")

    def clear(self) -> None:
        self.save_undo_state()
        self.canvas[:] = 0
        self.mask[:] = 0
        self.prev_point = None
        self.say("Board cleared")

    def new_page(self) -> None:
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.pages.append(
            (
                np.zeros((self.height, self.width, 3), dtype=np.uint8),
                np.zeros((self.height, self.width), dtype=np.uint8),
            )
        )
        self.page_index = len(self.pages) - 1
        self.prev_point = None
        self.say(f"Page {self.page_index + 1}")

    def next_page(self) -> None:
        if self.page_index < len(self.pages) - 1:
            self.undo_stack.clear()
            self.redo_stack.clear()
            self.page_index += 1
            self.prev_point = None
            self.say(f"Page {self.page_index + 1}")

    def previous_page(self) -> None:
        if self.page_index > 0:
            self.undo_stack.clear()
            self.redo_stack.clear()
            self.page_index -= 1
            self.prev_point = None
            self.say(f"Page {self.page_index + 1}")

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

    def draw_shape(self, shape: str, center: Point, size: int) -> None:
        self.save_undo_state()
        color = self._active_color()
        thickness = max(2, size // 4)
        x, y = center
        radius = max(28, size * 3)
        if shape == "circle":
            cv2.circle(self.canvas, center, radius, color, thickness)
            cv2.circle(self.mask, center, radius, 255, thickness)
        elif shape == "rectangle":
            top_left = (x - radius, y - radius // 2)
            bottom_right = (x + radius, y + radius // 2)
            cv2.rectangle(self.canvas, top_left, bottom_right, color, thickness)
            cv2.rectangle(self.mask, top_left, bottom_right, 255, thickness)
        elif shape == "triangle":
            pts = np.array([(x, y - radius), (x - radius, y + radius), (x + radius, y + radius)], np.int32)
            cv2.polylines(self.canvas, [pts], True, color, thickness)
            cv2.polylines(self.mask, [pts], True, 255, thickness)
        self.say(f"{shape.title()} added")

    def compose(self, frame: np.ndarray) -> np.ndarray:
        output = frame.copy()
        active = self.mask > 0
        output[active] = self.canvas[active]
        return output

    def draw_ui(self, frame: np.ndarray, cursor: Optional[Point], gesture: str, brush_size: int) -> None:
        self._draw_toolbar(frame, cursor)
        self._draw_status(frame, gesture, brush_size)
        if cursor:
            cv2.circle(frame, cursor, max(5, brush_size // 2), self._active_color(), 2)
        if self.show_color_menu:
            self.draw_color_palette(frame, cursor)
        if self.message_frames > 0:
            self._draw_message(frame)
            self.message_frames -= 1

    def draw_color_palette(self, frame: np.ndarray, cursor: Optional[Point]) -> Optional[str]:
        cy, cx = frame.shape[0] // 2, frame.shape[1] // 2
        radius = 45
        import math
        colors = [
            ("Red", (0, 0, 255)),
            ("Green", (0, 200, 0)),
            ("Blue", (255, 90, 0)),
            ("Purple", (255, 0, 255)),
            ("Orange", (0, 165, 255)),
            ("Black", (0, 0, 0)),
        ]
        
        overlay = frame.copy()
        cv2.rectangle(overlay, (cx - 320, cy - 120), (cx + 320, cy + 120), (20, 20, 25), -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)
        cv2.rectangle(frame, (cx - 320, cy - 120), (cx + 320, cy + 120), (255, 255, 255), 2)
        cv2.putText(frame, "SELECT COLOR (Right Index + Middle UP to Select)", (cx - 280, cy - 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
        
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
                
            cv2.putText(frame, name, (x - 24, y + radius + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 1, cv2.LINE_AA)
            
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
            self.mode = "eraser"
            self.say("Eraser mode")
            return "eraser"
        for name, color in self._color_actions().items():
            if name in command:
                self.color = color
                self.mode = "draw"
                self.effect = "normal"
                self.say(f"{name.title()} selected")
                return name
        if "piano" in command:
            self.mode = "piano"
            self.say("Piano opened")
            return "piano"
        if "game" in command:
            self.mode = "game"
            self.say("Game started")
            return "game"
        return None

    def save(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.output_dir / f"drawing_page_{self.page_index + 1}_{timestamp}.png"
        white = np.full((self.height, self.width, 3), 255, dtype=np.uint8)
        active = self.mask > 0
        white[active] = self.canvas[active]
        cv2.imwrite(str(path), white)
        self.say(f"Saved {path.name}")
        return str(path)

    def get_page_on_white(self) -> np.ndarray:
        white = np.full((self.height, self.width, 3), 255, dtype=np.uint8)
        active = self.mask > 0
        white[active] = self.canvas[active]
        return white

    def say(self, text: str, frames: int = 70) -> None:
        self.message = text
        self.message_frames = frames

    def _apply_action(self, action: str) -> str:
        colors = self._color_actions()
        if action in colors:
            self.color = colors[action]
            self.effect = "normal"
            self.mode = "draw"
            self.say(f"{action.title()} selected")
        elif action in {"neon", "rainbow", "sparkle", "fire", "glow"}:
            self.effect = action
            self.mode = "draw"
            self.say(f"{action.title()} brush")
        elif action == "eraser":
            self.mode = "eraser"
            self.say("Eraser selected")
        elif action == "clear":
            self.clear()
        elif action == "save":
            self.save()
        elif action == "new":
            self.new_page()
        elif action == "prev":
            self.previous_page()
        elif action == "next":
            self.next_page()
        elif action == "piano":
            self.mode = "piano"
            self.say("Piano mode")
        elif action == "game":
            self.mode = "game"
            self.say("Game mode")
        elif action == "draw":
            self.mode = "draw"
            self.say("Draw mode")
        elif action == "ocr":
            self.mode = "ocr"
            self.say("OCR mode")
        elif action == "voice":
            self.mode = "voice"
            self.say("Voice mode")
        self.stop_stroke()
        return action

    def _draw_effect_line(self, start: Point, end: Point, thickness: int) -> None:
        color = self._active_color()
        if self.effect == "neon":
            cv2.line(self.canvas, start, end, color, thickness * 4)
            cv2.line(self.canvas, start, end, (255, 255, 255), max(1, thickness // 2))
            cv2.line(self.mask, start, end, 255, thickness * 4)
        elif self.effect == "glow":
            glow = np.zeros_like(self.canvas)
            glow_mask = np.zeros_like(self.mask)
            cv2.line(glow, start, end, color, thickness * 5)
            cv2.line(glow_mask, start, end, 255, thickness * 5)
            blurred = cv2.GaussianBlur(glow, (0, 0), 9)
            self.canvas[:] = np.maximum(self.canvas, blurred)
            self.mask[:] = np.maximum(self.mask, glow_mask)
            cv2.line(self.canvas, start, end, color, thickness)
            cv2.line(self.mask, start, end, 255, thickness)
        elif self.effect == "sparkle":
            cv2.line(self.canvas, start, end, color, thickness)
            cv2.line(self.mask, start, end, 255, thickness)
            for _ in range(5):
                ox = random.randint(-18, 18)
                oy = random.randint(-18, 18)
                radius = random.randint(1, 4)
                sparkle = (255, 255, 255) if random.random() < 0.45 else color
                center = (end[0] + ox, end[1] + oy)
                cv2.circle(self.canvas, center, radius, sparkle, -1)
                cv2.circle(self.mask, center, radius, 255, -1)
        elif self.effect == "fire":
            cv2.line(self.canvas, start, end, (0, 90, 255), thickness + 4)
            cv2.line(self.canvas, start, end, (0, 220, 255), max(1, thickness // 2))
            cv2.line(self.mask, start, end, 255, thickness + 4)
            for _ in range(4):
                center = (end[0] + random.randint(-10, 10), end[1] - random.randint(0, 24))
                cv2.circle(self.canvas, center, random.randint(2, 7), (0, random.randint(80, 180), 255), -1)
                cv2.circle(self.mask, center, 7, 255, -1)
        else:
            cv2.line(self.canvas, start, end, color, thickness)
            cv2.line(self.mask, start, end, 255, thickness)

    def _active_color(self) -> Color:
        if self.effect == "rainbow":
            self._rainbow_hue = (self._rainbow_hue + 3) % 180
            hsv = np.uint8([[[self._rainbow_hue, 255, 255]]])
            bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)[0][0]
            return int(bgr[0]), int(bgr[1]), int(bgr[2])
        return self.color

    def _build_toolbar(self) -> None:
        specs = [
            ("RED", "red", (0, 0, 220)),
            ("GREEN", "green", (0, 180, 0)),
            ("BLUE", "blue", (220, 80, 0)),
            ("BLACK", "black", (20, 20, 20)),
            ("DRAW", "draw", (90, 90, 90)),
            ("ERASE", "eraser", (190, 190, 190)),
            ("NEON", "neon", (255, 0, 255)),
            ("RAIN", "rainbow", (0, 200, 255)),
            ("SPARK", "sparkle", (255, 255, 255)),
            ("FIRE", "fire", (0, 90, 255)),
            ("GLOW", "glow", (120, 255, 120)),
            ("CLEAR", "clear", (80, 80, 80)),
            ("SAVE", "save", (60, 140, 220)),
            # ("OCR", "ocr", (140, 90, 220)),
            # ("PIANO", "piano", (180, 120, 60)),
            # ("GAME", "game", (60, 160, 180)),
            # ("NEW", "new", (120, 120, 120)),
            # ("PREV", "prev", (120, 120, 120)),
            # ("NEXT", "next", (120, 120, 120)),
        ]
        self.buttons = []
        margin = 8
        button_w = max(58, (self.width - margin * 2) // 10 - 6)
        button_h = 34
        gap = 6
        for index, (label, action, color) in enumerate(specs):
            row = index // 10
            col = index % 10
            left = margin + col * (button_w + gap)
            top = margin + row * (button_h + gap)
            self.buttons.append(Button(label, action, (left, top, left + button_w, top + button_h), color))

    def _draw_toolbar(self, frame: np.ndarray, cursor: Optional[Point]) -> None:
        overlay = frame.copy()
        drawn_buttons = []
        for button in self.buttons:
            left, top, right, bottom = button.rect
            active = (
                button.action == self.mode
                or button.action == self.effect
                or button.action in self._color_actions()
                and self.color == self._color_actions()[button.action]
                and self.effect == "normal"
            )
            fill = button.color if active else tuple(max(0, channel - 45) for channel in button.color)
            if cursor and button.contains(cursor):
                fill = tuple(min(255, channel + 55) for channel in fill)
            cv2.rectangle(overlay, (left, top), (right, bottom), fill, -1)
            drawn_buttons.append((button, fill))
        cv2.addWeighted(overlay, 0.82, frame, 0.18, 0, frame)
        for button, fill in drawn_buttons:
            left, top, right, bottom = button.rect
            cv2.rectangle(frame, (left, top), (right, bottom), (245, 245, 245), 1)
            text_color = (255, 255, 255) if sum(fill) < 430 else (20, 20, 20)
            cv2.putText(frame, button.label, (left + 5, top + 23), cv2.FONT_HERSHEY_SIMPLEX, 0.46, text_color, 1, cv2.LINE_AA)

    def _draw_status(self, frame: np.ndarray, gesture: str, brush_size: int) -> None:
        page_text = f"Page {self.page_index + 1}/{len(self.pages)}"
        status = f"Gesture: {gesture} | Mode: {self.mode} | Effect: {self.effect} | Brush: {brush_size}px | {page_text}"
        y = self.height - 18
        cv2.rectangle(frame, (0, self.height - 42), (self.width, self.height), (0, 0, 0), -1)
        cv2.putText(frame, status, (12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (245, 245, 245), 1, cv2.LINE_AA)
        cv2.circle(frame, (self.width - 36, self.height - 22), min(22, max(4, brush_size // 2)), self._active_color(), 2)

    def _draw_message(self, frame: np.ndarray) -> None:
        text_size, _ = cv2.getTextSize(self.message, cv2.FONT_HERSHEY_SIMPLEX, 0.78, 2)
        x = max(12, (self.width - text_size[0]) // 2)
        y = 100
        cv2.rectangle(frame, (x - 14, y - 34), (x + text_size[0] + 14, y + 12), (25, 25, 25), -1)
        cv2.rectangle(frame, (x - 14, y - 34), (x + text_size[0] + 14, y + 12), (255, 255, 255), 1)
        cv2.putText(frame, self.message, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.78, (255, 255, 255), 2, cv2.LINE_AA)

    def _color_actions(self) -> Dict[str, Color]:
        return {
            "red": (0, 0, 255),
            "green": (0, 200, 0),
            "blue": (255, 90, 0),
            "black": (0, 0, 0),
            "purple": (255, 0, 255),
            "orange": (0, 165, 255),
        }

    def draw_mode_menu(
        self,
        frame: np.ndarray,
        cursor: Optional[Point],
        selection: str,
    ) -> None:
        # 1. Dim background with a sleek dark slate color
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (self.width, self.height), (12, 12, 18), -1)
        cv2.addWeighted(overlay, 0.76, frame, 0.24, 0, frame)

        # 2. Draw Title Header
        title_y = max(80, int(self.height * 0.16))
        # Draw a subtle neon accent line under title
        cv2.line(frame, (50, title_y + 15), (self.width - 50, title_y + 15), (60, 60, 65), 1)
        
        cv2.putText(
            frame,
            "VIRTUAL GESTURE STUDIO",
            (50, title_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.1,
            (255, 255, 255),
            3,
            cv2.LINE_AA,
        )
        
        # 3. Mode Cards layout
        box_y = max(140, int(self.height * 0.28))
        box_h = max(240, int(self.height * 0.38))
        gap = 36
        box_w = max(260, (self.width - gap * (len(MENU_OPTIONS) + 1)) // len(MENU_OPTIONS))
        total_width = len(MENU_OPTIONS) * box_w + (len(MENU_OPTIONS) - 1) * gap
        start_x = max(24, (self.width - total_width) // 2)

        for index, (mode, label) in enumerate(MENU_OPTIONS):
            left = start_x + index * (box_w + gap)
            right = left + box_w
            bottom = box_y + box_h
            highlighted = mode == selection
            
            # Draw Card Background
            # Use semi-transparent overlay for card background to keep the modern look
            card_overlay = frame.copy()
            fill = (36, 36, 44) if not highlighted else (54, 42, 30)
            cv2.rectangle(card_overlay, (left, box_y), (right, bottom), fill, -1)
            # Add card background transparency
            cv2.addWeighted(card_overlay, 0.85, frame, 0.15, 0, frame)

            # Draw Card Border (Neon highlight if hovered)
            border_color = (255, 140, 0) if highlighted else (80, 80, 90)  # Neon Orange / Slate Gray
            border_thickness = 3 if highlighted else 1
            cv2.rectangle(frame, (left, box_y), (right, bottom), border_color, border_thickness)

            # Draw Mode Label
            cv2.putText(
                frame,
                label,
                (left + 24, box_y + 45),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (255, 255, 255) if highlighted else (200, 200, 200),
                2,
                cv2.LINE_AA,
            )

            # Draw Subtitle/Description based on the mode
            desc = ""
            if mode == "draw":
                desc = "Brush, Neon & Shapes"
            elif mode == "piano":
                desc = "Play virtual notes"
            elif mode == "game":
                desc = "Slice spawning fruits"
                
            cv2.putText(
                frame,
                desc,
                (left + 24, box_y + 75),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.48,
                (200, 220, 255) if highlighted else (140, 140, 150),
                1,
                cv2.LINE_AA,
            )

            # Draw Mode Graphic/Icon inside the Card
            graphic_y_center = box_y + box_h - 75
            graphic_x_center = left + box_w // 2
            
            if mode == "draw":
                # Draw small color palette circles (Red, Green, Blue)
                r_c = (50, 50, 255)
                g_c = (50, 200, 50)
                b_c = (255, 100, 50)
                # Drawing concentric rings if highlighted
                if highlighted:
                    cv2.circle(frame, (graphic_x_center - 40, graphic_y_center), 18, (255, 255, 255), 1)
                    cv2.circle(frame, (graphic_x_center, graphic_y_center), 18, (255, 255, 255), 1)
                    cv2.circle(frame, (graphic_x_center + 40, graphic_y_center), 18, (255, 255, 255), 1)
                cv2.circle(frame, (graphic_x_center - 40, graphic_y_center), 14, r_c, -1)
                cv2.circle(frame, (graphic_x_center, graphic_y_center), 14, g_c, -1)
                cv2.circle(frame, (graphic_x_center + 40, graphic_y_center), 14, b_c, -1)
                
            elif mode == "piano":
                # Draw 4 piano keys
                key_width = 16
                key_height = 45
                start_k_x = graphic_x_center - (4 * key_width) // 2
                start_k_y = graphic_y_center - key_height // 2
                
                # Draw white keys
                for i in range(4):
                    k_left = start_k_x + i * key_width
                    k_right = k_left + key_width - 2
                    k_fill = (255, 255, 255) if highlighted else (220, 220, 220)
                    cv2.rectangle(frame, (k_left, start_k_y), (k_right, start_k_y + key_height), k_fill, -1)
                    cv2.rectangle(frame, (k_left, start_k_y), (k_right, start_k_y + key_height), (40, 40, 40), 1)
                # Draw black keys
                for i in range(3):
                    kb_left = start_k_x + i * key_width + key_width - key_width // 4
                    kb_right = kb_left + key_width // 2
                    cv2.rectangle(frame, (kb_left, start_k_y), (kb_right, start_k_y + int(key_height * 0.6)), (20, 20, 20), -1)

            elif mode == "game":
                # Draw sliced fruit graphic
                fruit_color = (0, 165, 255) if highlighted else (0, 120, 200) # Orange-ish fruit
                # Fruit circle
                cv2.circle(frame, (graphic_x_center, graphic_y_center), 22, fruit_color, -1)
                cv2.circle(frame, (graphic_x_center, graphic_y_center), 22, (255, 255, 255), 2)
                # Diagonal slice line
                cv2.line(frame, (graphic_x_center - 32, graphic_y_center + 18), (graphic_x_center + 32, graphic_y_center - 18), (255, 255, 255), 2)

        # 4. Draw pointer/cursor with glowing halo when active
        if cursor:
            # outer glow ring
            cv2.circle(frame, cursor, 22, (255, 140, 0), 1)
            cv2.circle(frame, cursor, 14, (255, 255, 255), 2)
            cv2.circle(frame, cursor, 5, (255, 255, 255), -1)
