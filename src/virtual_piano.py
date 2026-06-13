from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import math

import cv2
import numpy as np


Point = Tuple[int, int]


@dataclass
class PianoKey:
    note: str
    rect: Tuple[int, int, int, int]
    color: Tuple[int, int, int]

    def contains(self, point: Point) -> bool:
        x, y = point
        left, top, right, bottom = self.rect
        return left <= x <= right and top <= y <= bottom


class VirtualPiano:
    NOTES = ["C", "D", "E", "F", "G", "A", "B", "C2"]
    FREQUENCIES = {
        "C": 261.63,
        "D": 293.66,
        "E": 329.63,
        "F": 349.23,
        "G": 392.00,
        "A": 440.00,
        "B": 493.88,
        "C2": 523.25,
    }

    def __init__(self, asset_dir: str = "assets/piano") -> None:
        self.asset_dir = Path(asset_dir)
        self.keys: List[PianoKey] = []
        self.last_note: Optional[str] = None
        self.cooldown = 0
        self.enabled = False
        self.sounds: Dict[str, object] = {}
        self.message = ""
        
        self.octave_offset = 0
        self.instruments = ["Classic", "Organ", "Retro", "Triangle"]
        self.instrument_index = 0
        self.active_channels: Dict[str, object] = {}
        self.sustain = False
        
        self._init_audio()

    def ensure_layout(self, width: int, height: int) -> None:
        piano_height = 118  

        top = (height - piano_height) // 2
        bottom = top + piano_height

        margin = 24
        key_w = max(48, (width - margin * 2) // len(self.NOTES))

        self.keys = []
        for index, note in enumerate(self.NOTES):
            left = margin + index * key_w
            right = left + key_w - 4

            color = (245, 245, 245) if index % 2 == 0 else (230, 230, 230)

            self.keys.append(
                PianoKey(
                    note,
                    (left, top, right, bottom),
                    color,
                )
            )

    def draw(self, frame: np.ndarray, cursor: Optional[Point]) -> None:
        if not self.keys:
            self.ensure_layout(frame.shape[1], frame.shape[0])

        overlay = frame.copy()
        for key in self.keys:
            fill = key.color
            if cursor and key.contains(cursor):
                fill = (120, 220, 255)
            left, top, right, bottom = key.rect
            cv2.rectangle(overlay, (left, top), (right, bottom), fill, -1)

        cv2.addWeighted(overlay, 0.72, frame, 0.28, 0, frame)
        for key in self.keys:
            left, top, right, bottom = key.rect
            cv2.rectangle(frame, (left, top), (right, bottom), (30, 30, 30), 2)
            cv2.putText(frame, key.note, (left + 18, bottom - 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (20, 20, 20), 2, cv2.LINE_AA)
        piano_top = self.keys[0].rect[1]

        # Draw current instrument, octave, and sustain status on HUD
        inst_text = f"Inst: {self.instruments[self.instrument_index]} | Octave: {self.octave_offset:+d} | Sustain: {'ON' if self.sustain else 'OFF'}"
        cv2.putText(
            frame,
            f"Virtual Piano - {inst_text}",
            (28, piano_top - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        if self.message:
            cv2.putText(
                frame,
                self.message,
                (28, piano_top - 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (180, 255, 255),
                1,
                cv2.LINE_AA,
            )

    def touch(self, point: Optional[Point], sustain_active: bool = False) -> Optional[str]:
        if self.cooldown > 0:
            self.cooldown -= 1
            
        self.sustain = sustain_active
        
        touched_note = None
        if point is not None:
            for key in self.keys:
                if key.contains(point):
                    touched_note = key.note
                    break

        if touched_note:
            if touched_note != self.last_note or self.cooldown == 0:
                self._play(touched_note)
                self.last_note = touched_note
                self.cooldown = 12
        else:
            self.last_note = None

        # Handle sustain release fading
        if not self.sustain:
            for note in list(self.active_channels.keys()):
                if note != touched_note:
                    channel = self.active_channels.get(note)
                    if channel:
                        try:
                            channel.fadeout(250)
                        except Exception:
                            pass
                    self.active_channels.pop(note, None)

        return touched_note

    def change_octave(self, amount: int) -> None:
        new_octave = max(-2, min(2, self.octave_offset + amount))
        if new_octave != self.octave_offset:
            self.octave_offset = new_octave
            self.regenerate_tones()

    def next_instrument(self) -> None:
        self.instrument_index = (self.instrument_index + 1) % len(self.instruments)
        self.regenerate_tones()

    def regenerate_tones(self) -> None:
        if not self.enabled:
            return
        try:
            import pygame
            factor = 2.0 ** self.octave_offset
            for note in self.NOTES:
                freq = self.FREQUENCIES[note] * factor
                self.sounds[note] = self._generate_instrument_tone(pygame, freq)
        except Exception as exc:
            self.message = f"Re-gen failed: {exc}"

    def _init_audio(self) -> None:
        try:
            import pygame
            import pygame.sndarray
        except ImportError:  # pragma: no cover - optional dependency
            self.enabled = False
            self.message = "Install pygame for sound"
            return

        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2)
            pygame.mixer.set_num_channels(16)
            for note in self.NOTES:
                self.sounds[note] = self._generate_instrument_tone(pygame, self.FREQUENCIES[note])
            self.enabled = True
        except Exception as exc:  # pragma: no cover - audio device dependent
            self.enabled = False
            self.message = f"Audio unavailable: {exc}"

    def _generate_instrument_tone(self, pygame, freq: float):
        sample_rate = 44100
        duration = 1.5
        t = np.arange(int(sample_rate * duration)) / sample_rate
        inst = self.instruments[self.instrument_index]

        if inst == "Classic":
            envelope = np.exp(-3.0 * t)
            wave = np.sin(2.0 * np.pi * freq * t) * envelope
        elif inst == "Organ":
            envelope = np.exp(-1.2 * t)
            wave = (np.sin(2.0 * np.pi * freq * t) +
                    0.5 * np.sin(4.0 * np.pi * freq * t) +
                    0.25 * np.sin(6.0 * np.pi * freq * t)) * envelope
            wave = wave / 1.75
        elif inst == "Retro":
            envelope = np.exp(-4.0 * t)
            wave = np.sign(np.sin(2.0 * np.pi * freq * t)) * envelope
        elif inst == "Triangle":
            envelope = np.exp(-2.0 * t)
            wave = (2.0 * np.abs(2.0 * (t * freq - np.floor(t * freq + 0.5))) - 1.0) * envelope
        else:
            envelope = np.exp(-3.0 * t)
            wave = np.sin(2.0 * np.pi * freq * t) * envelope

        audio = (wave * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(audio)

    def _play(self, note: str) -> None:
        sound = self.sounds.get(note)
        if not sound:
            return
        try:
            channel = sound.play()
            if channel:
                self.active_channels[note] = channel
        except Exception:
            pass
