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
        self._init_audio()

    def ensure_layout(self, width: int, height: int) -> None:
        top = height - 170
        bottom = height - 52
        margin = 24
        key_w = max(48, (width - margin * 2) // len(self.NOTES))
        self.keys = []
        for index, note in enumerate(self.NOTES):
            left = margin + index * key_w
            right = left + key_w - 4
            color = (245, 245, 245) if index % 2 == 0 else (230, 230, 230)
            self.keys.append(PianoKey(note, (left, top, right, bottom), color))

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
        cv2.putText(frame, "Virtual Piano", (28, frame.shape[0] - 188), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)
        if self.message:
            cv2.putText(frame, self.message, (28, frame.shape[0] - 205), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (180, 255, 255), 1, cv2.LINE_AA)

    def touch(self, point: Optional[Point]) -> Optional[str]:
        if self.cooldown > 0:
            self.cooldown -= 1
        if point is None:
            self.last_note = None
            return None
        for key in self.keys:
            if key.contains(point):
                if key.note != self.last_note or self.cooldown == 0:
                    self._play(key.note)
                    self.last_note = key.note
                    self.cooldown = 10
                    return key.note
                return None
        self.last_note = None
        return None

    def _init_audio(self) -> None:
        try:
            import pygame
            import pygame.sndarray
        except ImportError:  # pragma: no cover - optional dependency
            self.enabled = False
            self.message = "Install pygame for sound"
            return

        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=1)
            for note in self.NOTES:
                wav = self.asset_dir / f"{note}.wav"
                if wav.exists():
                    self.sounds[note] = pygame.mixer.Sound(str(wav))
                else:
                    self.sounds[note] = self._tone(pygame, self.FREQUENCIES[note])
            self.enabled = True
        except Exception as exc:  # pragma: no cover - audio device dependent
            self.enabled = False
            self.message = f"Audio unavailable: {exc}"

    def _tone(self, pygame, frequency: float):
        sample_rate = 44100
        duration = 0.22
        samples = np.arange(int(sample_rate * duration))
        envelope = np.linspace(1.0, 0.15, samples.size)
        wave = np.sin(2 * math.pi * frequency * samples / sample_rate) * envelope
        audio = (wave * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(audio)

    def _play(self, note: str) -> None:
        sound = self.sounds.get(note)
        if not sound:
            return
        try:
            sound.play()
        except Exception:
            pass
