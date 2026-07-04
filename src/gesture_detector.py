from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from typing import Dict, List, Optional, Tuple

from src.hand_tracker import HandResult


@dataclass
class GestureState:
    # Right hand (Action)
    fingers: Dict[str, bool]
    pinch_distance: float
    brush_size: int

    # Left hand
    left_name: str
    # "none", "menu_cursor", "menu_select", "menu_return",
    # "open_hand", "four_fingers_up", "closed_fist",
    # "thumb_up", "pinky_up", "rock", "color_menu", "pinch"    
    left_cursor: Optional[Tuple[int, int]]
    left_fingers: Dict[str, bool]
    left_pinch_distance: float
    left_pinch_brush_size: int

    # Right hand
    right_name: str
    # "none", "draw", "select", "return",
    # "open_hand", "four_fingers_up", "closed_fist",
    # "pinky_up", "color_menu", "pinch", "move"
    right_cursor: Optional[Tuple[int, int]]
    right_fingers: Dict[str, bool]
    right_pinch_distance: float
    right_brush_size: int

    # Two-handed gesture
    two_handed_name: str  # "none", "both_open_palms", "both_thumbs_up"
    shape: Optional[str] = None


class GestureDetector:
    """Classifies gestures for both Right (Action) and Left (Modifier) hands."""

    FINGER_NAMES = ("thumb", "index", "middle", "ring", "pinky")
    TIP_IDS = {"thumb": 4, "index": 8, "middle": 12, "ring": 16, "pinky": 20}
    PIP_IDS = {"index": 6, "middle": 10, "ring": 14, "pinky": 18}

    def __init__(
        self,
        min_brush: int = 3,
        max_brush: int = 36,
    ) -> None:
        self.min_brush = min_brush
        self.max_brush = max_brush

    def detect(self, hands: List[HandResult]) -> GestureState:
        # 1. Identify Left and Right hands from the list
        right_hand: Optional[HandResult] = None
        left_hand: Optional[HandResult] = None

        for hand in hands:
            if hand.handedness == "Right":
                right_hand = hand
            elif hand.handedness == "Left":
                left_hand = hand

        # 2. Process Right Hand (Action)
        right_name = "none"
        right_cursor = None
        right_fingers = {name: False for name in self.FINGER_NAMES}
        right_pinch = 0.0
        right_brush = self.min_brush

        if right_hand:
            lm = right_hand.landmarks
            right_fingers = self._finger_states(right_hand)
            right_cursor = (lm[8][0], lm[8][1])
            thumb_tip = (lm[4][0], lm[4][1])
            right_pinch = hypot(
                right_cursor[0] - thumb_tip[0], right_cursor[1] - thumb_tip[1]
            )
            right_brush = self._pinch_to_brush_size(right_pinch)

            # Determine Right hand gesture
            if right_fingers["index"] and not any(
                right_fingers[f] for f in ("middle", "ring", "pinky")
            ):
                right_name = "draw"
            elif (
                right_fingers["index"]
                and right_fingers["middle"]
                and not any(right_fingers[f] for f in ("ring", "pinky"))
            ):
                right_name = "select"
            elif (
                right_fingers["index"]
                and right_fingers["middle"]
                and right_fingers["ring"]
                and not right_fingers["pinky"]
            ):
                right_name = "color_menu"
            elif right_pinch < 40:
                right_name = "pinch"
            elif (
                right_fingers["pinky"]
                and not right_fingers["index"]
                and not right_fingers["middle"]
                and not right_fingers["ring"]
            ):
                right_name = "pinky_up"

            elif (
                right_fingers["index"]
                and right_fingers["pinky"]
                and not right_fingers["middle"]
                and not right_fingers["ring"]
                and not right_fingers["thumb"]
            ):
                right_name = "rock"
                
            # All five fingers
            elif all(right_fingers.values()):
                right_name = "open_hand"

            # Four fingers (thumb folded)
            elif (
                right_fingers["index"]
                and right_fingers["middle"]
                and right_fingers["ring"]
                and right_fingers["pinky"]
                and not right_fingers["thumb"]
            ):
                right_name = "four_fingers_up"

            # Closed fist
            elif not any(right_fingers.values()):
                right_name = "closed_fist"
            else:
                right_name = "move"

        # 3. Process Left Hand (Modifier)
        left_name = "none"
        left_cursor = None
        left_fingers = {name: False for name in self.FINGER_NAMES}
        left_pinch = 0.0
        left_brush = self.min_brush

        if left_hand:
            lm = left_hand.landmarks
            left_fingers = self._finger_states(left_hand)
            left_cursor = (lm[8][0], lm[8][1])
            thumb_tip = (lm[4][0], lm[4][1])
            left_pinch = hypot(
                left_cursor[0] - thumb_tip[0], left_cursor[1] - thumb_tip[1]
            )
            left_brush = self._pinch_to_brush_size(left_pinch)

            # Determine Left hand gesture
            # Left Index only -> move cursor
            if (
                left_fingers["index"]
                and not left_fingers["middle"]
                and not left_fingers["ring"]
                and not left_fingers["pinky"]
            ):
                left_name = "menu_cursor"

            # Left Index + Middle -> select
            elif (
                left_fingers["index"]
                and left_fingers["middle"]
                and not left_fingers["ring"]
                and not left_fingers["pinky"]
            ):
                left_name = "menu_select"

            # Left Index + Middle + Ring -> return/open menu
            elif (
                left_fingers["index"]
                and left_fingers["middle"]
                and left_fingers["ring"]
                and not left_fingers["pinky"]
            ):
                left_name = "menu_return"

            elif (
                left_fingers["index"]
                and left_fingers["middle"]
                and left_fingers["ring"]
                and left_fingers["pinky"]
                and not left_fingers["thumb"]
            ):
                left_name = "four_fingers_up"
            elif all(left_fingers.values()):
                left_name = "open_hand"

            elif not any(left_fingers.values()):
                left_name = "closed_fist"
            elif left_fingers["thumb"] and not any(
                left_fingers[f] for f in ("index", "middle", "ring", "pinky")
            ):
                left_name = "thumb_up"
            elif left_fingers["pinky"] and not any(
                left_fingers[f] for f in ("thumb", "index", "middle", "ring")
            ):
                left_name = "pinky_up"
            elif (
                left_fingers["index"]
                and left_fingers["pinky"]
                and not left_fingers["middle"]
                and not left_fingers["ring"]
            ):
                left_name = "rock"
            elif (
                left_fingers["index"]
                and left_fingers["middle"]
                and left_fingers["pinky"]
                and not left_fingers["ring"]
            ):
                left_name = "color_menu"
            elif left_pinch < 40:
                left_name = "pinch"

        # 4. Determine Two-Handed Gestures
        two_handed_name = "none"
        if right_hand and left_hand:
            if right_name == "draw" and left_name == "four_fingers_up":
                # Let open palm on left hand modify right index draw
                pass

            # Both Hands Open Palm -> Clear
            if all(
                right_fingers[f] for f in ("index", "middle", "ring", "pinky")
            ) and all(left_fingers[f] for f in ("index", "middle", "ring", "pinky")):
                two_handed_name = "both_open_palms"
            # Both Thumbs Up -> Save / Restart
            elif (
                right_fingers["thumb"]
                and not any(
                    right_fingers[f] for f in ("index", "middle", "ring", "pinky")
                )
                and left_fingers["thumb"]
                and not any(left_fingers[f] for f in ("index", "middle", "ring", "pinky"))
            ):
                two_handed_name = "both_thumbs_up"

        return GestureState(
            fingers=right_fingers,
            pinch_distance=right_pinch,
            brush_size=right_brush,
            right_name=right_name,
            right_cursor=right_cursor,
            right_fingers=right_fingers,
            right_pinch_distance=right_pinch,
            right_brush_size=right_brush,
            left_name=left_name,
            left_cursor=left_cursor,
            left_fingers=left_fingers,
            left_pinch_distance=left_pinch,
            left_pinch_brush_size=left_brush,
            two_handed_name=two_handed_name,
        )

    def _finger_states(self, hand: HandResult) -> Dict[str, bool]:
        lm = hand.landmarks
        fingers = {
            "index": lm[self.TIP_IDS["index"]][1] < lm[self.PIP_IDS["index"]][1],
            "middle": lm[self.TIP_IDS["middle"]][1] < lm[self.PIP_IDS["middle"]][1],
            "ring": lm[self.TIP_IDS["ring"]][1] < lm[self.PIP_IDS["ring"]][1],
            "pinky": lm[self.TIP_IDS["pinky"]][1] < lm[self.PIP_IDS["pinky"]][1],
        }

        thumb_tip_x = lm[4][0]
        thumb_ip_x = lm[3][0]
        if hand.handedness == "Right":
            fingers["thumb"] = thumb_tip_x > thumb_ip_x
        elif hand.handedness == "Left":
            fingers["thumb"] = thumb_tip_x < thumb_ip_x
        else:
            fingers["thumb"] = abs(thumb_tip_x - thumb_ip_x) > 24

        return fingers

    def _pinch_to_brush_size(self, distance: float) -> int:
        low = 20.0
        high = 150.0
        normalized = max(0.0, min(1.0, (distance - low) / (high - low)))
        return int(self.min_brush + normalized * (self.max_brush - self.min_brush))
