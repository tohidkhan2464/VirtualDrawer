from __future__ import annotations

import argparse
import time
import math
from typing import Optional

import cv2

from src.menu_selection import MenuSelection, MENU_OPTIONS
from src.drawing_canvas import DrawingCanvas
from src.fruit_ninja import FruitNinjaMiniGame
from src.gesture_detector import GestureDetector, GestureState
from src.hand_tracker import HandTracker
from src.handwriting_ocr import HandwritingOCR
from src.virtual_piano import VirtualPiano
from src.voice_commands import VoiceCommandListener


def draw_or_erase(
    canvas: DrawingCanvas, state: GestureState, current_brush_size: int
) -> None:
    if state.right_cursor is None:
        canvas.stop_stroke()
        return

    if state.right_name == "draw":
        if canvas.tool == "eraser":
            canvas.erase(state.right_cursor, current_brush_size)
        else:
            canvas.draw(state.right_cursor, current_brush_size)
    else:
        canvas.stop_stroke()


def menu_selection_for_cursor(cursor, width: int) -> str:
    if cursor is None or width <= 0:
        return MENU_OPTIONS[0][0]

    option_width = width / len(MENU_OPTIONS)
    index = int(cursor[0] / max(1.0, option_width))
    index = max(0, min(len(MENU_OPTIONS) - 1, index))
    return MENU_OPTIONS[index][0]


def activate_mode(
    board: DrawingCanvas, menu: MenuSelection, mode: str, game: FruitNinjaMiniGame
) -> None:
    if mode == "draw":
        menu.mode = "draw"
        menu.set_mode("draw")
        board.color = (0, 0, 255)
        board.tool = "pencil"
        board.effect = "normal"
    elif mode == "piano":
        menu.mode = "piano"
        menu.set_mode("piano")
    elif mode == "game":
        menu.mode = "game"
        menu.set_mode("game")
        game.reset()
    elif mode == "ocr":
        menu.mode = "ocr"
        menu.set_mode("ocr")
    elif mode == "voice":
        menu.mode = "voice"
        menu.set_mode("voice")
    board.stop_stroke()


def handle_key(
    key: int,
    board: DrawingCanvas,
    ocr: Optional[HandwritingOCR],
    voice: Optional[VoiceCommandListener],
    game: FruitNinjaMiniGame,
    app_state: str,
):
    if key == ord("c"):
        board.clear()
    elif key == ord("s"):
        board.save()
    elif key == ord("n"):
        board.new_page()
    elif key == ord("["):
        board.previous_page()
    elif key == ord("]"):
        board.next_page()
    elif key == ord("p"):
        board.mode = "draw" if board.mode == "piano" else "piano"
        board.say(f"{board.mode.title()} mode")
        app_state = "active"
    elif key == ord("g"):
        if board.mode == "game":
            board.mode = "draw"
        else:
            board.mode = "game"
            game.reset()
        board.say(f"{board.mode.title()} mode")
        app_state = "active"
    elif key == ord("o"):
        if ocr is None:
            ocr = HandwritingOCR()
        board.mode = "ocr"
        board.say("OCR mode")
        app_state = "active"
    elif key == ord("v"):
        if voice is None:
            voice = VoiceCommandListener()
        board.mode = "voice"
        board.say("Voice mode")
        app_state = "active"
    return ocr, voice, app_state
