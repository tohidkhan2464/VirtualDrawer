from __future__ import annotations

import argparse
import time
from typing import Optional

import cv2

from drawing_board import DrawingBoard

# from fruit_ninja import FruitNinjaMiniGame
from gesture_detector import GestureDetector, GestureState
from src.hand_tracker import HandTracker

# from handwriting_ocr import HandwritingOCR
# from virtual_piano import VirtualPiano
# from voice_commands import VoiceCommandListener


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Virtual Drawing Board using Hand Gestures"
    )
    parser.add_argument("--camera", type=int, default=0, help="Webcam device index")
    parser.add_argument(
        "--width", type=int, default=1280, help="Requested camera width"
    )
    parser.add_argument(
        "--height", type=int, default=720, help="Requested camera height"
    )
    parser.add_argument(
        "--no-landmarks", action="store_true", help="Hide MediaPipe hand landmarks"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cap = cv2.VideoCapture(args.camera)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera {args.camera}")

    tracker = HandTracker(max_hands=1)
    detector = GestureDetector()
    board = DrawingBoard()
    # piano = VirtualPiano()
    # game = FruitNinjaMiniGame()
    # ocr: Optional[HandwritingOCR] = None
    # voice: Optional[VoiceCommandListener] = None

    frame_number = 0
    last_clear_frame = -999
    current_brush_size = 8
    shape_hold = {"name": None, "frames": 0}
    fps_time = time.time()
    fps = 0.0

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                board.say("Camera frame unavailable")
                continue

            frame = cv2.flip(frame, 1)
            height, width = frame.shape[:2]
            board.ensure_size(width, height)
            # piano.ensure_layout(width, height)
            frame_number += 1

            hands = tracker.process(frame)
            hand = hands[0] if hands else None
            state = detector.detect(hand)
            if state.name == "brush_resize":
                current_brush_size = state.brush_size
                board.stop_stroke()

            print(
                f"Frame {frame_number}: Gesture={state.name}, Cursor={state.cursor}, Fingers={state.fingers}, Pinch={state.pinch_distance:.1f}, Brush={state.brush_size}, CurrentBrush={current_brush_size}"
            )

            if not args.no_landmarks:
                tracker.draw_landmarks(frame, hands)

            action = board.handle_toolbar(state.cursor, frame_number)
            if action:
                if action == "game":
                    # game.reset()
                    pass
                board.stop_stroke()

            _handle_gesture(board, state, frame_number, last_clear_frame)
            if state.name == "clear" and frame_number - last_clear_frame >= 45:
                last_clear_frame = frame_number

            if board.mode == "piano":
                board.stop_stroke()
                # piano.touch(state.cursor)
            elif board.mode == "game":
                board.stop_stroke()
                # game.update(width, height, state.cursor)
            elif not action:
                _draw_or_erase(board, state, current_brush_size)
                _maybe_draw_shape(board, state, shape_hold, current_brush_size)

            output = board.compose(frame)

            # if board.mode == "piano":
            # piano.draw(output, state.cursor)
            # elif board.mode == "game":
            # game.draw(output)

            now = time.time()
            elapsed = now - fps_time
            if elapsed >= 0.5:
                fps = 1.0 / max(0.0001, elapsed / max(1, frame_number % 30 or 30))
                fps_time = now

            board.draw_ui(output, state.cursor, state.name, current_brush_size)
            cv2.putText(
                output,
                f"FPS: {fps:.1f}",
                (width - 122, 28),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )
            cv2.imshow("Virtual Gesture Studio", output)

            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord("q")):
                break
            if key:
                # ocr, voice = _handle_key(key, board, ocr, voice, game)
                pass
    finally:
        tracker.close()
        cap.release()
        cv2.destroyAllWindows()


def _handle_gesture(
    board: DrawingBoard, state: GestureState, frame_number: int, last_clear_frame: int
) -> None:
    if state.name == "clear" and frame_number - last_clear_frame >= 45:
        board.clear()
        board.stop_stroke()
    elif state.name == "pause":
        board.stop_stroke()


def _draw_or_erase(
    board: DrawingBoard, state: GestureState, current_brush_size: int
) -> None:
    if state.cursor is None:
        board.stop_stroke()
        return
    if board.mode == "eraser" or state.name == "eraser":
        board.erase(state.cursor, current_brush_size)
    elif state.name == "draw" and board.mode == "draw":
        board.draw(state.cursor, current_brush_size)
    else:
        board.stop_stroke()


def _maybe_draw_shape(
    board: DrawingBoard,
    state: GestureState,
    shape_hold: dict,
    current_brush_size: int,
) -> None:
    if state.name == "brush_resize" or not state.shape or not state.cursor:
        shape_hold["name"] = None
        shape_hold["frames"] = 0
        return

    if shape_hold["name"] == state.shape:
        shape_hold["frames"] += 1
    else:
        shape_hold["name"] = state.shape
        shape_hold["frames"] = 1

    if shape_hold["frames"] == 24:
        board.draw_shape(state.shape, state.cursor, current_brush_size)
        board.stop_stroke()


# def _handle_key(
#     key: int,
#     board: DrawingBoard,
#     # ocr: Optional[HandwritingOCR],
#     # voice: Optional[VoiceCommandListener],
#     # game: FruitNinjaMiniGame,
# ):
#     if key == ord("c"):
#         board.clear()
#     elif key == ord("s"):
#         board.save()
#     elif key == ord("n"):
#         board.new_page()
#     elif key == ord("["):
#         board.previous_page()
#     elif key == ord("]"):
#         board.next_page()
#     # elif key == ord("p"):
#         # board.mode = "draw" if board.mode == "piano" else "piano"
#         # board.say(f"{board.mode.title()} mode")
#     elif key == ord("g"):
#         if board.mode == "game":
#             board.mode = "draw"
#         # else:
#             # board.mode = "game"
#             # game.reset()
#         # board.say(f"{board.mode.title()} mode")
#     # elif key == ord("o"):
#         # if ocr is None:
#             # ocr = HandwritingOCR()
#         # _, message = ocr.recognize(board.get_page_on_white())
#         # board.say(message, frames=120)
#     # elif key == ord("v"):
#         # if voice is None:
#             # voice = VoiceCommandListener()
#         # board.say("Listening...", frames=20)
#         # result = voice.listen_once()
#         # board.say(result.message, frames=120)
#         # if result.command:
#             # action = board.apply_voice_command(result.command)
#             # if action == "game":
#                 # game.reset()
#             # voice.speak(board.message)
#     # return ocr, voice


if __name__ == "__main__":
    main()
