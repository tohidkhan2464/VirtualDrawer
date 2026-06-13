from __future__ import annotations

import argparse
import time
import math
from typing import Optional

import cv2

from src.drawing_board import DrawingBoard, MENU_OPTIONS
from src.fruit_ninja import FruitNinjaMiniGame
from src.gesture_detector import GestureDetector, GestureState
from src.hand_tracker import HandTracker
from src.handwriting_ocr import HandwritingOCR
from src.virtual_piano import VirtualPiano
from src.voice_commands import VoiceCommandListener


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

    # Explicitly track up to 2 hands
    tracker = HandTracker(max_hands=2)
    detector = GestureDetector()
    board = DrawingBoard()
    piano = VirtualPiano()
    game = FruitNinjaMiniGame()
    ocr = HandwritingOCR()
    voice = VoiceCommandListener()

    frame_number = 0
    current_brush_size = 8
    app_state = "menu"
    fps_time = time.time()
    fps = 0.0

    menu_selection = "draw"
    menu_cursor = None

    # Hold tracking variables
    gesture_start_times = {}
    gesture_triggered = {}

    # State transition flags
    pinky_toggled = False
    pinch_started = False
    pinch_start_dist = 0.0
    pinch_start_brush = 8

    # Octave/Instrument cooldowns
    last_octave_change_time = 0.0
    last_instrument_change_time = 0.0

    # OCR variables
    ocr_text_result = ""
    ocr_copied = False
    ocr_spoken = False

    # Voice variables
    last_voice_command = ""
    voice_command_repeated = False

    # Idle timer
    last_hand_seen_time = time.time()

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                board.say("Camera frame unavailable")
                continue

            frame = cv2.flip(frame, 1)
            height, width = frame.shape[:2]
            board.ensure_size(width, height)
            piano.ensure_layout(width, height)
            frame_number += 1

            # Process both hands
            hands = tracker.process(frame)
            state = detector.detect(hands)

            # Global Idle Timer: returns to menu after 3 seconds of no hands
            now = time.time()
            if hands:
                last_hand_seen_time = now
                idle_active = False
            else:
                idle_active = (now - last_hand_seen_time) > 3.0

            if idle_active:
                if app_state != "menu" or board.mode != "draw":
                    app_state = "menu"
                    board.mode = "draw"
                    board.stop_stroke()
                    board.say("System Idle", frames=120)

            if not args.no_landmarks:
                tracker.draw_landmarks(frame, hands)

            # Compose output frame (merge canvas layer)
            output = board.compose(frame)

            # Define active hold gestures for timing
            active_gestures = []
            if state.left_name == "fist":
                active_gestures.append("left_fist")
            if state.left_name == "thumb_up":
                active_gestures.append("left_thumb_up")
            if state.left_name == "open_palm":
                active_gestures.append("left_open_palm")
            if state.left_name == "pinky_up":
                active_gestures.append("left_pinky_up")
            if state.left_name == "rock":
                active_gestures.append("left_rock")
            if state.two_handed_name == "both_open_palms":
                active_gestures.append("both_open_palms")
            if state.two_handed_name == "both_thumbs_up":
                active_gestures.append("both_thumbs_up")

            # Manage hold timings
            for g in list(gesture_start_times.keys()):
                if g not in active_gestures:
                    gesture_start_times.pop(g, None)
                    gesture_triggered.pop(g, None)
            for g in active_gestures:
                if g not in gesture_start_times:
                    gesture_start_times[g] = now
                    gesture_triggered[g] = False

            if not idle_active:
                # ------------------- STATE: MENU -------------------
                if app_state == "menu":
                    board.stop_stroke()
                    # Point with Right Index
                    if state.cursor:
                        menu_cursor = state.cursor
                        menu_selection = _menu_selection_for_cursor(menu_cursor, width)
                    else:
                        menu_cursor = None

                    # Select with Right Index + Middle UP
                    if state.name == "select":
                        _activate_mode(board, menu_selection, game)
                        app_state = "active"
                        board.say(f"{menu_selection.upper()} mode")

                # ------------------- STATE: ACTIVE -------------------
                else:
                    # Return to Mode Menu with Right Index + Middle + Ring UP
                    if state.name == "return":
                        app_state = "menu"
                        board.mode = "draw"
                        board.stop_stroke()
                        board.say("Mode menu")
                        menu_cursor = None
                    else:
                        # 1. Mode: Drawing Board
                        if board.mode in ("draw", "eraser"):
                            # Left Fist -> Undo (0.8s hold)
                            if "left_fist" in gesture_start_times and not gesture_triggered.get("left_fist", True):
                                if now - gesture_start_times["left_fist"] >= 0.8:
                                    board.undo()
                                    gesture_triggered["left_fist"] = True

                            # Left Thumb UP -> Redo (0.8s hold)
                            if "left_thumb_up" in gesture_start_times and not gesture_triggered.get("left_thumb_up", True):
                                if now - gesture_start_times["left_thumb_up"] >= 0.8:
                                    board.redo()
                                    gesture_triggered["left_thumb_up"] = True

                            # Both Open Palms -> Clear (2.0s hold)
                            if "both_open_palms" in gesture_start_times and not gesture_triggered.get("both_open_palms", True):
                                if now - gesture_start_times["both_open_palms"] >= 2.0:
                                    board.clear()
                                    gesture_triggered["both_open_palms"] = True

                            # Both Thumbs Up -> Save (1.0s hold)
                            if "both_thumbs_up" in gesture_start_times and not gesture_triggered.get("both_thumbs_up", True):
                                if now - gesture_start_times["both_thumbs_up"] >= 1.0:
                                    board.save()
                                    gesture_triggered["both_thumbs_up"] = True

                            # Left Pinky UP -> Toggle Eraser
                            if state.left_name == "pinky_up":
                                if not pinky_toggled:
                                    if board.mode == "eraser":
                                        board.mode = "draw"
                                        board.say("Drawing Mode")
                                    else:
                                        board.mode = "eraser"
                                        board.say("Eraser Mode")
                                    pinky_toggled = True
                            else:
                                pinky_toggled = False

                            # Left Pinch -> Brush size control
                            if state.left_name == "pinch":
                                if not pinch_started:
                                    pinch_start_dist = state.left_pinch_distance
                                    pinch_start_brush = current_brush_size
                                    pinch_started = True
                                else:
                                    diff = state.left_pinch_distance - pinch_start_dist
                                    current_brush_size = max(board.min_brush, min(board.max_brush, int(pinch_start_brush + diff * 0.2)))
                            else:
                                pinch_started = False

                            # Left Color Menu Pop-up (Index + Middle + Pinky)
                            board.show_color_menu = (state.left_name == "color_menu")
                            if board.show_color_menu:
                                hovered_color = board.draw_color_palette(output, state.cursor)
                                if hovered_color and state.name == "select":
                                    board.color = board._color_actions().get(hovered_color, board.color)
                                    board.effect = "normal"
                                    board.mode = "draw"
                                    board.show_color_menu = False
                                    board.say(f"{hovered_color.title()} selected")

                            # Handle Toolbar Button Clicks
                            action = board.handle_toolbar(state.cursor, frame_number)
                            if action:
                                if action == "game":
                                    game.reset()
                                board.stop_stroke()

                            # Draw or Erase
                            if not board.show_color_menu and not action:
                                _draw_or_erase(board, state, current_brush_size)

                        # 2. Mode: Virtual Piano
                        elif board.mode == "piano":
                            board.stop_stroke()
                            # Sustain pedal (Left Hand Open Palm)
                            sustain = (state.left_name == "open_palm")
                            piano.touch(state.cursor, sustain_active=sustain)

                            # Octave Up (Left Hand Thumb UP, cooldown 1s)
                            if state.left_name == "thumb_up":
                                if now - last_octave_change_time > 1.0:
                                    piano.change_octave(1)
                                    last_octave_change_time = now
                                    board.say(f"Octave: {piano.octave_offset:+d}")
                            # Octave Down (Left Hand Pinky UP, cooldown 1s)
                            elif state.left_name == "pinky_up":
                                if now - last_octave_change_time > 1.0:
                                    piano.change_octave(-1)
                                    last_octave_change_time = now
                                    board.say(f"Octave: {piano.octave_offset:+d}")

                            # Instrument Change (Left Hand Rock Sign, cooldown 1s)
                            if state.left_name == "rock":
                                if now - last_instrument_change_time > 1.0:
                                    piano.next_instrument()
                                    last_instrument_change_time = now
                                    board.say(f"Instrument: {piano.instruments[piano.instrument_index]}")

                        # 3. Mode: Fruit Ninja
                        elif board.mode == "game":
                            board.stop_stroke()
                            # Restart Game (Both Thumbs Up held for 2.0s)
                            if "both_thumbs_up" in gesture_start_times and not gesture_triggered.get("both_thumbs_up", True):
                                if now - gesture_start_times["both_thumbs_up"] >= 2.0:
                                    game.reset()
                                    gesture_triggered["both_thumbs_up"] = True

                            # Update game mechanics
                            game.update(
                                width,
                                height,
                                cutter=state.cursor if state.name == "draw" else None,
                                shield_pressed=(state.left_name == "fist"),
                                slow_mo_pressed=(state.left_name == "open_palm")
                            )

                        # 4. Mode: Handwriting OCR
                        elif board.mode == "ocr":
                            # Draw strokes inside the OCR area
                            _draw_or_erase(board, state, current_brush_size)

                            # Start Recognition (Left Open Palm held for 1.0s)
                            if "left_open_palm" in gesture_start_times and not gesture_triggered.get("left_open_palm", True):
                                if now - gesture_start_times["left_open_palm"] >= 1.0:
                                    results, msg = ocr.recognize(board.get_page_on_white())
                                    board.say(msg, frames=150)
                                    ocr_text_result = " ".join(r.text for r in results)
                                    gesture_triggered["left_open_palm"] = True

                            # Copy Result (Left Hand Thumb UP)
                            if state.left_name == "thumb_up":
                                if not ocr_copied:
                                    if ocr_text_result:
                                        success = ocr.copy_to_clipboard(ocr_text_result)
                                        if success:
                                            board.say("Copied text to clipboard!", frames=100)
                                        else:
                                            board.say("Failed to copy text", frames=100)
                                    ocr_copied = True
                            else:
                                ocr_copied = False

                            # Read Aloud (Left Hand Rock Sign)
                            if state.left_name == "rock":
                                if not ocr_spoken:
                                    if ocr_text_result:
                                        ocr.speak_text(ocr_text_result)
                                        board.say("Reading aloud...", frames=100)
                                    ocr_spoken = True
                            else:
                                ocr_spoken = False

                            # Clear OCR Area (Both Open Palms held for 2.0s)
                            if "both_open_palms" in gesture_start_times and not gesture_triggered.get("both_open_palms", True):
                                if now - gesture_start_times["both_open_palms"] >= 2.0:
                                    board.clear()
                                    ocr_text_result = ""
                                    board.say("OCR Canvas Cleared")
                                    gesture_triggered["both_open_palms"] = True

                        # 5. Mode: Voice Command
                        elif board.mode == "voice":
                            board.stop_stroke()
                            # Start Listening (Left Hand Open Palm)
                            if state.left_name == "open_palm":
                                if not voice.is_currently_listening:
                                    voice.start_listening_background()
                                    board.say("Listening...", frames=25)
                            # Stop Listening (Left Hand Closed Fist)
                            elif state.left_name == "fist":
                                if voice.is_currently_listening:
                                    voice.stop_listening_background()
                                    board.say("Listening stopped", frames=100)
                            # Repeat Last Command (Left Hand Thumb UP)
                            elif state.left_name == "thumb_up":
                                if not voice_command_repeated:
                                    if last_voice_command:
                                        board.say(f"Repeating: {last_voice_command}", frames=100)
                                        action = board.apply_voice_command(last_voice_command)
                                        if action == "game":
                                            game.reset()
                                        voice.speak(board.message)
                                    else:
                                        board.say("No command to repeat", frames=100)
                                    voice_command_repeated = True
                            else:
                                voice_command_repeated = False

                            # Retrieve background commands
                            v_res = voice.get_result()
                            if v_res:
                                board.say(v_res.message, frames=150)
                                if v_res.command:
                                    last_voice_command = v_res.command
                                    action = board.apply_voice_command(v_res.command)
                                    if action == "game":
                                        game.reset()
                                    voice.speak(board.message)

            # Draw active mode HUD and overlays
            if app_state == "menu":
                board.draw_mode_menu(output, menu_cursor, menu_selection)
            elif board.mode == "piano":
                piano.draw(output, state.cursor)
            elif board.mode == "game":
                game.draw(output)
            elif board.mode == "ocr":
                # Draw handwriting bounding zone
                cx, cy = width // 2, height // 2
                cv2.rectangle(output, (cx - 280, cy - 180), (cx + 280, cy + 180), (255, 165, 0), 2, cv2.LINE_4)
                cv2.putText(output, "OCR Zone - Write Here", (cx - 270, cy - 195), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 165, 0), 1, cv2.LINE_AA)
                # Show recognized text block
                if ocr_text_result:
                    cv2.rectangle(output, (cx - 300, height - 120), (cx + 300, height - 55), (35, 30, 25), -1)
                    cv2.rectangle(output, (cx - 300, height - 120), (cx + 300, height - 55), (255, 165, 0), 1)
                    cv2.putText(output, f"Recognized: {ocr_text_result[:45]}...", (cx - 280, height - 85), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
            elif board.mode == "voice":
                cx, cy = width // 2, height // 2
                # Pulsing mic icon
                if voice.is_currently_listening:
                    pulse = int(24 + 6 * math.sin(time.time() * 8))
                    cv2.circle(output, (cx, cy - 40), pulse, (0, 0, 255), -1)
                    cv2.circle(output, (cx, cy - 40), pulse + 6, (0, 0, 150), 2)
                    cv2.putText(output, "LISTENING...", (cx - 55, cy + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2, cv2.LINE_AA)
                else:
                    cv2.circle(output, (cx, cy - 40), 24, (100, 100, 100), -1)
                    cv2.putText(output, "Open Palm: Listen | Fist: Stop | Thumb UP: Repeat", (cx - 200, cy + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1, cv2.LINE_AA)
                
                if last_voice_command:
                    cv2.putText(output, f"Last Command: {last_voice_command}", (cx - 150, cy + 70), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (100, 255, 100), 1, cv2.LINE_AA)

            # Draw progress rings for hold gestures
            if state.cursor:
                for g, threshold in [("left_fist", 0.8), ("left_thumb_up", 0.8), ("both_open_palms", 2.0), ("both_thumbs_up", 1.0 if board.mode in ("draw", "eraser") else 2.0), ("left_open_palm", 1.0)]:
                    if g in gesture_start_times and not gesture_triggered.get(g, True):
                        elapsed = now - gesture_start_times[g]
                        progress = min(1.0, elapsed / threshold)
                        angle = int(progress * 360)
                        cursor_pos = state.cursor
                        if g.startswith("left_") and state.left_cursor:
                            cursor_pos = state.left_cursor
                        cv2.ellipse(output, cursor_pos, (30, 30), 0, -90, -90 + angle, (0, 255, 255), 3, cv2.LINE_AA)

            # Overlay System Idle screensaver
            if idle_active:
                overlay = output.copy()
                cv2.rectangle(overlay, (0, 0), (width, height), (12, 12, 18), -1)
                cv2.addWeighted(overlay, 0.82, output, 0.18, 0, output)
                cv2.putText(output, "SYSTEM IDLE", (width // 2 - 100, height // 2 - 20), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (180, 180, 200), 3, cv2.LINE_AA)
                cv2.putText(output, "Show hand to wake up", (width // 2 - 120, height // 2 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (140, 140, 150), 1, cv2.LINE_AA)

            # Calculate and draw FPS
            now_fps = time.time()
            elapsed = now_fps - fps_time
            if elapsed >= 0.5:
                fps = 1.0 / max(0.0001, elapsed / max(1, frame_number % 30 or 30))
                fps_time = now_fps

            if app_state == "menu":
                cv2.putText(
                    output,
                    "Index to point. Index + Middle selects. Index + Middle + Ring returns here.",
                    (28, 38),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.56,
                    (245, 245, 245),
                    1,
                    cv2.LINE_AA,
                )
            else:
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
                ocr, voice, app_state = _handle_key(key, board, ocr, voice, game, app_state)
    finally:
        tracker.close()
        cap.release()
        cv2.destroyAllWindows()


def _draw_or_erase(
    board: DrawingBoard, state: GestureState, current_brush_size: int
) -> None:
    if state.cursor is None:
        board.stop_stroke()
        return

    if board.mode == "eraser":
        if state.name == "draw":
            board.erase(state.cursor, current_brush_size)
        else:
            board.stop_stroke()
    elif board.mode in ("draw", "ocr"):
        if state.name == "draw":
            board.draw(state.cursor, current_brush_size)
        else:
            board.stop_stroke()
    else:
        board.stop_stroke()


def _menu_selection_for_cursor(cursor, width: int) -> str:
    if cursor is None or width <= 0:
        return MENU_OPTIONS[0][0]

    option_width = width / len(MENU_OPTIONS)
    index = int(cursor[0] / max(1.0, option_width))
    index = max(0, min(len(MENU_OPTIONS) - 1, index))
    return MENU_OPTIONS[index][0]


def _activate_mode(board: DrawingBoard, mode: str, game: FruitNinjaMiniGame) -> None:
    if mode == "draw":
        board.mode = "draw"
        board.color = (0, 0, 255)
        board.effect = "normal"
    elif mode == "piano":
        board.mode = "piano"
    elif mode == "game":
        board.mode = "game"
        game.reset()
    elif mode == "ocr":
        board.mode = "ocr"
    elif mode == "voice":
        board.mode = "voice"
    board.stop_stroke()


def _handle_key(
    key: int,
    board: DrawingBoard,
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


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
