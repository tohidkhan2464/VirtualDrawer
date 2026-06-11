import math
import time

class Gesture:
    NONE = "none"
    # Single hand - Right (Dominant)
    DRAW = "draw"
    SELECT = "select"
    PAUSE = "pause"
    PINCH = "pinch"
    # Single hand - Left (Modifier)
    ERASE = "erase"
    TEXT_MODE = "text_mode"
    BRUSH_MENU = "brush_menu"
    COLOR_MENU = "color_menu"
    # Two-hand
    SAVE = "save"
    CLEAR_CANVAS = "clear_canvas"
    UNDO = "undo"
    REDO = "redo"
    VOICE_COMMAND = "voice_command"
    ZOOM = "zoom"
    NEXT_TOOL = "next_tool"
    # Hold states
    SAVE_HOLD = "save_hold"
    CLEAR_HOLD = "clear_hold"
    UNDO_HOLD = "undo_hold"


class GestureRecognizer:
    def __init__(self):
        # Stateful timers for hold gestures
        self.save_start_time = None
        self.save_duration = 1.0  # 1 second
        
        self.clear_canvas_start_time = None
        self.clear_canvas_duration = 2.0  # 2 seconds
        
        self.undo_start_time = None
        self.undo_duration = 0.5  # 500ms

    def get_finger_states(self, landmarks, hand_type):
        """
        Determines whether each finger is UP or DOWN.
        Returns:
        {
            "thumb": bool,
            "index": bool,
            "middle": bool,
            "ring": bool,
            "pinky": bool
        }
        """
        if not landmarks or len(landmarks) < 21:
            return {
                "thumb": False,
                "index": False,
                "middle": False,
                "ring": False,
                "pinky": False,
            }

        # Hand size for normalization
        hand_size = math.hypot(
            landmarks[0][1] - landmarks[9][1],
            landmarks[0][2] - landmarks[9][2]
        )
        if hand_size == 0:
            hand_size = 1.0

        # Standard check: tip_y < pip_y
        index_up = landmarks[8][2] < landmarks[6][2]
        middle_up = landmarks[12][2] < landmarks[10][2]
        ring_up = landmarks[16][2] < landmarks[14][2]
        pinky_up = landmarks[20][2] < landmarks[18][2]

        # Thumb check
        thumb_tip_x = landmarks[4][1]
        thumb_joint_x = landmarks[2][1]

        thumb_index_mcp_dist = math.hypot(
            landmarks[4][1] - landmarks[5][1],
            landmarks[4][2] - landmarks[5][2]
        ) / hand_size

        if thumb_index_mcp_dist < 0.35:
            thumb_up = False
        else:
            if hand_type == "Right":
                thumb_up = thumb_tip_x > thumb_joint_x
            else:
                # Left Hand
                thumb_up = thumb_tip_x < thumb_joint_x

        return {
            "thumb": thumb_up,
            "index": index_up,
            "middle": middle_up,
            "ring": ring_up,
            "pinky": pinky_up,
        }

    def _is_pinch(self, landmarks, hand_size):
        if not landmarks or len(landmarks) < 21:
            return False
        dist = math.hypot(
            landmarks[4][1] - landmarks[8][1],
            landmarks[4][2] - landmarks[8][2]
        ) / hand_size
        return dist < 0.15

    def recognize_hands(self, all_hands):
        """
        Processes detected hands list and recognizes two-hand and single-hand gestures.
        Returns:
            {
                "global_gesture": str (e.g. Gesture.SAVE, Gesture.SAVE_HOLD, etc.),
                "global_progress": float (0.0 to 1.0),
                "left_gesture": str,
                "right_gesture": str,
                "left_fingers": dict,
                "right_fingers": dict
            }
        """
        # Find Left and Right hand data
        left_hand = None
        right_hand = None
        for hand in all_hands:
            if hand["hand_type"] == "Left":
                left_hand = hand
            elif hand["hand_type"] == "Right":
                right_hand = hand

        left_lms = left_hand["landmarks"] if left_hand else None
        right_lms = right_hand["landmarks"] if right_hand else None

        # Get finger states
        left_fingers = self.get_finger_states(left_lms, "Left") if left_hand else None
        right_fingers = self.get_finger_states(right_lms, "Right") if right_hand else None

        # Normalization hand size
        left_size = 1.0
        if left_lms:
            left_size = math.hypot(left_lms[0][1] - left_lms[9][1], left_lms[0][2] - left_lms[9][2])
            if left_size == 0: left_size = 1.0

        right_size = 1.0
        if right_lms:
            right_size = math.hypot(right_lms[0][1] - right_lms[9][1], right_lms[0][2] - right_lms[9][2])
            if right_size == 0: right_size = 1.0

        # Check pinch status
        left_pinch = self._is_pinch(left_lms, left_size) if left_hand else False
        right_pinch = self._is_pinch(right_lms, right_size) if right_hand else False

        # --- TWO-HAND GESTURE RECOGNITION ---
        if left_hand and right_hand:
            # 1. SAVE: Right Thumb UP AND Left Thumb UP
            # Right hand: thumb=True, others=False
            # Left hand: thumb=True, others=False
            rt_only = right_fingers["thumb"] and not (right_fingers["index"] or right_fingers["middle"] or right_fingers["ring"] or right_fingers["pinky"])
            lt_only = left_fingers["thumb"] and not (left_fingers["index"] or left_fingers["middle"] or left_fingers["ring"] or left_fingers["pinky"])
            if rt_only and lt_only:
                self._reset_except("save")
                current_time = time.time()
                if self.save_start_time is None:
                    self.save_start_time = current_time
                elapsed = current_time - self.save_start_time
                progress = min(1.0, elapsed / self.save_duration)
                if elapsed >= self.save_duration:
                    return {
                        "global_gesture": Gesture.SAVE, "global_progress": 1.0,
                        "left_gesture": Gesture.SAVE, "right_gesture": Gesture.SAVE,
                        "left_fingers": left_fingers, "right_fingers": right_fingers
                    }
                else:
                    return {
                        "global_gesture": Gesture.SAVE_HOLD, "global_progress": progress,
                        "left_gesture": Gesture.SAVE_HOLD, "right_gesture": Gesture.SAVE_HOLD,
                        "left_fingers": left_fingers, "right_fingers": right_fingers
                    }

            # 2. CLEAR CANVAS: Right Palm AND Left Palm (all fingers UP)
            r_palm = right_fingers["thumb"] and right_fingers["index"] and right_fingers["middle"] and right_fingers["ring"] and right_fingers["pinky"]
            l_palm = left_fingers["thumb"] and left_fingers["index"] and left_fingers["middle"] and left_fingers["ring"] and left_fingers["pinky"]
            if r_palm and l_palm:
                self._reset_except("clear")
                current_time = time.time()
                if self.clear_canvas_start_time is None:
                    self.clear_canvas_start_time = current_time
                elapsed = current_time - self.clear_canvas_start_time
                progress = min(1.0, elapsed / self.clear_canvas_duration)
                if elapsed >= self.clear_canvas_duration:
                    return {
                        "global_gesture": Gesture.CLEAR_CANVAS, "global_progress": 1.0,
                        "left_gesture": Gesture.CLEAR_CANVAS, "right_gesture": Gesture.CLEAR_CANVAS,
                        "left_fingers": left_fingers, "right_fingers": right_fingers
                    }
                else:
                    return {
                        "global_gesture": Gesture.CLEAR_HOLD, "global_progress": progress,
                        "left_gesture": Gesture.CLEAR_HOLD, "right_gesture": Gesture.CLEAR_HOLD,
                        "left_fingers": left_fingers, "right_fingers": right_fingers
                    }

            # 3. UNDO: Right Index UP AND Left Index UP (hold 500ms)
            ri_only = right_fingers["index"] and not (right_fingers["thumb"] or right_fingers["middle"] or right_fingers["ring"] or right_fingers["pinky"])
            li_only = left_fingers["index"] and not (left_fingers["thumb"] or left_fingers["middle"] or left_fingers["ring"] or left_fingers["pinky"])
            if ri_only and li_only:
                self._reset_except("undo")
                current_time = time.time()
                if self.undo_start_time is None:
                    self.undo_start_time = current_time
                elapsed = current_time - self.undo_start_time
                progress = min(1.0, elapsed / self.undo_duration)
                if elapsed >= self.undo_duration:
                    return {
                        "global_gesture": Gesture.UNDO, "global_progress": 1.0,
                        "left_gesture": Gesture.UNDO, "right_gesture": Gesture.UNDO,
                        "left_fingers": left_fingers, "right_fingers": right_fingers
                    }
                else:
                    return {
                        "global_gesture": Gesture.UNDO_HOLD, "global_progress": progress,
                        "left_gesture": Gesture.UNDO_HOLD, "right_gesture": Gesture.UNDO_HOLD,
                        "left_fingers": left_fingers, "right_fingers": right_fingers
                    }

            # Reset hold timers if no two-hand hold gesture matches
            self._reset_except(None)

            # 4. REDO: Right Index + Middle UP AND Left Index + Middle UP (✌️ + ✌️)
            r_select = right_fingers["index"] and right_fingers["middle"] and not (right_fingers["thumb"] or right_fingers["ring"] or right_fingers["pinky"])
            l_select = left_fingers["index"] and left_fingers["middle"] and not (left_fingers["thumb"] or left_fingers["ring"] or left_fingers["pinky"])
            if r_select and l_select:
                return {
                    "global_gesture": Gesture.REDO, "global_progress": 0.0,
                    "left_gesture": Gesture.REDO, "right_gesture": Gesture.REDO,
                    "left_fingers": left_fingers, "right_fingers": right_fingers
                }

            # 5. VOICE COMMAND: Right 🤙 AND Left 🤙 (Thumb + Pinky UP)
            r_shaka = right_fingers["thumb"] and right_fingers["pinky"] and not (right_fingers["index"] or right_fingers["middle"] or right_fingers["ring"])
            l_shaka = left_fingers["thumb"] and left_fingers["pinky"] and not (left_fingers["index"] or left_fingers["middle"] or left_fingers["ring"])
            if r_shaka and l_shaka:
                return {
                    "global_gesture": Gesture.VOICE_COMMAND, "global_progress": 0.0,
                    "left_gesture": Gesture.VOICE_COMMAND, "right_gesture": Gesture.VOICE_COMMAND,
                    "left_fingers": left_fingers, "right_fingers": right_fingers
                }

            # 6. ZOOM MODE: Right Pinch AND Left Pinch
            if right_pinch and left_pinch:
                return {
                    "global_gesture": Gesture.ZOOM, "global_progress": 0.0,
                    "left_gesture": Gesture.ZOOM, "right_gesture": Gesture.ZOOM,
                    "left_fingers": left_fingers, "right_fingers": right_fingers
                }

            # 7. NEXT TOOL: Right Three fingers AND Left Three fingers (Index + Middle + Ring UP)
            r_three = right_fingers["index"] and right_fingers["middle"] and right_fingers["ring"] and not (right_fingers["pinky"] or right_fingers["thumb"])
            l_three = left_fingers["index"] and left_fingers["middle"] and left_fingers["ring"] and not (left_fingers["pinky"] or left_fingers["thumb"])
            if r_three and l_three:
                return {
                    "global_gesture": Gesture.NEXT_TOOL, "global_progress": 0.0,
                    "left_gesture": Gesture.NEXT_TOOL, "right_gesture": Gesture.NEXT_TOOL,
                    "left_fingers": left_fingers, "right_fingers": right_fingers
                }

        # Reset hold timers if no two-hand gesture was detected
        self._reset_except(None)

        # --- SINGLE-HAND GESTURE RECOGNITION ---
        left_g = Gesture.NONE
        right_g = Gesture.NONE

        # Evaluate Right Hand (Dominant)
        if right_hand and right_fingers:
            if right_pinch:
                right_g = Gesture.PINCH
            elif right_fingers["thumb"] and right_fingers["index"] and right_fingers["middle"] and right_fingers["ring"] and right_fingers["pinky"]:
                right_g = Gesture.PAUSE
            elif right_fingers["index"] and right_fingers["middle"] and not (right_fingers["ring"] or right_fingers["pinky"] or right_fingers["thumb"]):
                right_g = Gesture.SELECT
            elif right_fingers["index"] and not (right_fingers["middle"] or right_fingers["ring"] or right_fingers["pinky"] or right_fingers["thumb"]):
                right_g = Gesture.DRAW

        # Evaluate Left Hand (Modifier)
        if left_hand and left_fingers:
            # color menu: pinky only
            lp_only = left_fingers["pinky"] and not (left_fingers["thumb"] or left_fingers["index"] or left_fingers["middle"] or left_fingers["ring"])
            # brush menu: thumb only
            lt_only = left_fingers["thumb"] and not (left_fingers["index"] or left_fingers["middle"] or left_fingers["ring"] or left_fingers["pinky"])
            # eraser: index, middle, ring UP
            l_erase = left_fingers["index"] and left_fingers["middle"] and left_fingers["ring"] and not left_fingers["pinky"]
            # text mode: index, middle UP
            l_text = left_fingers["index"] and left_fingers["middle"] and not (left_fingers["ring"] or left_fingers["pinky"] or left_fingers["thumb"])

            if lp_only:
                left_g = Gesture.COLOR_MENU
            elif lt_only:
                left_g = Gesture.BRUSH_MENU
            elif l_erase:
                left_g = Gesture.ERASE
            elif l_text:
                left_g = Gesture.TEXT_MODE

        return {
            "global_gesture": Gesture.NONE,
            "global_progress": 0.0,
            "left_gesture": left_g,
            "right_gesture": right_g,
            "left_fingers": left_fingers,
            "right_fingers": right_fingers
        }

    def _reset_except(self, keep):
        if keep != "save":
            self.save_start_time = None
        if keep != "clear":
            self.clear_canvas_start_time = None
        if keep != "undo":
            self.undo_start_time = None

    def recognize_gesture(self, lm_list, hand_type):
        """
        Backward compatibility method.
        """
        # Pack single hand into recognized format
        hand_data = [{
            "hand_type": hand_type,
            "landmarks": lm_list
        }]
        res = self.recognize_hands(hand_data)
        
        gesture = res["left_gesture"] if hand_type == "Left" else res["right_gesture"]
        
        # Mapping to old uppercase names
        if gesture == Gesture.DRAW:
            return "DRAW"
        elif gesture == Gesture.SELECT:
            return "SELECT"
        elif gesture == Gesture.ERASE:
            return "ERASE"
        elif gesture == Gesture.PAUSE:
            return "PAUSE"
        
        return gesture.upper()