from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import cv2

try:
    import mediapipe as mp
    from mediapipe.framework.formats import landmark_pb2
except ImportError as exc:  # pragma: no cover - depends on local environment
    mp = None
    landmark_pb2 = None
    _MEDIAPIPE_IMPORT_ERROR = exc
else:
    _MEDIAPIPE_IMPORT_ERROR = None


Point3D = Tuple[int, int, float]


@dataclass
class HandResult:
    landmarks: List[Point3D]
    handedness: str
    bbox: Tuple[int, int, int, int]


class HandTracker:
    """Thin wrapper around MediaPipe Hands with pixel-space landmarks."""

    def __init__(
        self,
        max_hands: int = 2,
        detection_confidence: float = 0.7,
        tracking_confidence: float = 0.7,
    ) -> None:
        if mp is None:
            raise RuntimeError(
                "MediaPipe is not installed. Run: python -m pip install mediapipe"
            ) from _MEDIAPIPE_IMPORT_ERROR

        self._mp_hands = mp.solutions.hands
        self._mp_draw = mp.solutions.drawing_utils
        self._connections = self._mp_hands.HAND_CONNECTIONS
        self._hands = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            model_complexity=1,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )

    def process(self, frame_bgr) -> List[HandResult]:
        height, width = frame_bgr.shape[:2]
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        results = self._hands.process(frame_rgb)
        hands: List[HandResult] = []

        if not results.multi_hand_landmarks:
            return hands

        handedness_values = results.multi_handedness or []
        for index, hand_landmarks in enumerate(results.multi_hand_landmarks):
            landmarks: List[Point3D] = []
            xs: List[int] = []
            ys: List[int] = []

            for landmark in hand_landmarks.landmark:
                x = int(landmark.x * width)
                y = int(landmark.y * height)
                landmarks.append((x, y, landmark.z))
                xs.append(x)
                ys.append(y)

            label = "Unknown"
            if index < len(handedness_values):
                label = handedness_values[index].classification[0].label

            bbox = (min(xs), min(ys), max(xs), max(ys))
            hands.append(HandResult(landmarks=landmarks, handedness=label, bbox=bbox))

        return hands

    def draw_landmarks(self, frame_bgr, hand_results: Sequence[HandResult]) -> None:
        for hand in hand_results:
            # Rebuild a lightweight landmark list for MediaPipe drawing utilities.
            landmark_list = self._landmark_list_from_pixels(hand.landmarks, frame_bgr.shape)
            self._mp_draw.draw_landmarks(frame_bgr, landmark_list, self._connections)

    def close(self) -> None:
        self._hands.close()

    def _landmark_list_from_pixels(self, landmarks: Sequence[Point3D], frame_shape):
        height, width = frame_shape[:2]
        normalized = landmark_pb2.NormalizedLandmarkList()
        for x, y, z in landmarks:
            normalized.landmark.add(x=x / width, y=y / height, z=z)
        return normalized
