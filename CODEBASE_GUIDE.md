# VirtualDrawer Codebase Guide

This repository is a hand-gesture drawing demo built on OpenCV, MediaPipe, and NumPy, with optional voice, OCR, piano, and mini-game features. The active application flow runs from `main.py` into the modules under `src/`.

## How To Read The Codebase

1. Start with `main.py` to understand the runtime loop and mode switching.
2. Read `src/drawing_board.py` next, because it owns canvas state, toolbar actions, saving, pages, and the on-screen HUD.
3. Then read `src/hand_tracker.py` and `src/gesture_detector.py`, which convert camera frames into gesture states.
4. After that, inspect the optional feature modules: `src/virtual_piano.py`, `src/fruit_ninja.py`, `src/handwriting_ocr.py`, and `src/voice_commands.py`.
5. Finish with `README.md`, the two implementation plans, and the `temp/` snapshot tree.

## Active Files

### `main.py`
Entry point for the live app. It opens the webcam, processes each frame, detects hand gestures, dispatches drawing/erase/toolbar actions, and overlays the drawing board UI. It also wires in optional piano, game, OCR, and voice-command flows.

### `src/drawing_board.py`
Core UI and canvas manager. It owns the canvas and mask layers, toolbar buttons, colors, brush effects, page handling, saving, voice-command responses, status messaging, and frame composition.

### `src/gesture_detector.py`
Gesture classifier for a single detected hand. It turns MediaPipe landmarks into a `GestureState` with cursor position, finger states, pinch distance, brush size, and a shape hint. Current gestures include draw, move, brush resize, clear, pause, and shape detection.

### `src/hand_tracker.py`
MediaPipe wrapper that converts normalized hand landmarks into pixel-space coordinates. It returns `HandResult` objects with landmarks, handedness, and bounding boxes, and can also render hand landmarks back onto the frame.

### `src/virtual_piano.py`
Optional piano overlay. It lays out the keys, highlights the active key under the cursor, and plays note samples or generated tones through `pygame` when available.

### `src/fruit_ninja.py`
Optional mini-game. It spawns moving fruit, tracks score and misses, and renders the game overlay and finger-slice trail.

### `src/handwriting_ocr.py`
Optional handwriting OCR helper. It prepares the board image for text recognition, runs EasyOCR when installed, and returns a short status message plus structured detections.

### `src/voice_commands.py`
Optional voice input and speech output helper. It listens for one spoken command using `SpeechRecognition`, then can speak status messages with `pyttsx3` if installed.

### `README.md`
User-facing overview of the app. It explains installation, gestures, toolbar actions, keyboard shortcuts, voice commands, and the intended project layout.

### `requirements.txt`
Dependency list for the full demo. The base app needs OpenCV, MediaPipe, and NumPy; the rest are optional feature dependencies.

### `.gitignore`
Ignores Python cache, virtual environments, and generated drawing exports in `saved_drawings/`.


## Runtime Data And Media

### `assets/sounds/`
Asset folder reserved for extra sound effects. It is currently empty.

### `saved_drawings/`
Output folder for exported board images. It already contains saved drawings from prior runs.

## Suggested Reading Order

If you want a quick code review path, read these in order:

1. `main.py`
2. `src/drawing_board.py`
3. `src/hand_tracker.py`
4. `src/gesture_detector.py`
5. `src/virtual_piano.py`
6. `src/fruit_ninja.py`
7. `src/handwriting_ocr.py`
8. `src/voice_commands.py`
9. `README.md`
