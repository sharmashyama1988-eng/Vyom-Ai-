"""
VYOM EARS (Hearing Module)
This module runs in a background thread and listens for the wake word "Vyom".
"""
import speech_recognition as sr
import threading
import time
import os

class Ears:
    def __init__(self, callback_function=None):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.is_listening = False
        self.callback = callback_function # Function to call when "Vyom" is heard
        self.thread = None

    def listen_loop(self):
        """Continuous listening loop."""
        print("👂 Ears: Listening for 'Vyom' or 'Hey AI'...")
        
        # Adjust for ambient noise once
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
        while self.is_listening:
            try:
                with self.microphone as source:
                    # Listen for a short phrase (Wake Word)
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=3)
                
                # Recognize offline (faster) or online
                try:
                    # Try offline pocket sphinx if available, else google (online)
                    # Use 'en-IN' for better Indian Accent/Hinglish support
                    text = self.recognizer.recognize_google(audio, language="en-IN").lower()
                    print(f"   👂 Heard: {text}")
                    
                    if "vyom" in text or "hey ai" in text or "hello ai" in text:
                        print("   ⚡ Wake Word Detected!")
                        if self.callback:
                            self.callback()
                            
                except sr.UnknownValueError:
                    pass # Silence
                except sr.RequestError:
                    pass # Net down

            except Exception as e:
                # print(f"Ears Error: {e}")
                time.sleep(1)

    def start_listening(self):
        if not self.is_listening:
            self.is_listening = True
            self.thread = threading.Thread(target=self.listen_loop, daemon=True)
            self.thread.start()

    def stop_listening(self):
        self.is_listening = False
