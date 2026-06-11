# Implementation Plan - Day 3: Gesture Recognition v2

We will update our gesture recognition system to support **Gesture Set v2**, which introduces asymmetric left/right hand roles (Right hand controls primary actions like Drawing, Selecting, and Pausing, while Left hand acts as a keyboard modifier) and Two-Hand Gestures (which reduce accidental triggers).

## Proposed Changes

We will modify the following files:

1. **`src/gesture_recognizer.py`** [MODIFY]: Update `Gesture` enum, `get_finger_states`, and implement two-hand multi-gesture detection.
2. **`main.py`** [MODIFY]: Integrate the two-hand recognizer, update the top HUD and per-hand badges, and render the hold indicators for SAVE (1s), CLEAR CANVAS (2s), and UNDO (500ms).

---

### Component: Gesture Recognition v2

#### [MODIFY] [gesture_recognizer.py](file:///d:/VirtualDrawer/src/gesture_recognizer.py)

We will update `src/gesture_recognizer.py` to support two-hand logic:
- A new method `recognize_hands(self, all_hands)` that detects:
  1. **Two-Hand Gestures**:
     - `SAVE` (Right Thumb + Left Thumb, hold 1s)
     - `CLEAR_CANVAS` (Right Palm + Left Palm, hold 2s)
     - `UNDO` (Right Index + Left Index, hold 500ms)
     - `REDO` (Right 2 Fingers + Left 2 Fingers)
     - `VOICE_COMMAND` (Right 🤙 + Left 🤙)
     - `ZOOM` (Right Pinch + Left Pinch)
     - `NEXT_TOOL` (Right 3 Fingers + Left 3 Fingers)
  2. **Single-Hand Gestures** (if two-hand matches fail or only one hand is visible):
     - **Right Hand (Dominant)**:
       - `DRAW` (Index UP, others DOWN)
       - `SELECT` (Index + Middle UP, others DOWN)
       - `PAUSE` (All UP / Open Palm)
       - `PINCH` (Thumb + Index pinch)
     - **Left Hand (Modifier)**:
       - `ERASE` (Index, Middle, Ring UP, others DOWN)
       - `TEXT_MODE` (Index, Middle UP, others DOWN)
       - `BRUSH_MENU` (Thumb UP, others DOWN)
       - `COLOR_MENU` (Pinky UP, others DOWN)

##### Gesture Enum Definition:
```python
class Gesture:
    NONE = "none"
    # Single hand
    DRAW = "draw"
    SELECT = "select"
    PAUSE = "pause"
    PINCH = "pinch"
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
```

---

### Component: Main Application

#### [MODIFY] [main.py](file:///d:/VirtualDrawer/main.py)

We will update the application loop to:
- Retrieve `all_hands` from `tracker.get_all_landmarks`.
- Call `gesture_detector.recognize_hands(all_hands)`.
- Render a premium visual HUD showing both hands and their active modes.
- Show circular/arc hold progress bars on screen for `SAVE` (1s), `CLEAR_CANVAS` (2s), and `UNDO` (500ms) when they are in progress.

---

## Verification Plan

### Manual Verification
1. Run the camera feed:
   ```bash
   python main.py
   ```
2. Run the mock unit tests using the modified [`verify_recognizer.py`](file:///d:/VirtualDrawer/verify_recognizer.py) to assert correct logic mapping.
