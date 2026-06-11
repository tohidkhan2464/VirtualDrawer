from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from typing import Dict, Optional, Tuple

from src.hand_tracker import HandResult


@dataclass
class GestureState:
    name: str
    cursor: Optional[Tuple[int, int]]
    fingers: Dict[str, bool]
    pinch_distance: float
    brush_size: int
    shape: Optional[str] = None


class GestureDetector:
    """Converts 21 MediaPipe landmarks into simple classroom-demo gestures."""

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

    def detect(self, hand: Optional[HandResult]) -> GestureState:
        if hand is None:
            return GestureState(
                name="none",
                cursor=None,
                fingers={name: False for name in self.FINGER_NAMES},
                pinch_distance=0.0,
                brush_size=self.min_brush,
            )

        lm = hand.landmarks
        fingers = self._finger_states(hand)
        index_tip = (lm[8][0], lm[8][1])
        thumb_tip = (lm[4][0], lm[4][1])
        pinch_distance = hypot(index_tip[0] - thumb_tip[0], index_tip[1] - thumb_tip[1])
        brush_size = self._pinch_to_brush_size(pinch_distance)

        up_count = sum(fingers.values())
        name = "none"
        shape = self._shape_hint(fingers, pinch_distance)

        if up_count == 5:
            name = "clear"
        elif up_count == 0:
            name = "pause"
        elif (
            fingers["thumb"]
            and fingers["index"]
            and not any(fingers[finger] for finger in ("middle", "ring", "pinky"))
        ):
            name = "brush_resize"
        elif fingers["index"] and not any(
            fingers[finger] for finger in ("middle", "ring", "pinky")
        ):
            name = "draw"
        elif (
            fingers["index"]
            and fingers["middle"]
            and not fingers["ring"]
            and not fingers["pinky"]
        ):
            name = "move"
        else:
            name = "move"
        print(
            f"Pinch: {pinch_distance:.1f}, " f"Brush: {brush_size}, " f"Gesture: {name}"
        )

        return GestureState(
            name=name,
            cursor=index_tip,
            fingers=fingers,
            pinch_distance=pinch_distance,
            brush_size=brush_size,
            shape=shape,
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

    def _shape_hint(
        self, fingers: Dict[str, bool], pinch_distance: float
    ) -> Optional[str]:
        if (
            pinch_distance < 45
            and fingers["middle"]
            and fingers["ring"]
            and fingers["pinky"]
        ):
            return "triangle"
        if (
            fingers["index"]
            and fingers["middle"]
            and fingers["ring"]
            and not fingers["pinky"]
        ):
            return "rectangle"
        if (
            fingers["thumb"]
            and fingers["index"]
            and fingers["middle"]
            and not fingers["ring"]
        ):
            return "circle"
        return None
