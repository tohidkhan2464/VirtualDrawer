from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple
import random
import time

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
    is_bomb: bool = False


class FruitNinjaMiniGame:
    def __init__(self) -> None:
        self.fruits: List[Fruit] = []
        self.score = 0
        self.misses = 0
        self.frame = 0
        self.trail: List[Point] = []
        self.running = False
        
        self.last_shield_trigger_time = 0.0
        self.shield_active = False
        
        self.slow_mo_start_time: Optional[float] = None
        self.slow_mo_cooldown_end = 0.0
        
        self.message = ""
        self.message_time = 0.0

    def reset(self) -> None:
        self.fruits.clear()
        self.score = 0
        self.misses = 0
        self.frame = 0
        self.trail.clear()
        self.running = True
        self.last_shield_trigger_time = 0.0
        self.shield_active = False
        self.slow_mo_start_time = None
        self.slow_mo_cooldown_end = 0.0
        self.message = "Game Started!"
        self.message_time = time.time() + 1.5

    def update(self, width: int, height: int, cutter: Optional[Point], shield_pressed: bool = False, slow_mo_pressed: bool = False) -> None:
        if not self.running:
            self.reset()
        self.frame += 1
        
        now = time.time()
        
        # 1. Update slow motion state
        is_slow_mo = False
        if slow_mo_pressed:
            if self.slow_mo_start_time is None:
                if now >= self.slow_mo_cooldown_end:
                    self.slow_mo_start_time = now
            else:
                elapsed = now - self.slow_mo_start_time
                if elapsed <= 2.0:
                    is_slow_mo = True
                else:
                    self.slow_mo_cooldown_end = now + 4.0
                    self.slow_mo_start_time = None
        else:
            if self.slow_mo_start_time is not None:
                self.slow_mo_cooldown_end = now + 3.0
                self.slow_mo_start_time = None
                
        # 2. Update shield state
        shield_cooldown_active = (now - self.last_shield_trigger_time) < 5.0
        self.shield_active = shield_pressed and not shield_cooldown_active

        # 3. Spawn fruits and bombs
        if self.frame % 28 == 0 and len(self.fruits) < 7:
            self._spawn(width, height)

        if cutter:
            self.trail.append(cutter)
            self.trail = self.trail[-12:]
        else:
            self.trail = self.trail[-8:]

        # 4. Update fruit positions and collisions
        dt = 0.3 if is_slow_mo else 1.0
        remaining: List[Fruit] = []
        for fruit in self.fruits:
            fruit.x += fruit.vx * dt
            fruit.y += fruit.vy * dt
            fruit.vy += 0.42 * dt
            
            cut = cutter and (fruit.x - cutter[0]) ** 2 + (fruit.y - cutter[1]) ** 2 < (fruit.radius + 15) ** 2
            if cut:
                if fruit.is_bomb:
                    if self.shield_active:
                        self.last_shield_trigger_time = now
                        self.shield_active = False
                        self.message = "DEFLECTED!"
                        self.message_time = now + 1.2
                        continue
                    else:
                        self.score = max(0, self.score - 5)
                        self.misses += 1
                        self.message = "BOOM!"
                        self.message_time = now + 1.2
                        continue
                else:
                    self.score += 1
                    continue
                    
            if fruit.y - fruit.radius > height:
                if not fruit.is_bomb:
                    self.misses += 1
                continue
            remaining.append(fruit)
        self.fruits = remaining

    def draw(self, frame: np.ndarray) -> None:
        now = time.time()
        overlay = frame.copy()
        
        # Draw background tint for slow motion
        if self.slow_mo_start_time is not None:
            cv2.rectangle(overlay, (0, 78), (frame.shape[1], frame.shape[0] - 44), (45, 15, 15), -1)
            cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
        else:
            cv2.rectangle(overlay, (0, 78), (frame.shape[1], frame.shape[0] - 44), (15, 20, 25), -1)
            cv2.addWeighted(overlay, 0.28, frame, 0.72, 0, frame)

        # Draw fruits and bombs
        for fruit in self.fruits:
            center = (int(fruit.x), int(fruit.y))
            if fruit.is_bomb:
                # Draw black bomb with red details
                cv2.circle(frame, center, fruit.radius, (30, 30, 30), -1)
                cv2.circle(frame, center, fruit.radius, (0, 0, 255), 2)
                cv2.circle(frame, (center[0] + 10, center[1] - 10), 4, (0, 150, 255), -1) # fuse
                cv2.putText(frame, fruit.name, (center[0] - 15, center[1] + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 0, 255), 1, cv2.LINE_AA)
            else:
                cv2.circle(frame, center, fruit.radius, fruit.color, -1)
                cv2.circle(frame, center, fruit.radius, (255, 255, 255), 2)
                cv2.putText(frame, fruit.name, (center[0] - 10, center[1] + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1, cv2.LINE_AA)

        # Draw slicing trail
        for i in range(1, len(self.trail)):
            thickness = max(1, i // 2)
            cv2.line(frame, self.trail[i - 1], self.trail[i], (255, 255, 255), thickness)

        # Draw shield bubble around cutter if active
        cutter = self.trail[-1] if self.trail else None
        if cutter and self.shield_active:
            shield_overlay = frame.copy()
            cv2.circle(shield_overlay, cutter, 45, (255, 200, 0), -1) # Cyan bubble
            cv2.addWeighted(shield_overlay, 0.4, frame, 0.6, 0, frame)
            cv2.circle(frame, cutter, 45, (255, 255, 100), 2)

        # HUD Text
        shield_cd = max(0.0, 5.0 - (now - self.last_shield_trigger_time))
        slow_mo_cd = max(0.0, self.slow_mo_cooldown_end - now)
        
        status = f"Fruit Ninja  Score: {self.score}  Misses: {self.misses}"
        cv2.putText(frame, status, (24, 118), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)
        
        # Display modifiers state
        sh_text = f"Shield: {'ON' if self.shield_active else 'OFF' if shield_cd == 0 else f'CD {shield_cd:.1f}s'}"
        sm_text = f"SlowMo: {'ON' if self.slow_mo_start_time is not None else 'OFF' if slow_mo_cd == 0 else f'CD {slow_mo_cd:.1f}s'}"
        cv2.putText(frame, f"{sh_text} | {sm_text}", (24, 148), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (200, 240, 255), 1, cv2.LINE_AA)
        
        # Draw pop-up impact messages (e.g., "BOOM" or "DEFLECTED")
        if self.message and now < self.message_time:
            text_color = (0, 0, 255) if "BOOM" in self.message else (255, 200, 0)
            cv2.putText(frame, self.message, (frame.shape[1] // 2 - 80, frame.shape[0] // 2), cv2.FONT_HERSHEY_SIMPLEX, 1.2, text_color, 3, cv2.LINE_AA)

    def _spawn(self, width: int, height: int) -> None:
        # 18% chance of spawning a bomb
        is_bomb = random.random() < 0.18
        
        if is_bomb:
            color = (0, 0, 0)
            name = "BOMB"
            radius = 22
        else:
            palette = [
                ((0, 0, 255), "Apple"),
                ((0, 180, 0), "Lime"),
                ((0, 165, 255), "Orange"),
                ((200, 0, 200), "Plum"),
                ((0, 220, 220), "Melon"),
            ]
            color, name = random.choice(palette)
            radius = random.randint(18, 30)
            
        x = random.randint(70, max(80, width - 70))
        vx = random.uniform(-3.2, 3.2)
        vy = random.uniform(-17.0, -12.5)
        self.fruits.append(Fruit(x=x, y=height + radius, vx=vx, vy=vy, radius=radius, color=color, name=name, is_bomb=is_bomb))
