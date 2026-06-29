from __future__ import annotations

import argparse
import time
import math
from typing import Optional

import cv2

from src.menu_selection import MenuSelection, MENU_OPTIONS
from src.drawing_canvas import DrawingCanvas
from src.game import FruitNinjaMiniGame
from src.gesture_detector import GestureDetector, GestureState
from src.hand_tracker import HandTracker
from src.handwriting_ocr import HandwritingOCR
from src.virtual_piano import VirtualPiano
from src.voice_commands import VoiceCommandListener
from src.utils.utility_functions import (
    draw_or_erase,
    menu_selection_for_cursor,
    activate_mode,
    handle_key,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Virtual Drawing Board using Hand Gestures"
    )
    parser.add_argument("--camera", type=int, default=0, help="Webcam device index")
    parser.add_argument("--width", type=int, default=1920, help="Requested camera width")
    parser.add_argument(
        "--height", type=int, default=1080, help="Requested camera height"
    )
    parser.add_argument(
        "--no-landmarks", action="store_true", help="Hide MediaPipe hand landmarks"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cv2.namedWindow("Virtual Gesture Studio", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(
        "Virtual Gesture Studio",
        cv2.WND_PROP_FULLSCREEN,
        cv2.WINDOW_NORMAL,
    )

    cv2.namedWindow("Virtual Gesture Studio", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Virtual Gesture Studio", 1920, 1080)
    cap = cv2.VideoCapture(args.camera)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera {args.camera}")

    # Explicitly track up to 2 hands
    tracker = HandTracker(max_hands=2)
    detector = GestureDetector()
    menu = MenuSelection()
    canvas = DrawingCanvas()

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
    last_volume_change_time = 0.0
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
                menu.say("Camera frame unavailable")
                continue

            frame = cv2.flip(frame, 1)
            height, width = frame.shape[:2]
            menu.ensure_size(width, height)
            canvas.ensure_size(width, height)
            piano.ensure_layout(width, height)
            frame_number += 1

            # Process both hands
            hands = tracker.process(frame)
            state = detector.detect(hands)

            # Global Idle Timer: returns to menu after 10 seconds of no hands
            now = time.time()
            if hands:
                last_hand_seen_time = now
                idle_active = False
            else:
                idle_active = (now - last_hand_seen_time) > 10.0

            if idle_active:
                if app_state != "menu":
                    game.sound.stop_music()
                    app_state = "menu"
                    menu.say("System Idle", frames=120)

            if not args.no_landmarks:
                tracker.draw_landmarks(frame, hands)

            if menu.mode in ("draw", "ocr"):
                output = canvas.compose(frame)
            else:
                output = frame.copy()

            # Define active hold gestures for timing
            active_gestures = []
            if state.left_name == "closed_fist":
                active_gestures.append("left_fist")
            if state.left_name == "thumb_up":
                active_gestures.append("left_thumb_up")
            if state.left_name == "four_fingers_up":
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
                    canvas.stop_stroke()

                    # Point with LEFT Index
                    if state.left_cursor:
                        menu_cursor = state.left_cursor
                        menu_selection = menu_selection_for_cursor(menu_cursor, width)
                    else:
                        menu_cursor = None

                    # Select with LEFT Index + Middle
                    if state.left_name == "menu_select":
                        activate_mode(canvas, menu, menu_selection, game)
                        if menu_selection == "game":
                            game.sound.start_music()
                        else:
                            game.sound.stop_music()
                        app_state = "active"
                        menu.say(f"{menu_selection.upper()} mode")

                # ------------------- STATE: ACTIVE -------------------
                else:
                    # Return to Mode Menu with Right Index + Middle + Ring UP
                    if state.left_name == "menu_return":
                        game.sound.stop_music()
                        app_state = "menu"
                        # board.set_mode("draw")
                        canvas.stop_stroke()
                        menu.say("Mode menu")
                        menu_cursor = None
                    else:
                        # 1. Mode: Drawing Board
                        if menu.mode == "draw":
                            # Left Fist -> Undo (0.8s hold)
                            if (
                                "left_fist" in gesture_start_times
                                and not gesture_triggered.get("left_fist", True)
                            ):
                                if now - gesture_start_times["left_fist"] >= 0.8:
                                    canvas.undo()
                                    gesture_triggered["left_fist"] = True

                            # Left Thumb UP -> Redo (0.8s hold)
                            if (
                                "left_thumb_up" in gesture_start_times
                                and not gesture_triggered.get("left_thumb_up", True)
                            ):
                                if now - gesture_start_times["left_thumb_up"] >= 0.8:
                                    canvas.redo()
                                    gesture_triggered["left_thumb_up"] = True

                            # Both Open Palms -> Clear (2.0s hold)
                            if (
                                "both_open_palms" in gesture_start_times
                                and not gesture_triggered.get("both_open_palms", True)
                            ):
                                if now - gesture_start_times["both_open_palms"] >= 2.0:
                                    canvas.clear()
                                    gesture_triggered["both_open_palms"] = True

                            # Both Thumbs Up -> Save (1.0s hold)
                            if (
                                "both_thumbs_up" in gesture_start_times
                                and not gesture_triggered.get("both_thumbs_up", True)
                            ):
                                if now - gesture_start_times["both_thumbs_up"] >= 1.0:
                                    canvas.save()
                                    gesture_triggered["both_thumbs_up"] = True

                            # Right Pinky UP -> Toggle Eraser
                            if state.right_name == "pinky_up":
                                if not pinky_toggled:
                                    if canvas.tool == "eraser":
                                        canvas.tool = "pencil"
                                        menu.say("Drawing Mode")
                                    else:
                                        canvas.tool = "eraser"
                                        menu.say("Eraser Mode")
                                    pinky_toggled = True
                            else:
                                pinky_toggled = False

                            # Right Pinch -> Brush size control
                            if state.right_name == "pinch":
                                if not pinch_started:
                                    pinch_start_dist = state.right_pinch_distance
                                    pinch_start_brush = current_brush_size
                                    pinch_started = True
                                else:
                                    diff = state.right_pinch_distance - pinch_start_dist
                                    current_brush_size = max(
                                        canvas.min_brush,
                                        min(
                                            canvas.max_brush,
                                            int(pinch_start_brush + diff * 0.2),
                                        ),
                                    )
                            else:
                                pinch_started = False

                            # Right Color Menu Pop-up (Index + Middle + Pinky)
                            if state.right_name == "color_menu":
                                canvas.show_color_menu = True

                            # Draw palette whenever it is open
                            if canvas.show_color_menu:
                                hovered_color = canvas.draw_color_palette(
                                    output,
                                    state.right_cursor,
                                )

                                # Select using Index + Middle
                                if hovered_color and state.right_name == "select":
                                    canvas.color = canvas._color_actions()[hovered_color]
                                    canvas.effect = "normal"
                                    canvas.tool = "pencil"

                                    canvas.show_color_menu = False
                                    menu.say(f"{hovered_color.title()} selected")

                            # Handle Toolbar Button Clicks
                            action = canvas.handle_toolbar(
                                state.right_cursor, frame_number
                            )
                            if action:
                                if action == "game":
                                    game.reset()
                                canvas.stop_stroke()

                            # Draw or Erase
                            if not canvas.show_color_menu and not action:
                                draw_or_erase(canvas, state, current_brush_size)

                        # 2. Mode: Virtual Piano
                        elif menu.mode == "piano":
                            menu.set_mode("piano")
                            canvas.stop_stroke()
                            # Sustain pedal (Left Hand Open Palm)
                            sustain = state.left_name == "four_fingers_up"
                            piano.touch(state.right_cursor, sustain_active=sustain)

                            # ---------------- Volume ----------------

                            # Left Index -> Volume +
                            if state.left_name == "four_fingers_up":
                                if now - last_volume_change_time > 0.5:
                                    piano.set_volume(+0.1)
                                    menu.say(f"Volume {int(piano.volume*100)}%")
                                    last_volume_change_time = now

                            # Left Fist -> Volume -
                            elif state.left_name == "closed_fist":
                                if now - last_volume_change_time > 0.5:
                                    piano.set_volume(-0.1)
                                    menu.say(f"Volume {int(piano.volume*100)}%")
                                    last_volume_change_time = now

                            # ---------------- Octave ----------------

                            # Thumb Up
                            elif state.left_name == "menu_cursor":
                                if now - last_octave_change_time > 1:
                                    piano.change_octave(+1)
                                    menu.say(f"Octave {piano.octave_offset:+d}")
                                    last_octave_change_time = now

                            # Pinky Up
                            elif state.left_name == "pinky_up":
                                if now - last_octave_change_time > 1:
                                    piano.change_octave(-1)
                                    menu.say(f"Octave {piano.octave_offset:+d}")
                                    last_octave_change_time = now

                            # ---------------- Instrument ----------------

                            elif state.left_name == "rock":
                                if now - last_instrument_change_time > 1:
                                    piano.next_instrument()
                                    menu.say(piano.instruments[piano.instrument_index])
                                    last_instrument_change_time = now

                        # 3. Mode: Fruit Ninja
                        elif menu.mode == "game":
                            canvas.stop_stroke()
                            menu.set_mode("game")
                            # Restart Game (Both Thumbs Up held for 2.0s)
                            if (
                                "both_thumbs_up" in gesture_start_times
                                and not gesture_triggered.get("both_thumbs_up", True)
                            ):
                                if now - gesture_start_times["both_thumbs_up"] >= 2.0:
                                    game.reset()
                                    gesture_triggered["both_thumbs_up"] = True

                            # Update game mechanics
                            game.update(
                                width,
                                height,
                                cutter=(
                                    state.right_cursor
                                    if state.right_name == "draw"
                                    else None
                                ),
                                shield_pressed=(state.left_name == "closed_fist"),
                                slow_mo_pressed=(state.left_name == "four_fingers_up"),
                            )

                        # 4. Mode: Handwriting OCR
                        elif menu.mode == "ocr":
                            menu.set_mode("ocr")
                            # Draw strokes inside the OCR area
                            draw_or_erase(canvas, state, current_brush_size)

                            # Start Recognition (Left Open Palm held for 1.0s)
                            if (
                                "left_open_palm" in gesture_start_times
                                and not gesture_triggered.get("left_open_palm", True)
                            ):
                                if now - gesture_start_times["left_open_palm"] >= 1.0:
                                    results, msg = ocr.recognize(
                                        canvas.get_page_on_white()
                                    )
                                    menu.say(msg, frames=150)
                                    ocr_text_result = " ".join(r.text for r in results)
                                    gesture_triggered["left_open_palm"] = True

                            # Copy Result (Left Hand Thumb UP)
                            if state.left_name == "thumb_up":
                                if not ocr_copied:
                                    if ocr_text_result:
                                        success = ocr.copy_to_clipboard(ocr_text_result)
                                        if success:
                                            menu.say(
                                                "Copied text to clipboard!", frames=100
                                            )
                                        else:
                                            menu.say("Failed to copy text", frames=100)
                                    ocr_copied = True
                            else:
                                ocr_copied = False

                            # Read Aloud (Left Hand Rock Sign)
                            if state.left_name == "rock":
                                if not ocr_spoken:
                                    if ocr_text_result:
                                        ocr.speak_text(ocr_text_result)
                                        menu.say("Reading aloud...", frames=100)
                                    ocr_spoken = True
                            else:
                                ocr_spoken = False

                            # Clear OCR Area (Both Open Palms held for 2.0s)
                            if (
                                "both_open_palms" in gesture_start_times
                                and not gesture_triggered.get("both_open_palms", True)
                            ):
                                if now - gesture_start_times["both_open_palms"] >= 2.0:
                                    canvas.clear()
                                    ocr_text_result = ""
                                    menu.say("OCR Canvas Cleared")
                                    gesture_triggered["both_open_palms"] = True

                        # 5. Mode: Voice Command
                        elif menu.mode == "voice":
                            menu.set_mode("voice")
                            canvas.stop_stroke()
                            # Start Listening (Left Hand Open Palm)
                            if state.left_name == "four_fingers_up":
                                if not voice.is_currently_listening:
                                    voice.start_listening_background()
                                    menu.say("Listening...", frames=25)
                            # Stop Listening (Left Hand Closed Fist)
                            elif state.left_name == "closed_fist":
                                if voice.is_currently_listening:
                                    voice.stop_listening_background()
                                    menu.say("Listening stopped", frames=100)
                            # Repeat Last Command (Left Hand Thumb UP)
                            elif state.left_name == "thumb_up":
                                if not voice_command_repeated:
                                    if last_voice_command:
                                        menu.say(
                                            f"Repeating: {last_voice_command}", frames=100
                                        )
                                        action = canvas.apply_voice_command(
                                            last_voice_command
                                        )
                                        if action == "game":
                                            game.reset()
                                        voice.speak(menu.message)
                                    else:
                                        menu.say("No command to repeat", frames=100)
                                    voice_command_repeated = True
                            else:
                                voice_command_repeated = False

                            # Retrieve background commands
                            v_res = voice.get_result()
                            if v_res:
                                menu.say(v_res.message, frames=150)
                                if v_res.command:
                                    last_voice_command = v_res.command
                                    action = canvas.apply_voice_command(v_res.command)
                                    if action == "game":
                                        game.reset()
                                    voice.speak(menu.message)

            # Draw active mode HUD and overlays
            if app_state == "menu":
                menu.draw_mode_menu(output, menu_cursor, menu_selection)
            elif menu.mode == "piano":
                menu.set_mode("piano")
                piano.draw(output, state.right_cursor)
            elif menu.mode == "game":
                menu.set_mode("game")
                game.draw(output)
            elif menu.mode == "ocr":
                menu.set_mode("ocr")
                # Draw handwriting bounding zone
                cx, cy = width // 2, height // 2
                w = menu.scale(280)
                h = menu.scale(180)
                cv2.rectangle(
                    output,
                    (cx - w, cy - h),
                    (cx + w, cy + h),
                    (255, 165, 0),
                    2,
                    cv2.LINE_4,
                )
                cv2.putText(
                    output,
                    "OCR Zone - Write Here",
                    (
                        cx - menu.scale(270),
                        cy - menu.scale(195),
                    ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55 * menu.scale(1),
                    (255, 165, 0),
                    menu.scale(1),
                    cv2.LINE_AA,
                )
                # Show recognized text block
                if ocr_text_result:
                    panel_w = menu.scale(300)
                    panel_top = height - menu.scale(120)
                    panel_bottom = height - menu.scale(55)
                    cv2.rectangle(
                        output,
                        (cx - panel_w, panel_top),
                        (cx + panel_w, panel_bottom),
                        (35, 30, 25),
                        -1,
                    )
                    cv2.rectangle(
                        output,
                        (cx - panel_w, panel_top),
                        (cx + panel_w, panel_bottom),
                        (255, 165, 0),
                        1,
                    )
                    cv2.putText(
                        output,
                        f"Recognized: {ocr_text_result[:45]}...",
                        (cx - menu.scale(280), height - menu.scale(85)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55 * menu.scale(1),
                        (255, 255, 255),
                        menu.scale(1),
                        cv2.LINE_AA,
                    )
            elif menu.mode == "voice":
                menu.set_mode("voice")
                cx, cy = width // 2, height // 2
                # Pulsing mic icon
                if voice.is_currently_listening:
                    pulse = menu.scale(int(24 + 6 * math.sin(time.time() * 8)))
                    cv2.circle(
                        output,
                        (cx, cy - menu.scale(40)),
                        pulse,
                        (0, 0, 255),
                        -1,
                    )
                    cv2.circle(
                        output, (cx, cy - menu.scale(40)), pulse + 6, (0, 0, 150), 2
                    )
                    cv2.putText(
                        output,
                        "LISTENING...",
                        (
                            cx - menu.scale(55),
                            cy + menu.scale(30),
                        ),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.65 * (menu.scale(100) / 100),
                        (0, 0, 255),
                        menu.scale(2),
                        cv2.LINE_AA,
                    )
                else:
                    cv2.circle(
                        output,
                        (cx, cy - menu.scale(40)),
                        menu.scale(24),
                        (100, 100, 100),
                        -1,
                    )
                    cv2.putText(
                        output,
                        "Open Palm: Listen | Fist: Stop | Thumb UP: Repeat",
                        (cx - 200, cy + 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (200, 200, 200),
                        1,
                        cv2.LINE_AA,
                    )

                if last_voice_command:
                    cv2.putText(
                        output,
                        f"Last Command: {last_voice_command}",
                        (cx - 150, cy + 70),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (100, 255, 100),
                        1,
                        cv2.LINE_AA,
                    )

            # Draw progress rings for hold gestures
            if state.right_cursor:
                for g, threshold in [
                    ("left_fist", 0.8),
                    ("left_thumb_up", 0.8),
                    ("both_open_palms", 2.0),
                    ("both_thumbs_up", 1.0 if menu.mode == "draw" else 2.0),
                    ("left_open_palm", 1.0),
                ]:
                    if g in gesture_start_times and not gesture_triggered.get(g, True):
                        elapsed = now - gesture_start_times[g]
                        progress = min(1.0, elapsed / threshold)
                        angle = int(progress * 360)
                        cursor_pos = state.right_cursor
                        if g.startswith("left_") and state.left_cursor:
                            cursor_pos = state.left_cursor
                        cv2.ellipse(
                            output,
                            cursor_pos,
                            (30, 30),
                            0,
                            -90,
                            -90 + angle,
                            (0, 255, 255),
                            3,
                            cv2.LINE_AA,
                        )

            # Overlay System Idle screensaver
            if idle_active:
                overlay = output.copy()
                cv2.rectangle(overlay, (0, 0), (width, height), (12, 12, 18), -1)
                cv2.addWeighted(overlay, 0.82, output, 0.18, 0, output)
                cv2.putText(
                    output,
                    "SYSTEM IDLE",
                    (width // 2 - 100, height // 2 - 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.1,
                    (180, 180, 200),
                    3,
                    cv2.LINE_AA,
                )
                cv2.putText(
                    output,
                    "Show hand to wake up",
                    (width // 2 - 120, height // 2 + 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (140, 140, 150),
                    1,
                    cv2.LINE_AA,
                )

            # Calculate and draw FPS
            now_fps = time.time()
            elapsed = now_fps - fps_time
            if elapsed >= 0.5:
                fps = 1.0 / max(0.0001, elapsed / max(1, frame_number % 30 or 30))
                fps_time = now_fps

            if app_state == "menu":
                cv2.putText(
                    output,
                    "Index to point. Index + Middle selects.",
                    (menu.scale(60), menu.scale(950)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.56,
                    (245, 245, 245),
                    menu.scale(1),
                    cv2.LINE_AA,
                )

                cv2.putText(
                    output,
                    "Index + Middle + Ring returns here.",
                    (menu.scale(60), menu.scale(1050)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.56,
                    (245, 245, 245),
                    menu.scale(1),
                    cv2.LINE_AA,
                )
                cv2.putText(
                    output,
                    "use right hand gestures to control modes.",
                    (menu.scale(60), menu.scale(1150)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.56,
                    (245, 245, 245),
                    menu.scale(1),
                    cv2.LINE_AA,
                )
            else:
                if menu.mode == "draw":
                    canvas.draw_ui(
                        output, state.right_cursor, state.right_name, current_brush_size
                    )

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
                ocr, voice, app_state = handle_key(
                    key, canvas, ocr, voice, game, app_state
                )
    finally:
        tracker.close()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
