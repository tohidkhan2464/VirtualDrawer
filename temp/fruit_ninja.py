from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple
import random

import cv2
import numpy as np


Point = Tuple[int, int]


@dataclass
class Fruit:
    x: float
    y: float
    vx: float
    vy: float
    radius: int
    color: Tuple[int, int, int]
    name: str


class FruitNinjaMiniGame:
    def __init__(self) -> None:
        self.fruits: List[Fruit] = []
        self.score = 0
        self.misses = 0
        self.frame = 0
        self.trail: List[Point] = []
        self.running = False

    def reset(self) -> None:
        self.fruits.clear()
        self.score = 0
        self.misses = 0
        self.frame = 0
        self.trail.clear()
        self.running = True

    def update(self, width: int, height: int, cutter: Optional[Point]) -> None:
        if not self.running:
            self.reset()
        self.frame += 1
        if self.frame % 28 == 0 and len(self.fruits) < 7:
            self._spawn(width, height)

        if cutter:
            self.trail.append(cutter)
            self.trail = self.trail[-12:]
        else:
            self.trail = self.trail[-8:]

        remaining: List[Fruit] = []
        for fruit in self.fruits:
            fruit.x += fruit.vx
            fruit.y += fruit.vy
            fruit.vy += 0.42
            cut = cutter and (fruit.x - cutter[0]) ** 2 + (fruit.y - cutter[1]) ** 2 < (fruit.radius + 12) ** 2
            if cut:
                self.score += 1
                continue
            if fruit.y - fruit.radius > height:
                self.misses += 1
                continue
            remaining.append(fruit)
        self.fruits = remaining

    def draw(self, frame: np.ndarray) -> None:
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 78), (frame.shape[1], frame.shape[0] - 44), (15, 20, 25), -1)
        cv2.addWeighted(overlay, 0.28, frame, 0.72, 0, frame)

        for fruit in self.fruits:
            center = (int(fruit.x), int(fruit.y))
            cv2.circle(frame, center, fruit.radius, fruit.color, -1)
            cv2.circle(frame, center, fruit.radius, (255, 255, 255), 2)
            cv2.putText(frame, fruit.name, (center[0] - 10, center[1] + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1, cv2.LINE_AA)

        for i in range(1, len(self.trail)):
            thickness = max(1, i // 2)
            cv2.line(frame, self.trail[i - 1], self.trail[i], (255, 255, 255), thickness)

        cv2.putText(frame, f"Fruit Ninja  Score: {self.score}  Misses: {self.misses}", (24, 118), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, "Slice fruit with your index finger. Press G to leave game mode.", (24, 148), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (220, 240, 255), 1, cv2.LINE_AA)

    def _spawn(self, width: int, height: int) -> None:
        palette = [
            ((0, 0, 255), "A"),
            ((0, 180, 0), "L"),
            ((0, 165, 255), "O"),
            ((200, 0, 200), "P"),
            ((0, 220, 220), "M"),
        ]
        color, name = random.choice(palette)
        x = random.randint(70, max(80, width - 70))
        vx = random.uniform(-3.2, 3.2)
        vy = random.uniform(-17.0, -12.5)
        radius = random.randint(18, 30)
        self.fruits.append(Fruit(x=x, y=height + radius, vx=vx, vy=vy, radius=radius, color=color, name=name))
