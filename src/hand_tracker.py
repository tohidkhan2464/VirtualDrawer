import cv2
import mediapipe as mp


class HandTracker:
    def __init__(
        self,
        static_mode=False,
        max_hands=2,
        detection_confidence=0.7,
        tracking_confidence=0.7,
    ):
        self.static_mode = static_mode
        self.max_hands = max_hands
        self.detection_confidence = detection_confidence
        self.tracking_confidence = tracking_confidence

        # MediaPipe Hands
        self.mp_hands = mp.solutions.hands

        self.hands = self.mp_hands.Hands(
            static_image_mode=self.static_mode,
            max_num_hands=self.max_hands,
            min_detection_confidence=self.detection_confidence,
            min_tracking_confidence=self.tracking_confidence,
        )

        self.mp_draw = mp.solutions.drawing_utils

        self.results = None
        self.landmark_list = []

    def find_hands(self, frame, draw=True):
        """
        Detect hands and optionally draw landmarks.
        """

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        self.results = self.hands.process(rgb_frame)

        if self.results.multi_hand_landmarks:

            for hand_landmarks in self.results.multi_hand_landmarks:

                if draw:
                    self.mp_draw.draw_landmarks(
                        frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS
                    )

        return frame, self.results

    def get_landmarks(self, frame, hand_no=0, draw_ids=True):
        """
        Returns all landmark coordinates of single hand.
        """

        self.landmark_list = []

        if self.results and self.results.multi_hand_landmarks:

            if hand_no < len(self.results.multi_hand_landmarks):

                hand = self.results.multi_hand_landmarks[hand_no]

                h, w, c = frame.shape

                for idx, landmark in enumerate(hand.landmark):

                    cx = int(landmark.x * w)
                    cy = int(landmark.y * h)

                    self.landmark_list.append([idx, cx, cy])

                    if draw_ids:
                        cv2.putText(
                            frame,
                            str(idx),
                            (cx + 5, cy - 5),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.4,
                            (0, 255, 0),
                            1,
                        )

        return self.landmark_list

    def get_all_landmarks(self, frame, draw_ids=True):
        """
        Returns landmarks for all detected hands.

        Returns:
        [
            {
                "hand_type": "Left",
                "landmarks": [[id, x, y], ...]
            },
            {
                "hand_type": "Right",
                "landmarks": [[id, x, y], ...]
            }
        ]
        """

        all_hands = []

        if self.results and self.results.multi_hand_landmarks:

            h, w, _ = frame.shape

            for hand_idx, hand_landmarks in enumerate(
                self.results.multi_hand_landmarks
            ):

                lm_list = []

                for idx, landmark in enumerate(hand_landmarks.landmark):

                    cx = int(landmark.x * w)
                    cy = int(landmark.y * h)

                    lm_list.append([idx, cx, cy])

                    if draw_ids:
                        cv2.putText(
                            frame,
                            str(idx),
                            (cx + 5, cy - 5),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.4,
                            (0, 255, 0),
                            1,
                        )

                # Get Left / Right hand label
                hand_type = (
                    self.results.multi_handedness[hand_idx].classification[0].label
                )

                all_hands.append(
                    {
                        "hand_type": hand_type,
                        "landmarks": lm_list,
                    }
                )

        return all_hands
