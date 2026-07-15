from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple
import random
import math
import time
import cv2
import numpy as np
import pygame
from .utils.path import resource_path


Point = Tuple[int, int]
Color = Tuple[int, int, int]

pygame.mixer.init()


@dataclass
class Fruit:
    x: float
    y: float
    vx: float
    vy: float
    radius: int
    color: Color
    name: str
    angle: float = 0
    spin: float = 0
    is_bomb: bool = False


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    radius: float
    color: Color
    life: int


@dataclass
class FloatingText:
    x: float
    y: float
    text: str
    color: Color
    life: int
    scale: float = 1.0


class SoundManager:
    def __init__(self):
        self.enabled = True
        self.music_playing = False
        try:
            self.slice = pygame.mixer.Sound(resource_path("assets/sounds/slice.wav"))
            self.bomb = pygame.mixer.Sound(resource_path("assets/sounds/explosion.wav"))
            self.combo = pygame.mixer.Sound(resource_path("assets/sounds/combo.wav"))
            self.shield = pygame.mixer.Sound(resource_path("assets/sounds/shield.wav"))
            self.spawn = pygame.mixer.Sound(resource_path("assets/sounds/spawn.wav"))
            self.slow = pygame.mixer.Sound(resource_path("assets/sounds/slow.wav"))
            self.gameover = pygame.mixer.Sound(resource_path("assets/sounds/gameover.wav"))
            pygame.mixer.music.load(resource_path("assets/music/background.mp3"))
            pygame.mixer.music.set_volume(0.35)
            # pygame.mixer.music.play(-1)

        except Exception:
            self.enabled = False

    def play(self, sound):
        if not self.enabled:
            return
        try:
            sound.play()
        except:
            pass
        
    def start_music(self):
        if self.enabled and not self.music_playing:
            pygame.mixer.music.play(-1)
            self.music_playing = True

    def stop_music(self):
        if self.enabled and self.music_playing:
            pygame.mixer.music.stop()
            self.music_playing = False


class FruitNinjaMiniGame:
    def __init__(self):
        self.running = False
        self.frame = 0
        self.score = 0
        self.best_score = 0
        self.combo = 0
        self.combo_timer = 0
        self.misses = 0
        self.fruits: List[Fruit] = []
        self.particles: List[Particle] = []
        self.floating: List[FloatingText] = []
        self.trail: List[Point] = []
        self.last_slice_time = 0
        self.message = ""
        self.message_time = 0
        self.last_shield_trigger_time = 0
        self.shield_active = False
        self.slow_mo_start_time = None
        self.slow_mo_cooldown_end = 0
        self.screen_shake = 0
        self.countdown = 3
        self.countdown_start = time.time()
        self.sound = SoundManager()

    def reset(self):
        self.running = True
        self.frame = 0
        self.score = 0
        self.combo = 0
        self.combo_timer = 0
        self.misses = 0
        self.screen_shake = 0
        self.fruits.clear()
        self.particles.clear()
        self.floating.clear()
        self.trail.clear()
        self.last_shield_trigger_time = 0
        self.shield_active = False
        self.slow_mo_start_time = None
        self.slow_mo_cooldown_end = 0
        self.message = "SLICE!"
        self.message_time = time.time() + 2
        if self.sound.enabled:
            self.sound.start_music()

    def add_floating_text(self, x, y, text, color=(255, 255, 255)):
        self.floating.append(
            FloatingText(x=x, y=y, text=text, color=color, life=35, scale=1.0)
        )

    def create_splash(self, x, y, color):
        for _ in range(40):
            angle = random.random() * 2 * math.pi
            speed = random.uniform(2, 10)
            self.particles.append(
                Particle(
                    x=x,
                    y=y,
                    vx=math.cos(angle) * speed,
                    vy=math.sin(angle) * speed,
                    radius=random.uniform(2, 6),
                    color=color,
                    life=random.randint(20, 40),
                )
            )

    def shake(self, strength=12):
        self.screen_shake = strength

    def _spawn(self, width: int, height: int):
        # Bomb chance increases slightly with score
        bomb_probability = min(0.18 + self.score * 0.002, 0.30)
        is_bomb = random.random() < bomb_probability
        if is_bomb:
            color = (30, 30, 30)
            name = "BOMB"
            radius = 24

        else:
            palette = [
                ((40, 40, 255), "Apple"),
                ((0, 230, 0), "Lime"),
                ((0, 170, 255), "Orange"),
                ((180, 40, 220), "Plum"),
                ((0, 240, 240), "Melon"),
                ((70, 70, 255), "Cherry"),
                ((40, 255, 180), "Pear"),
                ((90, 70, 200), "Berry"),
                ((0, 255, 120), "Kiwi"),
                ((30, 120, 255), "Peach"),
            ]
            color, name = random.choice(palette)
            radius = random.randint(20, 32)

        x = random.randint(80, width - 80)
        vx = random.uniform(-4, 4)
        vy = random.uniform(-18, -13)
        spin = random.uniform(-10, 10)
        angle = random.uniform(0, 360)
        self.fruits.append(
            Fruit(
                x=x,
                y=height + radius,
                vx=vx,
                vy=vy,
                radius=radius,
                color=color,
                name=name,
                angle=angle,
                spin=spin,
                is_bomb=is_bomb,
            )
        )

        if self.sound.enabled:
            self.sound.play(self.sound.spawn)

    def update_combo(self):
        if self.combo_timer > 0:
            self.combo_timer -= 1

        else:
            self.combo = 0

    def register_slice(self):
        self.combo += 1
        self.combo_timer = 45
        if self.combo == 2:
            self.message = "DOUBLE SLICE!"

        elif self.combo == 3:
            self.message = "TRIPLE SLICE!"

        elif self.combo == 4:
            self.message = "QUAD SLICE!"

        elif self.combo >= 5:
            self.message = f"{self.combo} HIT COMBO!"

        if self.combo >= 2:
            self.sound.play(self.sound.combo)

        self.message_time = time.time() + 1.2

    def update_particles(self):
        alive = []
        for p in self.particles:
            p.x += p.vx
            p.y += p.vy
            p.vy += 0.15
            p.life -= 1
            p.radius *= 0.96
            if p.color == (120, 120, 120):
                p.radius *= 1.03
            if p.life > 0:
                alive.append(p)

        self.particles = alive

    def update_floating_text(self):
        alive = []
        for t in self.floating:
            t.y -= 1.5
            t.scale += 0.01
            t.life -= 1
            if t.life > 0:
                alive.append(t)

        self.floating = alive

    def update_screen_shake(self):
        if self.screen_shake > 0:
            self.screen_shake -= 1

    def update_fruit_physics(self, slow_motion=False):
        dt = 0.35 if slow_motion else 1.0
        for fruit in self.fruits:
            fruit.x += fruit.vx * dt
            fruit.y += fruit.vy * dt
            fruit.vy += 0.42 * dt
            fruit.angle = (fruit.angle + fruit.spin) % 360
            if fruit.is_bomb:
                self.bomb_smoke(fruit)

    def remove_dead_fruits(self, height):
        alive = []
        for fruit in self.fruits:
            if fruit.y - fruit.radius > height:
                if not fruit.is_bomb:
                    self.misses += 1
                continue
            alive.append(fruit)
        self.fruits = alive

    def spawn_controller(self, width, height):
        limit = 6 + self.score // 15
        limit = min(limit, 10)
        interval = max(12, 30 - self.score // 4)
        if self.frame % interval == 0:
            if len(self.fruits) < limit:
                amount = random.randint(1, 3)
                for _ in range(amount):
                    self._spawn(width, height)

    def update_trail(self, cutter):
        if cutter:
            self.trail.append(cutter)
            self.trail = self.trail[-18:]

        else:
            self.trail = self.trail[-10:]

    def score_popup(self, fruit):
        self.add_floating_text(fruit.x, fruit.y, "+1", (0, 255, 255))

    def bomb_explosion(self, fruit):
        self.score = max(0, self.score)
        self.combo = 0
        self.shake(18)
        self.create_splash(fruit.x, fruit.y, (0, 0, 255))
        self.sound.play(self.sound.bomb)
        self.message = "BOOM!"
        self.message_time = time.time() + 1.5

    def fruit_slice(self, fruit):
        self.score += 1
        self.register_slice()
        self.create_splash(fruit.x, fruit.y, fruit.color)
        self.score_popup(fruit)
        self.sound.play(self.sound.slice)

    def update(
        self,
        width: int,
        height: int,
        cutter: Optional[Point],
        shield_pressed: bool = False,
        slow_mo_pressed: bool = False,
    ):
        if not self.running:
            self.reset()

        self.frame += 1
        now = time.time()

        # Slow Motion
        slow_motion = False
        if slow_mo_pressed:
            if self.slow_mo_start_time is None:
                if now >= self.slow_mo_cooldown_end:
                    self.slow_mo_start_time = now
                    self.sound.play(self.sound.slow)

            else:
                elapsed = now - self.slow_mo_start_time
                if elapsed <= 2.0:
                    slow_motion = True
                else:
                    self.slow_mo_cooldown_end = now + 4
                    self.slow_mo_start_time = None

        else:
            if self.slow_mo_start_time is not None:
                self.slow_mo_cooldown_end = now + 3
                self.slow_mo_start_time = None

        # Shield
        shield_cd = (now - self.last_shield_trigger_time) < 5
        self.shield_active = shield_pressed and not shield_cd

        # Spawn Fruits
        self.spawn_controller(width, height)

        # Trail
        self.update_trail(cutter)

        # Physics
        self.update_fruit_physics(slow_motion)

        # Combo Timer
        self.update_combo()

        # Collision Detection
        alive = []
        for fruit in self.fruits:
            hit = False
            if cutter:
                dx = fruit.x - cutter[0]
                dy = fruit.y - cutter[1]
                hit = dx * dx + dy * dy < (fruit.radius + 18) ** 2
            if hit:
                if fruit.is_bomb:
                    if self.shield_active:
                        self.shield_deflect(fruit)
                        continue
                    else:
                        self.score = max(0, self.score - 5)
                        self.misses += 1
                        self.combo = 0
                        self.bomb_explosion(fruit)
                        continue
                else:
                    self.fruit_slice(fruit)
                    continue
            if fruit.y - fruit.radius > height:
                if not fruit.is_bomb:
                    self.combo = 0
                    self.misses += 1
                continue
            alive.append(fruit)
        self.fruits = alive

        # Best Score
        if self.score > self.best_score:
            self.best_score = self.score

        # Update Effects
        self.update_particles()
        self.update_floating_text()
        self.update_screen_shake()

        # Game Over
        if self.misses >= 10:
            self.running = False
            self.sound.play(self.sound.gameover)
            self.message = "GAME OVER"
            self.message_time = now + 3

    def game_accuracy(self):
        total = self.score + self.misses
        if total == 0:
            return 100
        return int(self.score / total * 100)

    def fruit_slice(self, fruit):
        self.score += 1
        if self.combo >= 2:
            self.score += self.combo // 2

        self.register_slice()
        self.create_splash(fruit.x, fruit.y, fruit.color)
        self.score_popup(fruit)
        self.sound.play(self.sound.slice)

    def draw(self, frame: np.ndarray):
        h, w = frame.shape[:2]
        now = time.time()

        # Background
        self.draw_background(frame)

        # Fruits
        self.draw_fruits(frame)

        # Juice Particles
        self.draw_particles(frame)

        # Sword Trail
        self.draw_trail(frame)

        # Shield
        if self.shield_active and self.trail:
            self.draw_shield(frame)

        # Floating +1
        self.draw_floating(frame)

        # HUD
        self.draw_hud(frame)
        self.draw_combo_banner(frame)
        self.draw_slow_motion(frame)

        # Messages
        self.draw_messages(frame)
        self.draw_achievement(frame)
        self.draw_countdown(frame)
        self.draw_fps(frame)

        self.draw_game_over(frame)

        # Screen Shake
        if self.screen_shake > 0:
            dx = random.randint(-self.screen_shake, self.screen_shake)
            dy = random.randint(-self.screen_shake, self.screen_shake)
            M = np.float32([[1, 0, dx], [0, 1, dy]])
            frame[:] = cv2.warpAffine(frame, M, (w, h))

    def draw_background(self, frame):
        h, w = frame.shape[:2]
        overlay = np.zeros_like(frame)
        for y in range(h):
            t = y / h
            color = (int(35 + 40 * t), int(55 + 60 * t), int(90 + 80 * t))
            cv2.line(overlay, (0, y), (w, y), color, 1)

        frame[:] = cv2.addWeighted(frame, 0.25, overlay, 0.75, 0)

        # Slow motion tint
        if self.slow_mo_start_time is not None:
            blue = frame.copy()
            cv2.rectangle(blue, (0, 0), (w, h), (255, 120, 40), -1)
            cv2.addWeighted(blue, 0.15, frame, 0.85, 0, frame)

        # vignette
        mask = np.zeros((h, w), np.uint8)
        cv2.circle(mask, (w // 2, h // 2), int(min(w, h) * 0.65), 255, -1)
        mask = cv2.GaussianBlur(mask, (201, 201), 0)

        for c in range(3):
            frame[:, :, c] = (frame[:, :, c] * (mask / 255)).astype(np.uint8)

    def draw_hud(self, frame):
        hud = frame.copy()
        cv2.rectangle(hud, (15, 15), (380, 120), (35, 35, 40), -1)
        cv2.addWeighted(hud, 0.55, frame, 0.45, 0, frame)
        cv2.putText(
            frame,
            f"SCORE {self.score}",
            (35, 50),
            cv2.FONT_HERSHEY_DUPLEX,
            0.9,
            (255, 255, 255),
            2,
        )
        cv2.putText(
            frame,
            f"BEST {self.best_score}",
            (35, 80),
            cv2.FONT_HERSHEY_DUPLEX,
            0.7,
            (0, 255, 255),
            2,
        )
        cv2.putText(
            frame,
            f"MISS {self.misses}/10",
            (220, 80),
            cv2.FONT_HERSHEY_DUPLEX,
            0.7,
            (50, 180, 255),
            2,
        )
        shield = max(0, 5 - (time.time() - self.last_shield_trigger_time))
        slow = max(0, self.slow_mo_cooldown_end - time.time())
        cv2.putText(
            frame,
            f"Shield {'READY' if shield==0 else f'{shield:.1f}s'}",
            (25, 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 220, 120),
            2,
        )
        cv2.putText(
            frame,
            f"Slow {'READY' if slow==0 else f'{slow:.1f}s'}",
            (220, 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (150, 255, 255),
            2,
        )
        if self.combo >= 2:
            cv2.putText(
                frame,
                f"x{self.combo} COMBO",
                (frame.shape[1] - 230, 55),
                cv2.FONT_HERSHEY_DUPLEX,
                0.9,
                (0, 255, 255),
                2,
            )

    def draw_messages(self, frame):
        if time.time() > self.message_time:
            return
        scale = 1 + 0.08 * np.sin(time.time() * 15)
        size = cv2.getTextSize(self.message, cv2.FONT_HERSHEY_DUPLEX, scale, 3)[0]

        x = (frame.shape[1] - size[0]) // 2
        y = frame.shape[0] // 2
        color = (0, 255, 255)
        if "BOOM" in self.message:
            color = (0, 0, 255)

        if "GAME" in self.message:
            color = (255, 255, 255)

        cv2.putText(frame, self.message, (x, y), cv2.FONT_HERSHEY_DUPLEX, scale, color, 3)

    def draw_floating(self, frame):
        for t in self.floating:
            alpha = t.life / 35
            scale = t.scale + (1 - alpha) * 0.5
            cv2.putText(
                frame,
                t.text,
                (int(t.x), int(t.y)),
                cv2.FONT_HERSHEY_DUPLEX,
                scale,
                (0, 0, 0),
                5,
            )
            cv2.putText(
                frame,
                t.text,
                (int(t.x), int(t.y)),
                cv2.FONT_HERSHEY_DUPLEX,
                scale,
                t.color,
                2,
            )

    def draw_particles(self, frame):
        for p in self.particles:
            alpha = p.life / 40
            overlay = frame.copy()
            cv2.circle(
                overlay, (int(p.x), int(p.y)), max(1, int(p.radius * 2)), p.color, -1
            )
            cv2.addWeighted(overlay, alpha * 0.4, frame, 1 - alpha * 0.4, 0, frame)
            cv2.circle(frame, (int(p.x), int(p.y)), max(1, int(p.radius)), p.color, -1)

    def draw_shield(self, frame):
        x, y = self.trail[-1]
        pulse = int(4 * np.sin(time.time() * 8))
        overlay = frame.copy()
        cv2.circle(overlay, (x, y), 45 + pulse, (255, 220, 0), -1)
        cv2.addWeighted(overlay, 0.25, frame, 0.75, 0, frame)
        cv2.circle(frame, (x, y), 45 + pulse, (255, 255, 120), 3)

    def draw_trail(self, frame):
        if len(self.trail) < 2:
            return
        for i in range(1, len(self.trail)):
            alpha = i / len(self.trail)
            thick = max(2, int(alpha * 10))
            glow = (255, 255, int(255 * alpha))
            cv2.line(frame, self.trail[i - 1], self.trail[i], glow, thick + 6)
            cv2.line(frame, self.trail[i - 1], self.trail[i], (255, 255, 255), thick)

    def draw_fruits(self, frame):
        for fruit in self.fruits:
            if fruit.is_bomb:
                self.draw_bomb(frame, fruit)
            else:
                self.draw_fruit(frame, fruit)

    def draw_fruit(self, frame, fruit):
        x = int(fruit.x)
        y = int(fruit.y)
        r = fruit.radius

        # Shadow
        shadow = frame.copy()
        cv2.circle(shadow, (x + 6, y + 8), r, (20, 20, 20), -1)
        cv2.addWeighted(shadow, 0.22, frame, 0.78, 0, frame)

        # Main fruit
        cv2.circle(frame, (x, y), r, fruit.color, -1)

        # Dark rim
        cv2.circle(frame, (x, y), r, (30, 30, 30), 2)

        # Gloss
        cv2.circle(frame, (x - r // 3, y - r // 3), r // 3, (255, 255, 255), -1)
        cv2.circle(frame, (x - r // 3, y - r // 3), r // 5, (220, 220, 220), -1)

        # Stem
        stem_x = int(x + math.sin(math.radians(fruit.angle)) * 3)
        cv2.line(frame, (stem_x, y - r), (stem_x, y - r - 10), (40, 80, 20), 3)

        # Leaf
        leaf_x = int(stem_x + 8 * math.cos(math.radians(fruit.angle)))
        leaf_y = int(y - r - 5)
        cv2.ellipse(
            frame, (leaf_x, leaf_y), (7, 4), fruit.angle, 0, 360, (30, 180, 30), -1
        )

        # Rotating shine
        shine_x = int(x + math.cos(math.radians(fruit.angle)) * r * 0.45)
        shine_y = int(y + math.sin(math.radians(fruit.angle)) * r * 0.45)
        cv2.circle(frame, (shine_x, shine_y), 4, (255, 255, 255), -1)

    def draw_bomb(self, frame, bomb):
        x = int(bomb.x)
        y = int(bomb.y)
        r = bomb.radius
        pulse = int(4 * np.sin(time.time() * 8))

        # Shadow
        shadow = frame.copy()
        cv2.circle(shadow, (x + 6, y + 8), r, (0, 0, 0), -1)
        cv2.addWeighted(shadow, 0.25, frame, 0.75, 0, frame)

        # Bomb body
        cv2.circle(frame, (x, y), r, (35, 35, 35), -1)
        cv2.circle(frame, (x, y), r, (90, 90, 90), 2)

        # Glowing danger ring
        cv2.circle(frame, (x, y), r + pulse, (0, 0, 255), 2)

        # Metal cap
        cv2.rectangle(frame, (x - 5, y - r - 10), (x + 5, y - r), (180, 180, 180), -1)

        # Fuse
        cv2.line(frame, (x, y - r - 10), (x + 10, y - r - 22), (60, 120, 60), 2)

        # Burning spark
        if int(time.time() * 12) % 2 == 0:
            cv2.circle(frame, (x + 10, y - r - 22), 4, (0, 180, 255), -1)
            cv2.circle(frame, (x + 10, y - r - 22), 8, (0, 80, 255), 2)

        # Skull
        cv2.circle(frame, (x - 5, y - 2), 2, (255, 255, 255), -1)
        cv2.circle(frame, (x + 5, y - 2), 2, (255, 255, 255), -1)
        cv2.ellipse(frame, (x, y + 5), (7, 4), 0, 0, 180, (255, 255, 255), 2)

    def bomb_smoke(self, bomb):
        if random.random() > 0.25:
            return

        self.particles.append(
            Particle(
                x=bomb.x + random.randint(-4, 4),
                y=bomb.y - bomb.radius,
                vx=random.uniform(-0.4, 0.4),
                vy=random.uniform(-2, -1),
                radius=random.randint(5, 9),
                color=(120, 120, 120),
                life=20,
            )
        )

    def draw_combo_banner(self, frame):
        if self.combo < 2:
            return

        text = f"{self.combo} HIT COMBO"
        pulse = 1 + 0.08 * np.sin(time.time() * 10)
        size = cv2.getTextSize(text, cv2.FONT_HERSHEY_DUPLEX, pulse, 3)[0]
        x = (frame.shape[1] - size[0]) // 2
        cv2.putText(frame, text, (x, 170), cv2.FONT_HERSHEY_DUPLEX, pulse, (0, 0, 0), 6)
        cv2.putText(
            frame, text, (x, 170), cv2.FONT_HERSHEY_DUPLEX, pulse, (0, 255, 255), 3
        )

    def draw_slow_motion(self, frame):
        if self.slow_mo_start_time is None:
            return

        pulse = 1 + 0.05 * np.sin(time.time() * 8)

        cv2.putText(
            frame,
            "SLOW MOTION",
            (frame.shape[1] // 2 - 170, 70),
            cv2.FONT_HERSHEY_DUPLEX,
            pulse,
            (255, 200, 0),
            3,
        )

    def draw_game_over(self, frame):

        if self.running:
            return

        overlay = frame.copy()

        cv2.rectangle(overlay, (0, 0), frame.shape[:2][::-1], (0, 0, 0), -1)

        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        cx = frame.shape[1] // 2

        cv2.putText(
            frame,
            "GAME OVER",
            (cx - 170, 170),
            cv2.FONT_HERSHEY_DUPLEX,
            1.7,
            (255, 255, 255),
            4,
        )

        cv2.putText(
            frame,
            f"Score : {self.score}",
            (cx - 120, 250),
            cv2.FONT_HERSHEY_DUPLEX,
            1,
            (0, 255, 255),
            2,
        )

        cv2.putText(
            frame,
            f"Best : {self.best_score}",
            (cx - 120, 300),
            cv2.FONT_HERSHEY_DUPLEX,
            1,
            (255, 255, 255),
            2,
        )

        cv2.putText(
            frame,
            f"Accuracy : {self.game_accuracy()} %",
            (cx - 120, 350),
            cv2.FONT_HERSHEY_DUPLEX,
            1,
            (120, 255, 120),
            2,
        )

        cv2.putText(
            frame,
            "Pinch to Restart",
            (cx - 150, 430),
            cv2.FONT_HERSHEY_DUPLEX,
            0.9,
            (255, 200, 50),
            2,
        )

    def draw_achievement(self, frame):
        if self.score == 25:
            text = "FRUIT MASTER"

        elif self.score == 50:
            text = "NINJA MASTER"

        elif self.score == 100:
            text = "LEGEND"

        else:
            return

        cv2.putText(
            frame,
            text,
            (frame.shape[1] // 2 - 140, 120),
            cv2.FONT_HERSHEY_DUPLEX,
            1.2,
            (0, 255, 255),
            3,
        )

    def draw_countdown(self, frame):
        elapsed = time.time() - self.countdown_start
        if elapsed > 3:
            return

        value = 3 - int(elapsed)
        text = str(value) if value > 0 else "SLICE!"
        scale = 3 - (elapsed % 1)
        size = cv2.getTextSize(text, cv2.FONT_HERSHEY_DUPLEX, scale, 5)[0]
        x = (frame.shape[1] - size[0]) // 2
        y = frame.shape[0] // 2
        cv2.putText(
            frame, text, (x, y), cv2.FONT_HERSHEY_DUPLEX, scale, (255, 255, 255), 5
        )

    def draw_fps(self, frame):
        now = time.time()
        if not hasattr(self, "last_frame_time"):
            self.last_frame_time = now
            self.fps = 0

        dt = now - self.last_frame_time
        if dt > 0:
            self.fps = 1 / dt

        self.last_frame_time = now
        cv2.putText(
            frame,
            f"{int(self.fps)} FPS",
            (frame.shape[1] - 120, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (180, 255, 180),
            2,
        )
