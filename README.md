# Virtual Gesture Studio

Virtual Gesture Studio is a Python, OpenCV, and MediaPipe demo for drawing in the air with hand gestures. The core drawing board works with only `opencv-python`, `mediapipe`, and `numpy`; optional modules add OCR, voice feedback, piano notes, and a small gesture game.

## Install

### Using Poetry

Python 3.11 is required. Create and activate a virtual environment, then install Poetry and the project dependencies:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install poetry
poetry config virtualenvs.create false --local
poetry install
```

The `virtualenvs.create false` setting makes Poetry install into the already activated `.venv` environment. The project uses the PyTorch CPU package source configured in `pyproject.toml`.

### Using pip

Create and activate a virtual environment before installing the dependencies:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

For Windows PowerShell, activate the environment with `.venv\Scripts\Activate.ps1` instead.

### Core dependencies only

For a lighter install:

```bash
python -m pip install opencv-python mediapipe numpy
```

The full `requirements.txt` install includes optional OCR, voice feedback, piano, and game features.

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
