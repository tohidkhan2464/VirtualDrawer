# 🖐️ VirtualDrawer — Gestures Guide

> **Hand Convention**
> - **Right Hand** = Action hand — controls the cursor and triggers mode actions.
> - **Left Hand** = Modifier hand — controls drawing tools, modifiers, and power-ups.
> - Both hands together enable special two-handed gestures.

---

## Gesture Glossary

| Symbol | Meaning |
|--------|---------|
| ☝️ | Index finger raised, all others folded |
| ✌️ | Index + Middle raised, others folded |
| 🤟 | Index + Middle + Ring raised, pinky folded |
| 👋 | All four fingers raised (Open Palm) |
| ✊ | All fingers folded (Fist) |
| 👍 | Only Thumb raised |
| 🤙 | Only Pinky raised |
| 🤘 | Index + Pinky raised (Rock Sign) |
| 🤙+ | Index + Middle + Pinky raised (Color Menu Sign) |
| 🤏 | Thumb and Index close together (Pinch) |

---

## 🏠 Menu State (Mode Selection)

> Shown at launch and whenever you return from any active mode.

| Gesture | Hand | Action |
|---------|------|--------|
| ☝️ Index Finger | **Right** | Move cursor to highlight a mode card |
| ✌️ Index + Middle | **Right** | **Select** the currently highlighted mode |

**Available modes:** Drawing · Piano · Game (Fruit Ninja) · OCR Mode · Voice Mode

---

## 🎨 Drawing Mode

> Activated by selecting **Drawing** from the menu.

### Core Drawing

| Gesture | Hand | Action |
|---------|------|--------|
| ☝️ Index Finger | **Right** | **Draw** — move index tip to paint on the canvas |
| ✌️ Index + Middle | **Right** | **Hover / Move** without drawing (lift stroke) |
| 🤟 Index + Middle + Ring | **Right** | **Return to Menu** |

### Eraser

| Gesture | Hand | Action |
|---------|------|--------|
| 🤙 Pinky Up | **Left** | **Toggle Eraser** on/off (single tap trigger) |
| ☝️ Index Finger (in eraser mode) | **Right** | **Erase** under the index tip |

### Brush Size

| Gesture | Hand | Action |
|---------|------|--------|
| 🤏 Pinch (thumb ↔ index close) | **Left** | **Adjust Brush Size** — spread fingers wider to increase size, pinch tighter to decrease |

### Color Selection

| Gesture | Hand | Action |
|---------|------|--------|
| 🤙+ Index + Middle + Pinky | **Left** | **Open Color Palette** popup |
| ☝️ + ✌️ (while palette open) | **Right** | Hover over a color swatch, then raise **Index + Middle** to select it |

> **Available colors:** Red · Green · Blue · Purple · Orange · Black

### History

| Gesture | Hand | Hold Duration | Action |
|---------|------|--------------|--------|
| ✊ Fist | **Left** | 0.8 s | **Undo** last stroke |
| 👍 Thumb Up | **Left** | 0.8 s | **Redo** |

### Canvas Actions

| Gesture | Both Hands | Hold Duration | Action |
|---------|-----------|--------------|--------|
| 👋 + 👋 Both Open Palms | Left + Right | 2.0 s | **Clear Canvas** |
| 👍 + 👍 Both Thumbs Up | Left + Right | 1.0 s | **Save** drawing to `saved_drawings/` |

### Toolbar Buttons (on-screen)

Point your right-hand cursor at any toolbar button at the top of the screen and hover for ~18 frames to trigger it.

| Button | Action |
|--------|--------|
| RED / GREEN / BLUE / BLACK | Switch pen color |
| DRAW | Switch back to draw mode |
| ERASE | Switch to eraser mode |
| NEON | Neon glow brush effect |
| RAIN | Rainbow cycling brush |
| SPARK | Sparkle brush effect |
| FIRE | Fire trail brush effect |
| GLOW | Gaussian glow brush effect |
| CLEAR | Clear the canvas |
| SAVE | Save current page as PNG |

---

## 🎹 Piano Mode

> Activated by selecting **Piano** from the menu.

### Playing Notes

| Gesture | Hand | Action |
|---------|------|--------|
| ☝️ Index Finger | **Right** | **Play note** — move index tip over piano keys to play |

### Sustain & Octave

| Gesture | Hand | Action |
|---------|------|--------|
| 👋 Open Palm | **Left** | **Sustain pedal** — hold to sustain currently pressed notes |
| 👍 Thumb Up | **Left** | **Octave Up** (1-second cooldown between changes) |
| 🤙 Pinky Up | **Left** | **Octave Down** (1-second cooldown between changes) |

### Instrument

| Gesture | Hand | Action |
|---------|------|--------|
| 🤘 Rock Sign (Index + Pinky) | **Left** | **Cycle to next instrument** (1-second cooldown) |

### Navigation

| Gesture | Hand | Action |
|---------|------|--------|
| 🤟 Index + Middle + Ring | **Right** | **Return to Menu** |

---

## 🍉 Game Mode — Fruit Ninja

> Activated by selecting **Game** from the menu.

### Slicing

| Gesture | Hand | Action |
|---------|------|--------|
| ☝️ Index Finger | **Right** | **Slice** — swing your index tip through fruits to cut them |

> 💥 Slicing a **BOMB** deducts 5 points and counts as a miss. Use Shield to deflect.

### Modifiers

| Gesture | Hand | Action |
|---------|------|--------|
| ✊ Fist | **Left** | **Shield** — deflects the next bomb hit (5-second cooldown after use) |
| 👋 Open Palm | **Left** | **Slow Motion** — slows fruit movement for up to 2 seconds (3–4 s cooldown) |

### Game Control

| Gesture | Both Hands | Hold Duration | Action |
|---------|-----------|--------------|--------|
| 👍 + 👍 Both Thumbs Up | Left + Right | 2.0 s | **Restart Game** |

### Navigation

| Gesture | Hand | Action |
|---------|------|--------|
| 🤟 Index + Middle + Ring | **Right** | **Return to Menu** |

---

## 🔤 OCR Mode — Handwriting Recognition

> Activated by selecting **OCR Mode** from the menu.

### Writing

| Gesture | Hand | Action |
|---------|------|--------|
| ☝️ Index Finger | **Right** | **Write** inside the orange OCR zone |

### Recognition & Output

| Gesture | Hand | Hold Duration | Action |
|---------|------|--------------|--------|
| 👋 Open Palm | **Left** | 1.0 s | **Recognize** handwriting (runs OCR on the current canvas) |
| 👍 Thumb Up | **Left** | instant | **Copy** recognized text to clipboard |
| 🤘 Rock Sign (Index + Pinky) | **Left** | instant | **Read aloud** recognized text via text-to-speech |

### Canvas

| Gesture | Both Hands | Hold Duration | Action |
|---------|-----------|--------------|--------|
| 👋 + 👋 Both Open Palms | Left + Right | 2.0 s | **Clear OCR Canvas** |

### Navigation

| Gesture | Hand | Action |
|---------|------|--------|
| 🤟 Index + Middle + Ring | **Right** | **Return to Menu** |

---

## 🎙️ Voice Mode

> Activated by selecting **Voice Mode** from the menu.

### Listening Control

| Gesture | Hand | Action |
|---------|------|--------|
| 👋 Open Palm | **Left** | **Start Listening** for a voice command |
| ✊ Fist | **Left** | **Stop Listening** |
| 👍 Thumb Up | **Left** | **Repeat Last Command** (re-applies the most recent recognized command) |

### Supported Voice Commands

| Say... | Effect |
|--------|--------|
| "clear" | Clear the canvas |
| "save" | Save the current drawing |
| "eraser" | Switch to eraser mode |
| "red" / "green" / "blue" / "black" / "purple" / "orange" | Change pen color |
| "piano" | Switch to Piano mode |
| "game" | Switch to Game mode |

### Navigation

| Gesture | Hand | Action |
|---------|------|--------|
| 🤟 Index + Middle + Ring | **Right** | **Return to Menu** |

---

## 🌙 System-Wide Behaviours

| Trigger | Action |
|---------|--------|
| No hand visible for **3 seconds** | System enters **Idle** mode — screen dims with "SYSTEM IDLE" message |
| Any hand detected | Wakes from Idle automatically |
| **Q** / **Esc** key | Quit application |

### Keyboard Shortcuts (Alternative to gestures)

| Key | Action |
|-----|--------|
| `C` | Clear canvas |
| `S` | Save drawing |
| `N` | New page |
| `[` | Previous page |
| `]` | Next page |
| `P` | Toggle Piano mode |
| `G` | Toggle Game mode |
| `O` | Switch to OCR mode |
| `V` | Switch to Voice mode |
| `Q` / `Esc` | Quit |

---

## 📐 Finger Detection Reference

> The system determines which fingers are "up" by comparing tip position vs. PIP joint:

| Finger | "Up" condition |
|--------|---------------|
| Index | Tip above PIP joint (landmark 8 above landmark 6) |
| Middle | Tip above PIP joint (landmark 12 above landmark 10) |
| Ring | Tip above PIP joint (landmark 16 above landmark 14) |
| Pinky | Tip above PIP joint (landmark 20 above landmark 18) |
| Thumb (Right hand) | Tip X > IP joint X |
| Thumb (Left hand) | Tip X < IP joint X |

> **Pinch distance** (thumb tip ↔ index tip) controls brush size: range 20–150 px maps to brush size 3–36 px.

---

*Generated for VirtualDrawer — Virtual Gesture Studio*
