from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import cv2
import numpy as np


@dataclass
class OCRResult:
    text: str
    confidence: float


class HandwritingOCR:
    def __init__(self) -> None:
        try:
            import easyocr
        except ImportError:  # pragma: no cover - optional dependency
            self.reader = None
            self.error = "EasyOCR is not installed. Run: python -m pip install easyocr"
        else:
            self.reader = easyocr.Reader(["en"], gpu=False)
            self.error = ""

    def recognize(self, image_bgr: np.ndarray) -> Tuple[List[OCRResult], str]:
        if self.reader is None:
            return [], self.error

        prepared = self._prepare(image_bgr)
        detections = self.reader.readtext(prepared)
        results = [
            OCRResult(text=str(text), confidence=float(confidence))
            for _, text, confidence in detections
            if str(text).strip()
        ]
        if not results:
            return [], "No text recognized"
        summary = " ".join(result.text for result in results)
        return results, f"Recognized: {summary}"

    def _prepare(self, image_bgr: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        _, binary = cv2.threshold(gray, 245, 255, cv2.THRESH_BINARY_INV)
        if cv2.countNonZero(binary) == 0:
            return image_bgr
        x, y, w, h = cv2.boundingRect(binary)
        pad = 18
        top = max(0, y - pad)
        left = max(0, x - pad)
        bottom = min(image_bgr.shape[0], y + h + pad)
        right = min(image_bgr.shape[1], x + w + pad)
        cropped = image_bgr[top:bottom, left:right]
        return cv2.resize(cropped, None, fx=1.6, fy=1.6, interpolation=cv2.INTER_CUBIC)

    def copy_to_clipboard(self, text: str) -> bool:
        if not text.strip():
            return False
        try:
            import tkinter as tk
            r = tk.Tk()
            r.withdraw()
            r.clipboard_clear()
            r.clipboard_append(text)
            r.update()
            r.destroy()
            return True
        except Exception:
            return False

    def speak_text(self, text: str) -> None:
        if not text.strip():
            return
        import threading
        def _speak():
            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.say(text)
                engine.runAndWait()
            except Exception:
                pass
        threading.Thread(target=_speak, daemon=True).start()
