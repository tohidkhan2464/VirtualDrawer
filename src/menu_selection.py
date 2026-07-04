from __future__ import annotations
from typing import  Optional, Tuple
import cv2
import numpy as np

Color = Tuple[int, int, int]
Point = Tuple[int, int]


MENU_OPTIONS = (
    ("draw", "Drawing"),
    ("piano", "Piano"),
    ("game", "Game"),
    ("ocr", "OCR Mode"),
)


class MenuSelection:
    def __init__(self) -> None:
        self.width = 0
        self.height = 0
        self.mode = "draw"
        self.message = "Ready"
        self.message_frames = 0

    def scale(self, value: int) -> int:
        base_w = 1920
        base_h = 1080
        sx = self.width / base_w
        sy = self.height / base_h
        scale = min(sx, sy)
        return max(1, int(value * scale))

    def _draw_message(self, frame: np.ndarray) -> None:
        text_size, _ = cv2.getTextSize(self.message, cv2.FONT_HERSHEY_SIMPLEX, 0.78, 2)
        x = max(12, (self.width - text_size[0]) // 2)
        y = 100
        cv2.rectangle(
            frame, (x - 14, y - 34), (x + text_size[0] + 14, y + 12), (25, 25, 25), -1
        )
        cv2.rectangle(
            frame, (x - 14, y - 34), (x + text_size[0] + 14, y + 12), (255, 255, 255), 1
        )
        cv2.putText(
            frame,
            self.message,
            (x, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.78,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )


    def set_mode(self, mode: str) -> None:
        self.mode = mode
        
    def ensure_size(self, width: int, height: int) -> None:
        if self.width == width and self.height == height:
            return
        self.width = width
        self.height = height


    def draw_mode_menu(
        self,
        frame: np.ndarray,
        cursor: Optional[Point],
        selection: str,
    ) -> None:

        base_w = 1920
        base_h = 1080
        sx = self.width / base_w
        sy = self.height / base_h
        scale = min(sx, sy)

        # BACKGROUND
        blurred = cv2.GaussianBlur(frame, (41, 41), 0)
        dark_overlay = blurred.copy()

        cv2.rectangle(
            dark_overlay,
            (0, 0),
            (self.width, self.height),
            (18, 20, 25),
            -1,
        )

        cv2.addWeighted(
            dark_overlay,
            0.82,
            blurred,
            0.18,
            0,
            frame,
        )

        # HEADER
        title = "VIRTUAL GESTURE STUDIO"
        cv2.putText(
            frame,
            title,
            (self.scale(50), self.scale(80)),
            cv2.FONT_HERSHEY_DUPLEX,
            1.2 * scale,
            (255, 255, 255),
            self.scale(2),
            cv2.LINE_AA,
        )

        cv2.putText(
            frame,
            "Select a mode using gesture control",
            (self.scale(52), self.scale(115)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55 * scale,
            (180, 180, 180),
            self.scale(1),
            cv2.LINE_AA,
        )

        cv2.line(
            frame,
            (self.scale(40), self.scale(145)),
            (self.width - self.scale(40), self.scale(145)),
            (70, 70, 70),
            self.scale(1),
        )

        # CARD LAYOUT
        cols = 3
        card_w = self.scale(340)
        card_h = self.scale(260)
        gap_x = self.scale(35)
        gap_y = self.scale(35)
        start_y = self.scale(190)
        total_width = cols * card_w + (cols - 1) * gap_x
        start_x = (self.width - total_width) // 2
        descriptions = {
            "draw": "Brush, Neon & Shapes",
            "piano": "Play virtual notes",
            "game": "Slice spawning fruits",
            "ocr": "Recognize text",
        }

        # DRAW CARDS
        for index, (mode, label) in enumerate(MENU_OPTIONS):
            row = index // cols
            col = index % cols

            # Center second row automatically
            if row == 1:

                row_items = len(MENU_OPTIONS) - cols

                row_width = row_items * card_w + (row_items - 1) * gap_x

                row_start_x = (self.width - row_width) // 2

                left = row_start_x + (col * (card_w + gap_x))

            else:
                left = start_x + (col * (card_w + gap_x))

            top = start_y + (row * (card_h + gap_y))

            right = left + card_w
            bottom = top + card_h

            highlighted = mode == selection

            # HOVER ANIMATION
            hover = self.scale(10) if highlighted else 0

            left -= hover
            top -= hover
            right += hover
            bottom += hover

            # GLASS CARD
            card_overlay = frame.copy()

            if highlighted:
                fill = (55, 45, 30)
                border = (0, 180, 255)
                alpha = 0.72
            else:
                fill = (40, 42, 48)
                border = (90, 95, 105)
                alpha = 0.55

            cv2.rectangle(
                card_overlay,
                (left, top),
                (right, bottom),
                fill,
                -1,
            )

            cv2.addWeighted(
                card_overlay,
                alpha,
                frame,
                1 - alpha,
                0,
                frame,
            )

            cv2.rectangle(
                frame,
                (left, top),
                (right, bottom),
                border,
                self.scale(3 if highlighted else 1),
            )

            # TITLE
            cv2.putText(
                frame,
                label,
                (left + self.scale(24), top + self.scale(42)),
                cv2.FONT_HERSHEY_DUPLEX,
                1.1 * scale,
                (255, 255, 255),
                self.scale(2),
                cv2.LINE_AA,
            )

            cv2.putText(
                frame,
                descriptions.get(mode, ""),
                (left + self.scale(24), top + self.scale(78)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.48 * scale,
                (185, 185, 185),
                self.scale(1),
                cv2.LINE_AA,
            )

            center_x = (left + right) // 2
            center_y = top + int(card_h * 0.68)

            # DRAW ICON
            if mode == "draw":

                colors = [
                    (50, 80, 255),
                    (50, 220, 100),
                    (255, 140, 50),
                ]

                offsets = [-self.scale(55), 0, self.scale(55)]

                for off, color in zip(offsets, colors):

                    cv2.circle(
                        frame,
                        (center_x + off, center_y),
                        self.scale(22),
                        (255, 255, 255),
                        self.scale(1),
                    )

                    cv2.circle(
                        frame,
                        (center_x + off, center_y),
                        self.scale(16),
                        color,
                        -1,
                    )

            # PIANO ICON
            elif mode == "piano":

                key_w = self.scale(24)
                key_h = self.scale(70)

                start_x_key = center_x - self.scale(48)

                for i in range(4):

                    x1 = start_x_key + i * key_w

                    cv2.rectangle(
                        frame,
                        (x1, center_y - key_h // 2),
                        (x1 + key_w, center_y + key_h // 2),
                        (255, 255, 255),
                        -1,
                    )

                    cv2.rectangle(
                        frame,
                        (x1, center_y - key_h // 2),
                        (x1 + key_w, center_y + key_h // 2),
                        (40, 40, 40),
                        self.scale(1),
                    )

                for i in range(3):

                    bx = start_x_key + i * key_w + self.scale(15)

                    cv2.rectangle(
                        frame,
                        (bx, center_y - key_h // 2),
                        (bx + self.scale(12), center_y),
                        (15, 15, 15),
                        -1,
                    )

            # GAME ICON
            elif mode == "game":

                cv2.circle(
                    frame,
                    (center_x, center_y),
                    self.scale(30),
                    (0, 165, 255),
                    -1,
                )

                cv2.circle(
                    frame,
                    (center_x, center_y),
                    self.scale(30),
                    (255, 255, 255),
                    self.scale(2),
                )

                cv2.line(
                    frame,
                    (center_x - self.scale(45), center_y + self.scale(22)),
                    (center_x + self.scale(45), center_y - self.scale(22)),
                    (255, 255, 255),
                    self.scale(4),
                )

            # OCR ICON
            elif mode == "ocr":

                cv2.rectangle(
                    frame,
                    (center_x - self.scale(45), center_y - self.scale(45)),
                    (center_x + self.scale(45), center_y + self.scale(45)),
                    (240, 240, 240),
                    -1,
                )

                cv2.rectangle(
                    frame,
                    (center_x - self.scale(45), center_y - self.scale(45)),
                    (center_x + self.scale(45), center_y + self.scale(45)),
                    (120, 120, 120),
                    self.scale(2),
                )

                cv2.putText(
                    frame,
                    "OCR",
                    (center_x - self.scale(28), center_y + self.scale(10)),
                    cv2.FONT_HERSHEY_DUPLEX,
                    0.8 * scale,
                    (50, 50, 50),
                    self.scale(2),
                    cv2.LINE_AA,
                )


        # CURSOR
        if cursor:
            cv2.circle(
                frame,
                cursor,
                self.scale(24),
                (0, 180, 255),
                self.scale(2),
            )

            cv2.circle(
                frame,
                cursor,
                self.scale(12),
                (255, 255, 255),
                self.scale(2),
            )

            cv2.circle(
                frame,
                cursor,
                self.scale(4),
                (255, 255, 255),
                -1,
            )

        if self.message_frames > 0:
            self._draw_message(frame)
            self.message_frames -= 1