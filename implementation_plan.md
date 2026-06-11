# Implementation Plan - Day 3: Gesture Recognition

We will build a reusable, robust, and extensible gesture recognition system. It will detect 15 gestures, support left and right hands, and use normalized distance thresholds for pinch/zoom actions. It will also support a 2-second hold confirmation delay with visual feedback for clearing the canvas.

## Proposed Changes

We will modify/create the following files:

1. **`src/gesture_recognizer.py`** [MODIFY]: Add the `Gesture` enum, the finger state detector, and the full implementation of 15 gestures.
2. **`main.py`** [MODIFY]: Integrate the new `GestureRecognizer` and draw a premium visual feedback overlay (e.g., circular progress indicator for hold-to-clear, gesture names, etc.).

---

### Component: Gesture Recognition

#### [MODIFY] [gesture_recognizer.py](file:///d:/VirtualDrawer/src/gesture_recognizer.py)

We will rewrite `src/gesture_recognizer.py` to contain:
- The `Gesture` class representing all gesture names as constants.
- The `GestureRecognizer` class that:
  - Detects finger states (up/down) via `get_finger_states(landmarks, hand_type)`.
  - Normalizes distance calculations for pinch and zoom using the distance between wrist (0) and middle MCP (9) to handle hands at varying distances from the camera.
  - Recognizes all 15 gestures.
  - Tracks hold time for the `CLEAR_CANVAS` gesture and returns holding progress.

##### Gesture Enum Definition:
```python
class Gesture:
    NONE = "none"
    DRAW = "draw"
    SELECT = "select"
    ERASE = "erase"
    CLEAR_CANVAS = "clear_canvas"
    PAUSE = "pause"
    TEXT_MODE = "text_mode"
    UNDO = "undo"
    SAVE = "save"
    DELETE = "delete"
    COLOR_SELECTION = "color_selection"
    BRUSH_MENU = "brush_menu"
    PINCH = "pinch"
    ZOOM = "zoom"
    NEXT_TOOL = "next_tool"
    VOICE_COMMAND = "voice_command"
```

##### 15 Gestures Logic:

1. **DRAW**: Index UP, Middle DOWN, Ring DOWN, Pinky DOWN.
2. **SELECT**: Index UP, Middle UP, Ring DOWN, Pinky DOWN.
3. **ERASE**: Index UP, Pinky UP, Middle DOWN, Ring DOWN, Thumb DOWN.
4. **CLEAR_CANVAS**: All fingers UP (Thumb, Index, Middle, Ring, Pinky UP). Needs 2s hold.
5. **PAUSE**: All fingers DOWN.
6. **TEXT_MODE**: Index, Middle, Ring UP, Pinky and Thumb DOWN.
7. **UNDO**: Pinky UP, all others DOWN.
8. **SAVE**: Thumb UP (according to side extension check), others DOWN.
9. **DELETE** (Thumb Down): Thumb pointing down (`thumb_tip_y > thumb_joint_y` and thumb is extended), others DOWN.
10. **COLOR_SELECTION**: Same finger pattern as SELECT, but we can treat SELECT as the primary action and keep COLOR_SELECTION for alias/alternate state handling.
11. **BRUSH_MENU**: Index, Middle, Ring, Pinky UP, Thumb DOWN.
12. **PINCH**: Normalized distance between Thumb Tip (4) and Index Tip (8) is `< 0.15`.
13. **ZOOM**: Pinch active AND Middle UP.
14. **NEXT_TOOL**: Index UP, Pinky UP, others DOWN.
15. **VOICE_COMMAND**: Thumb UP, Pinky UP, others DOWN.

---

### Component: Main Application

#### [MODIFY] [main.py](file:///d:/VirtualDrawer/main.py)

We will update the main loop to:
- Instantiate and call the new `GestureRecognizer`.
- Draw a premium UI:
  - Display the recognized gesture for each hand.
  - Display the current finger states (e.g. `[T: UP, I: UP, M: DOWN, R: DOWN, P: DOWN]`).
  - Draw a beautiful circular progress bar around the index finger or center of the hand when holding the `CLEAR_CANVAS` gesture.
  - Apply clean BGR colors from `COLORS` matching the mode.

---

## Verification Plan

### Manual Verification
1. Run the camera feed using:
   ```bash
   python main.py
   ```
2. Test each gesture and confirm that it recognizes the correct mode.
3. Verify that Left and Right hands both detect thumb state correctly.
4. Verify that holding the open palm (all fingers up) for 2 seconds clears the canvas (simulated / printed) and shows a progress overlay.
