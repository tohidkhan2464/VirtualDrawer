import cv2
import time
import math

from src.hand_tracker import HandTracker
from src.utils import FPSCounter
from src.gesture_recognizer import GestureRecognizer, Gesture
from src.colors import COLORS


def main():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print("Could not open webcam.")
        return

    # Hand Tracker
    tracker = HandTracker()
    gesture_detector = GestureRecognizer()

    # FPS Counter
    fps_counter = FPSCounter()

    while True:
        success, frame = cap.read()
        if not success:
            print("Failed to read frame.")
            break

        # Mirror view
        frame = cv2.flip(frame, 1)

        # Detect hands
        frame, results = tracker.find_hands(frame, draw=True)

        global_g = Gesture.NONE
        global_progress = 0.0

        if results.multi_hand_landmarks:
            all_hands = tracker.get_all_landmarks(frame, draw_ids=False)
            
            # Recognize gestures using Gesture Set v2 (Two-Hand & Single-Hand)
            res = gesture_detector.recognize_hands(all_hands)
            global_g = res["global_gesture"]
            global_progress = res["global_progress"]

            for hand in all_hands:
                hand_type = hand["hand_type"]
                lm_list = hand["landmarks"]
                if not lm_list or len(lm_list) < 21:
                    continue

                # Get index tip position for cursor reference
                index_x, index_y = lm_list[8][1], lm_list[8][2]

                # Fetch gestures and finger states from recognized output
                gesture = res["left_gesture"] if hand_type == "Left" else res["right_gesture"]
                fingers = res["left_fingers"] if hand_type == "Left" else res["right_fingers"]

                # If there's an overriding two-hand gesture, display it as primary
                display_gesture = global_g if global_g != Gesture.NONE else gesture

                # Set color based on active gesture
                color = COLORS["YELLOW"]  # default
                if display_gesture == Gesture.DRAW:
                    color = COLORS["GREEN"]
                elif display_gesture == Gesture.SELECT:
                    color = COLORS["BLUE"]
                elif display_gesture == Gesture.PAUSE:
                    color = COLORS["GRAY"]
                elif display_gesture == Gesture.PINCH:
                    color = COLORS["ORANGE"]
                elif display_gesture == Gesture.ERASE:
                    color = COLORS["RED"]
                elif display_gesture == Gesture.TEXT_MODE:
                    color = COLORS["MAGENTA"]
                elif display_gesture == Gesture.BRUSH_MENU:
                    color = COLORS["PURPLE"]
                elif display_gesture == Gesture.COLOR_MENU:
                    color = COLORS["PINK"]
                elif display_gesture in [Gesture.SAVE, Gesture.SAVE_HOLD]:
                    color = COLORS["GOLD"]
                elif display_gesture in [Gesture.CLEAR_CANVAS, Gesture.CLEAR_HOLD]:
                    color = COLORS["CYAN"]
                elif display_gesture in [Gesture.UNDO, Gesture.UNDO_HOLD]:
                    color = COLORS["LIGHT_BLUE"]
                elif display_gesture == Gesture.REDO:
                    color = COLORS["LIGHT_GREEN"]
                elif display_gesture == Gesture.VOICE_COMMAND:
                    color = COLORS["INDIGO"]
                elif display_gesture == Gesture.ZOOM:
                    color = COLORS["DARK_GREEN"]
                elif display_gesture == Gesture.NEXT_TOOL:
                    color = COLORS["VIOLET"]

                # 1. Draw pointer circle and ring around index finger tip
                cv2.circle(frame, (index_x, index_y), 12, color, cv2.FILLED, cv2.LINE_AA)
                cv2.circle(frame, (index_x, index_y), 18, color, 2, cv2.LINE_AA)

                # 2. Draw Hand Center HUD for hold progress (Global two-hand hold gestures)
                hand_center = (lm_list[9][1], lm_list[9][2])
                if global_g in [Gesture.SAVE_HOLD, Gesture.CLEAR_HOLD, Gesture.UNDO_HOLD] and global_progress > 0:
                    radius = 45
                    cv2.circle(frame, hand_center, radius, COLORS["GRAY"], 2, cv2.LINE_AA)
                    cv2.ellipse(
                        frame,
                        hand_center,
                        (radius, radius),
                        -90,
                        0,
                        int(360 * global_progress),
                        color,
                        5,
                        cv2.LINE_AA
                    )
                    # Label above the progress circle
                    action_name = "SAVING" if global_g == Gesture.SAVE_HOLD else ("CLEARING" if global_g == Gesture.CLEAR_HOLD else "UNDOING")
                    cv2.putText(
                        frame,
                        f"{action_name} {int(global_progress * 100)}%",
                        (hand_center[0] - 65, hand_center[1] - 60),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.45,
                        color,
                        2,
                        cv2.LINE_AA
                    )
                elif global_g in [Gesture.SAVE, Gesture.CLEAR_CANVAS, Gesture.UNDO]:
                    action_done = "SAVED!" if global_g == Gesture.SAVE else ("CLEARED!" if global_g == Gesture.CLEAR_CANVAS else "UNDONE!")
                    cv2.putText(
                        frame,
                        action_done,
                        (hand_center[0] - 50, hand_center[1] - 60),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        COLORS["GREEN"],
                        2,
                        cv2.LINE_AA
                    )

                # 3. Draw Gesture Text Label Badge
                badge_y = hand_center[1] + 50
                badge_x = hand_center[0]
                gesture_display_name = display_gesture.upper().replace("_", " ")
                text = f"{hand_type}: {gesture_display_name}"
                
                (w_text, h_text), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 2)
                cv2.rectangle(
                    frame,
                    (badge_x - w_text // 2 - 10, badge_y - h_text - 5),
                    (badge_x + w_text // 2 + 10, badge_y + baseline + 5),
                    COLORS["BLACK"],
                    cv2.FILLED
                )
                cv2.rectangle(
                    frame,
                    (badge_x - w_text // 2 - 10, badge_y - h_text - 5),
                    (badge_x + w_text // 2 + 10, badge_y + baseline + 5),
                    color,
                    2
                )
                cv2.putText(
                    frame,
                    text,
                    (badge_x - w_text // 2, badge_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.45,
                    color,
                    2,
                    cv2.LINE_AA
                )

                # 4. Draw Finger States Panel below the badge
                if fingers:
                    finger_names = ["thumb", "index", "middle", "ring", "pinky"]
                    circle_radius = 5
                    spacing = 15
                    start_x = badge_x - (spacing * 2)
                    circle_y = badge_y + 22

                    cv2.rectangle(
                        frame,
                        (start_x - 12, circle_y - 8),
                        (start_x + (spacing * 4) + 12, circle_y + 8),
                        COLORS["BLACK"],
                        cv2.FILLED
                    )
                    cv2.rectangle(
                        frame,
                        (start_x - 12, circle_y - 8),
                        (start_x + (spacing * 4) + 12, circle_y + 8),
                        COLORS["DARK_GRAY"],
                        1
                    )

                    for idx, fname in enumerate(finger_names):
                        fx = start_x + idx * spacing
                        is_up = fingers.get(fname, False)
                        if is_up:
                            cv2.circle(frame, (fx, circle_y), circle_radius, color, cv2.FILLED, cv2.LINE_AA)
                        else:
                            cv2.circle(frame, (fx, circle_y), circle_radius, COLORS["GRAY"], 1, cv2.LINE_AA)

        # FPS calculation
        fps = fps_counter.get_fps()

        # Render translucent top HUD bar
        hud_overlay = frame.copy()
        cv2.rectangle(hud_overlay, (0, 0), (640, 50), COLORS["BLACK"], cv2.FILLED)
        cv2.addWeighted(hud_overlay, 0.7, frame, 0.3, 0, frame)

        # Draw HUD Title
        cv2.putText(
            frame,
            "VIRTUAL GESTURE STUDIO",
            (20, 32),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            COLORS["GOLD"],
            2,
            cv2.LINE_AA
        )

        # Draw active two-hand gesture in the HUD center
        if results.multi_hand_landmarks and global_g != Gesture.NONE:
            global_display = global_g.upper().replace("_", " ")
            hud_text = f"COMBO: {global_display}"
            (w_t, _), _ = cv2.getTextSize(hud_text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
            cv2.putText(
                frame,
                hud_text,
                (320 - w_t // 2, 32),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                COLORS["CYAN"],
                2,
                cv2.LINE_AA
            )

        # Draw FPS and Exit controls
        cv2.putText(
            frame,
            f"FPS: {fps}",
            (430, 32),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            COLORS["GREEN"],
            2,
            cv2.LINE_AA
        )

        cv2.text_exit = "ESC: Exit"
        cv2.putText(
            frame,
            "ESC: Exit",
            (540, 32),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            COLORS["RED"],
            2,
            cv2.LINE_AA
        )

        cv2.imshow("Virtual Gesture Studio", frame)

        key = cv2.waitKey(1)
        if key == 27:  # ESC
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
