# Virtual Gesture Studio

Virtual Gesture Studio is a Python, OpenCV, and MediaPipe demo for drawing in the air with hand gestures. The core drawing board works with only `opencv-python`, `mediapipe`, and `numpy`; optional modules add OCR, voice feedback, piano notes, and a small gesture game.

## Install

```powershell
python -m pip install -r requirements.txt
```

For a lighter install:

```powershell
python -m pip install opencv-python mediapipe numpy
```

## Run

```powershell
python main.py
```

If your webcam is not device `0`:

```powershell
python main.py --camera 1
```

## Gestures

| Gesture | Action |
| --- | --- |
| Index finger up | Draw |
| Index + middle finger up | Move cursor |
| Thumb + index pinch | Adjust brush size |
| Open palm | Clear screen |
| Fist | Pause drawing |

Brush size changes only while the thumb + index resize gesture is active. When you return to drawing, the last selected brush size stays fixed. Use the toolbar to switch into eraser mode.

## Toolbar

Touch the virtual toolbar with your index finger to select:

- Colors: red, green, blue, black
- Effects: neon, rainbow, sparkle, fire, glow
- Tools: eraser, save, OCR, piano, game, page controls

## Keyboard Shortcuts

| Key | Action |
| --- | --- |
| `q` or `Esc` | Quit |
| `c` | Clear page |
| `s` | Save current page |
| `o` | OCR current page |
| `v` | Listen for one voice command |
| `p` | Toggle virtual piano |
| `g` | Toggle Fruit Ninja mini game |
| `n` | New page |
| `[` / `]` | Previous / next page |

## Voice Commands

Voice commands are optional and require `SpeechRecognition` plus a working microphone setup. Supported phrases include:

- "clear board"
- "save image"
- "change color red"
- "change color blue"
- "eraser mode"
- "piano open"
- "start game"

## Project Structure

```text
VirtualGestureStudio/
├── main.py
├── hand_tracker.py
├── gesture_detector.py
├── drawing_board.py
├── handwriting_ocr.py
├── voice_commands.py
├── virtual_piano.py
├── fruit_ninja.py
├── assets/
│   ├── piano/
│   ├── fruits/
│   ├── sounds/
│   └── icons/
├── saved_drawings/
└── requirements.txt
```


<!-- [tool.poetry]
name = "virtual_drawer"
version = "0.1.0"
description = ""
authors = ["Tohid Khan"]
readme = "README.md"

[[tool.poetry.source]]
name = "pytorch-cpu"
url = "https://download.pytorch.org/whl/cpu"
priority = "explicit"

[tool.poetry.dependencies]
python = ">=3.11,<3.12"
numpy = ">=1.24.0"
pygame = ">=2.5.0"
pyautogui = ">=0.9.54"
pillow = ">=10.0.0"
pyttsx3 = ">=2.90"
mediapipe = "0.10.14"
pyaudio = "^0.2.14"
torch = { source = "pytorch-cpu", version = "2.5.1" }

[tool.black]
line-length = 90
include = '\.pyi?$'
exclude = '''
/(
    \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[dependency-groups]
dev = [
    "pyinstaller (>=6.21.0,<7.0.0)"
] -->
