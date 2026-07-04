# 🖐️ VirtualDrawer — Gestures Guide

> **Hand Convention**
> - **Right Hand** = primary action hand in active modes.
> - **Left Hand** = menu selector and modifier hand.
> - Two hands enable the clear/save/restart gestures.

---

## Gesture Glossary

## Shared Controls

There is no single hand gesture that has the exact same effect in every mode, but the following controls are reused across multiple modes.

| Gesture | Hand | Effect |
|---------|------|--------|
| ☝️ Index Finger | **Left** | Move the menu cursor on the mode-selection screen |
| ✌️ Index + Middle | **Left** | Select the highlighted mode on the mode-selection screen |
| 🤟 Index + Middle + Ring | **Left** | Return to the menu from an active mode |
| 🤏 Pinch | **Right** | Adjust brush size in Drawing and OCR modes |
| No hand visible for 10 seconds | System | Enter Idle mode and show the idle message |
| Any hand detected | System | Wake from Idle automatically |
| **Q** / **Esc** key | System | Quit the application |

---

## 🏠 Menu State (Mode Selection)

> Shown at launch and whenever you return from an active mode.

| Gesture | Hand | Action |
|---------|------|--------|
| ☝️ Index Finger | **Left** | Move the cursor to highlight a mode card |
| ✌️ Index + Middle | **Left** | Select the currently highlighted mode |
| 🤟 Index + Middle + Ring | **Left** | Return to the menu (no effect in menu state) |

**Available modes:** Drawing · Piano · Game (Fruit Ninja) · OCR Mode

---

## 🎨 Drawing Mode

> Activated by selecting **Drawing** from the menu.

### Core Drawing

| Gesture | Hand | Action |
|---------|------|--------|
| ☝️ Index Finger | **Right** | Draw on the canvas |
| ✌️ Index + Middle | **Right** | Lift the stroke and move without drawing |
| 🤟 Index + Middle + Ring | **Left** | Return to the menu |

### Tool and Brush Control

| Gesture | Hand | Action |
|---------|------|--------|
| 🤙 Pinky Up | **Right** | Toggle eraser on/off |
| 🤏 Pinch | **Right** | Adjust brush size |
| 🤙 Index + Middle + Pinky | **Right** | Open the color palette |
| ☝️ + ✌️ while palette is open | **Right** | Hover a swatch and select it |

> **Selecting Color:** Move the cursor over a color using index + middle + ring finger and select the color using only index + middle finger.

> **Available colors:** Red · Green · Blue · Purple · Orange · Black

### History and Canvas Actions

| Gesture | Hand | Hold Duration | Action |
|---------|------|--------------|--------|
| ✊ Fist | **Left** | 0.8 s | Undo the last stroke |
| 👍 Thumb Up | **Left** | 0.8 s | Redo |
| 👋 + 👋 Both Open Palms | Left + Right | 2.0 s | Clear the canvas |
| 👍 + 👍 Both Thumbs Up | Left + Right | 1.0 s | Save the drawing to `saved_drawings/` |

### Voice Commands in Drawing Mode

| Gesture | Hand | Action |
|---------|------|--------|
| 👋 Open Palm | **Left** | Start background voice listening |

Supported voice commands while drawing: `clear`, `save`, `eraser`, `draw`, `red`, `green`, `blue`, `black`, `purple`, `orange`, `rainbow`, `neon`, `sparkle`, `fire`, `glow`, `piano`, `game`.

### Toolbar Buttons

Point the right-hand cursor at a toolbar button and hover for about 18 frames to trigger it.

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
| SAVE | Save the current page as PNG |

---

## 🎹 Piano Mode

> Activated by selecting **Piano** from the menu.

### Playing Notes

| Gesture | Hand | Action |
|---------|------|--------|
| ☝️ Index Finger | **Right** | Play notes by moving the index tip over the keys |

### Sustain, Volume, and Octave

| Gesture | Hand | Action |
|---------|------|--------|
| 4 Fingers Up | **Left** | Raise volume every 0.5 s |
| ✊ Fist | **Left** | Lower volume every 0.5 s |
| ☝️ Index Finger | **Left** | Octave up (1-second cooldown) |
| 🤙 Pinky Up | **Left** | Octave down (1-second cooldown) |

### Instrument

| Gesture | Hand | Action |
|---------|------|--------|
| 🤘 Rock Sign | **Left** | Cycle to the next instrument (1-second cooldown) |

### Navigation

| Gesture | Hand | Action |
|---------|------|--------|
| 🤟 Index + Middle + Ring | **Left** | Return to the menu |

---

## 🍉 Game Mode — Fruit Ninja

> Activated by selecting **Game** from the menu.

### Slicing

| Gesture | Hand | Action |
|---------|------|--------|
| ☝️ Index Finger | **Right** | Slice fruits by moving the index tip through them |

> Slicing a **BOMB** deducts 5 points and counts as a miss unless the shield is active.

### Modifiers

| Gesture | Hand | Action |
|---------|------|--------|
| ✊ Fist | **Left** | Shield the next bomb hit, with a 5-second cooldown |
| 4 Finger Up | **Left** | Slow motion for up to 2 seconds, then a 3-4 second cooldown |

### Game Control

| Gesture | Both Hands | Hold Duration | Action |
|---------|-----------|--------------|--------|
| 👍 + 👍 Both Thumbs Up | Left + Right | 2.0 s | Restart the game |

### Navigation

| Gesture | Hand | Action |
|---------|------|--------|
| 🤟 Index + Middle + Ring | **Left** | Return to the menu |

---

## 🔤 OCR Mode — Handwriting Recognition

> Activated by selecting **OCR Mode** from the menu.

### Writing

| Gesture | Hand | Action |
|---------|------|--------|
| ☝️ Index Finger | **Right** | Write inside the OCR page area |

### Recognition and Output

| Gesture | Hand | Hold Duration | Action |
|---------|------|--------------|--------|
| 👋 Open Palm | **Left** | 0.5 s | Recognize the handwriting on the current canvas |
| 👍 Thumb Up | **Left** | instant | Copy the recognized text to the clipboard |
| 🤘 Rock Sign | **Left** | instant | Read the recognized text aloud |

### Canvas

| Gesture | Both Hands | Hold Duration | Action |
|---------|-----------|--------------|--------|
| 👋 + 👋 Both Open Palms | Left + Right | 2.0 s | Clear the OCR canvas |

### Navigation

| Gesture | Hand | Action |
|---------|------|--------|
| 🤟 Index + Middle + Ring | **Left** | Return to the menu |

---

## 📐 Finger Detection Reference

> The detector determines which fingers are up by comparing tip position against the PIP joint:

| Finger | "Up" condition |
|--------|-----------------|
| Index | Tip above PIP joint (landmark 8 above landmark 6) |
| Middle | Tip above PIP joint (landmark 12 above landmark 10) |
| Ring | Tip above PIP joint (landmark 16 above landmark 14) |
| Pinky | Tip above PIP joint (landmark 20 above landmark 18) |
| Thumb (Right hand) | Tip X > IP joint X |
| Thumb (Left hand) | Tip X < IP joint X |

> **Pinch distance** (thumb tip ↔ index tip) controls brush size. The detector maps roughly 20–150 px to brush sizes 3–36 px.

---

*Generated for VirtualDrawer — Virtual Gesture Studio*
