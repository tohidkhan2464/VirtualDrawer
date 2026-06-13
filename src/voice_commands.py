from __future__ import annotations

from dataclasses import dataclass


import queue
import threading


@dataclass
class VoiceResult:
    command: str
    message: str


class VoiceCommandListener:
    def __init__(self) -> None:
        self.result_queue = queue.Queue()
        self.cancel_listening = False
        self.is_currently_listening = False
        
        try:
            import speech_recognition as sr
        except ImportError:  # pragma: no cover - optional dependency
            self.sr = None
            self.error = "SpeechRecognition is not installed."
        else:
            self.sr = sr
            self.error = ""

        try:
            import pyttsx3
        except ImportError:  # pragma: no cover - optional dependency
            self.tts = None
        else:
            self.tts = pyttsx3.init()

    def start_listening_background(self) -> None:
        if self.is_currently_listening:
            return
        self.cancel_listening = False
        self.is_currently_listening = True
        
        def _worker():
            res = self.listen_once()
            if not self.cancel_listening:
                self.result_queue.put(res)
            self.is_currently_listening = False
            
        threading.Thread(target=_worker, daemon=True).start()

    def stop_listening_background(self) -> None:
        self.cancel_listening = True
        self.is_currently_listening = False

    def get_result(self) -> Optional[VoiceResult]:
        try:
            return self.result_queue.get_nowait()
        except queue.Empty:
            return None

    def listen_once(self, timeout: int = 4, phrase_time_limit: int = 4) -> VoiceResult:
        if self.sr is None:
            return VoiceResult("", self.error + " Run: python -m pip install SpeechRecognition")

        recognizer = self.sr.Recognizer()
        try:
            with self.sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            command = recognizer.recognize_google(audio).lower()
        except Exception as exc:  # pragma: no cover - microphone and network dependent
            return VoiceResult("", f"Voice command failed: {exc}")
        return VoiceResult(command, f"Heard: {command}")

    def speak(self, text: str) -> None:
        if not self.tts:
            return
        try:
            self.tts.say(text)
            self.tts.runAndWait()
        except Exception:
            pass
