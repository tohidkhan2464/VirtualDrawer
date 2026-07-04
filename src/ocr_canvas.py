from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple
import time
import cv2
import numpy as np

from .voice_commands import VoiceCommandListener

Point = Tuple[int, int]
Color = Tuple[int, int, int]


@dataclass
class OCRResult:
    text: str
    confidence: float


# OCR Canvas
class OCRCanvas:
    """Dedicated UI for Handwriting OCR."""

    def __init__(self, voice: VoiceCommandListener) -> None:
        self.width = 1280
        self.voice = voice
        self.height = 720
        self.paper_rect = (0, 0, 0, 0)
        self.result_rect = (0, 0, 0, 0)
        self.current_tool = "write"
        self.brush_size = 3
        self.recognized_text = ""
        self.confidence = 0.0
        self.hover_button: Optional[str] = None
        self.selected_button: Optional[str] = None
        self.last_button_press = 0.0
        self.button_cooldown = 0.35
        self.button_hover_progress = {}
        self.hover_start_time = 0.0
        self.page = np.ones((10, 10, 3), dtype=np.uint8) * 255
        self.last_point: Optional[Point] = None
        self.is_drawing = False
        self.paper_padding = 12
        self.cursor = None
        self.cursor_inside = False

        # Brush settings
        self.eraser_size = 12

        # UI colors
        self.paper_border_color = (255, 170, 0)
        self.paper_hover_color = (0, 220, 255)
        self.paper_bg = (250, 250, 250)
        self._create_layout()
        try:
            import easyocr
        except ImportError:  # pragma: no cover - optional dependency
            self.reader = None
            self.error = "EasyOCR is not installed. Run: python -m pip install easyocr"
        else:
            self.reader = easyocr.Reader(["en"], gpu=False)
            self.error = ""

    # Layout
    def ensure_size(self, width: int, height: int):
        if width == self.width and height == self.height:
            return
        self.width = width
        self.height = height
        self._create_layout()

    def _create_layout(self):
        margin = 30

        paper_x = 20
        paper_y = margin

        paper_w = self.width - 40
        paper_h = int(self.height * 0.72)

        result_y = paper_y + paper_h + 20
        result_h = self.height - result_y - margin

        self.paper_rect = (
            paper_x,
            paper_y,
            paper_w,
            paper_h,
        )

        self.result_rect = (
            paper_x,
            result_y,
            paper_w,
            result_h,
        )

        self.page = (
            np.ones(
                (
                    self.paper_rect[3],
                    self.paper_rect[2],
                    3,
                ),
                dtype=np.uint8,
            )
            * 255
        )

    def inside_paper(self, point: Optional[Point]) -> bool:
        if point is None:
            return False

        px, py = point
        x, y, w, h = self.paper_rect
        return x <= px < x + w and y <= py < y + h

    def can_press(self):
        return time.time() - self.last_button_press > self.button_cooldown

    def screen_to_page(self, point: Point) -> Point:
        x, y, _, _ = self.paper_rect
        return (point[0] - x, point[1] - y)

    def start_stroke(self):
        self.is_drawing = True

    def stop_stroke(self):
        self.is_drawing = False
        self.last_point = None

    def update(self, cursor: Optional[Point], gesture: str | None):
        """
        gesture should be:
            draw
            erase/color_menu
            None
        """
        self.cursor = cursor
        self.cursor_inside = self.inside_paper(cursor)
        if cursor is None:
            self.stop_stroke()
            return

        if not self.cursor_inside:
            self.stop_stroke()
            return

        if gesture not in ("draw", "color_menu"):
            self.stop_stroke()
            return

        self.current_tool = "erase" if gesture == "color_menu" else "write"
        # px = max(0, min(page_point[0], self.page.shape[1] - 1))
        # py = max(0, min(page_point[1], self.page.shape[0] - 1))
        # page_point = (px, py)
        page_point = self.screen_to_page(cursor)
        self.draw_point(page_point)

    def draw_point(self, point: Point):
        if self.last_point is None:
            self.last_point = point
            self.paint_pixel(point)
            return

        self.interpolate(self.last_point, point)
        self.last_point = point

    def interpolate(self, p1: Point, p2: Point):
        x1, y1 = p1
        x2, y2 = p2
        distance = int(np.hypot(x2 - x1, y2 - y1))

        if distance == 0:
            distance = 1

        for i in range(distance + 1):
            t = i / distance
            x = int(x1 + (x2 - x1) * t)
            y = int(y1 + (y2 - y1) * t)
            self.paint_pixel((x, y))

    def paint_pixel(self, point: Point):
        radius = self.eraser_size if self.current_tool == "erase" else self.brush_size
        color = (255, 255, 255) if self.current_tool == "erase" else (0, 0, 0)
        cv2.circle(
            self.page,
            point,
            radius,
            color,
            -1,
            cv2.LINE_AA,
        )

    def clear(self):
        self.page[:] = 255
        self.stop_stroke()
        self.recognized_text = ""
        self.confidence = 0.0

    def get_page(self):
        return self.page.copy()

    # Drawing
    def draw(self, frame: np.ndarray):
        self.draw_paper(frame)
        self.draw_cursor(frame)
        self.draw_result_panel(frame)

    # Paper
    def draw_paper(self, frame):
        x, y, w, h = self.paper_rect

        border = self.paper_hover_color if self.cursor_inside else self.paper_border_color

        # Draw slightly transparent paper background
        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (x, y),
            (x + w, y + h),
            self.paper_bg,
            -1,
            cv2.LINE_AA,
        )

        paper_alpha = 0.25  # Background transparency
        cv2.addWeighted(overlay, paper_alpha, frame, 1 - paper_alpha, 0, frame)

        # Blend the drawing page with the camera image
        page_alpha = 0.65  # Increase/decrease to control visibility of hand
        roi = frame[y : y + h, x : x + w]

        blended = cv2.addWeighted(
            self.page,
            page_alpha,
            roi,
            1 - page_alpha,
            0,
        )

        frame[y : y + h, x : x + w] = blended

        # Border
        cv2.rectangle(
            frame,
            (x, y),
            (x + w, y + h),
            border,
            3,
            cv2.LINE_AA,
        )

        # Title
        cv2.putText(
            frame,
            "Write Here",
            (x + 20, y - 12),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 170, 0),
            2,
            cv2.LINE_AA,
        )

    def draw_result_panel(self, frame):
        x, y, w, h = self.result_rect
        cv2.rectangle(
            frame,
            (x, y),
            (x + w, y + h),
            (32, 32, 32),
            -1,
            cv2.LINE_AA,
        )
        cv2.rectangle(
            frame,
            (x, y),
            (x + w, y + h),
            (255, 170, 0),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            "Recognized Text",
            (x + 15, y + 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        if self.recognized_text:
            cv2.putText(
                frame,
                self.recognized_text,
                (x + 20, y + 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )
            cv2.putText(
                frame,
                f"Confidence : {self.confidence:.1f}%",
                (x + 20, y + 105),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (220, 220, 220),
                1,
                cv2.LINE_AA,
            )

    def draw_cursor(self, frame):
        if self.cursor is None:
            return

        if not self.cursor_inside:
            return

        radius = self.eraser_size if self.current_tool == "erase" else self.brush_size
        color = (0, 0, 255) if self.current_tool == "erase" else (0, 180, 255)
        cv2.circle(
            frame,
            self.cursor,
            radius,
            color,
            2,
            cv2.LINE_AA,
        )

        cv2.circle(
            frame,
            self.cursor,
            2,
            color,
            -1,
            cv2.LINE_AA,
        )

    def recognize(self, image_bgr: np.ndarray) -> Tuple[List[OCRResult], str]:
        if self.reader is None:
            return [], self.error

        detections = self.reader.readtext(image_bgr)
        results = [
            OCRResult(text=str(text), confidence=float(confidence))
            for _, text, confidence in detections
            if str(text).strip()
        ]
        if not results:
            return [], "No text recognized"
        summary = " ".join(result.text for result in results)
        return results, f"Recognized: {summary}"

    def copy_to_clipboard(self, text: str) -> bool:
        if not text.strip():
            return False
        try:
            import tkinter as tk

            r = tk.Tk()
            r.withdraw()
            r.clipboard_clear()
            r.clipboard_append(text)
            r.update()
            r.destroy()
            return True
        except Exception:
            return False

