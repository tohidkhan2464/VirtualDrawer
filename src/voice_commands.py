from __future__ import annotations

from dataclasses import dataclass
import datetime
from typing import Optional
import pyttsx3
import speech_recognition as sr
import queue
import threading
import traceback


@dataclass
class VoiceResult:
    command: str
    message: str


class VoiceCommandListener:
    def __init__(self) -> None:
        self.result_queue = queue.Queue()
        self.cancel_listening = False
        self.is_currently_listening = False
        self.sr = sr
        self.error = ""
        self.audio = None

        self.tts = pyttsx3.init()
        self.tts_queue = queue.Queue()
        threading.Thread(target=self._tts_worker, daemon=True).start()

    def _tts_worker(self):
        while True:
            text = self.tts_queue.get()

            if text is None:
                break

            try:
                self.tts.say(text)
                self.tts.runAndWait()
            except Exception as e:
                print(f"Error occurred while speaking: {e}")

    def start_listening_background(self):
        print("Starting background listening...")
        if self.is_currently_listening:
            return

        self.cancel_listening = False
        self.is_currently_listening = True

        def worker():
            recognizer = sr.Recognizer()

            with sr.Microphone(device_index=0) as source:
                recognizer.adjust_for_ambient_noise(source, duration=1)
                recognizer.dynamic_energy_threshold = False
                recognizer.energy_threshold = 300
                recognizer.pause_threshold = 1.0
                recognizer.non_speaking_duration = 0.5
                print("Listening for voice command...")
                audio = recognizer.record(source, duration=5)
                audio_data = audio.get_wav_data()
                output_path = (
                    f"{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.wav"
                )
                with open(output_path, "wb") as f:
                    f.write(audio_data)
            try:
                command = recognizer.recognize_google(audio).lower()
                print(f"Recognized command: {command}")
                self.result_queue.put(VoiceResult(command, command))
            except sr.WaitTimeoutError:
                print("No speech detected within the timeout.")
                self.result_queue.put(
                    VoiceResult("", "No speech detected within the timeout.")
                )
            except sr.UnknownValueError:
                print("Could not understand the speech.")
                self.result_queue.put(VoiceResult("", "Could not understand the speech."))

            except sr.RequestError as e:
                print(f"Speech service unavailable: {e}")
                self.result_queue.put(VoiceResult("", f"Speech service unavailable: {e}"))

            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                traceback.print_exc()
            self.is_currently_listening = False

        threading.Thread(target=worker, daemon=True).start()

    def get_result(self) -> Optional[VoiceResult]:
        try:
            return self.result_queue.get_nowait()
        except queue.Empty:
            return None

    def speak(self, text):
        self.tts_queue.put(text)
