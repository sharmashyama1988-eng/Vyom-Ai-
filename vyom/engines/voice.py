"""
VYOM AI VOICE ENGINE (Optimized & Humanized)
Uses Edge TTS (Cloud) for high quality, 
Coqui TTS (Local) for human-like voice cloning,
and pyttsx3 (System) as fallback.
"""
import threading
import os
import pygame
import queue
import time
import sys
import asyncio
import torch
from vyom import config

# Global Queue
speech_queue = queue.Queue()

# State
pyttsx3_engine = None
coqui_engine = None
_initialized = False

# --- SHARED WORKER ---
def worker():
    """Processes the speech queue."""
    global pyttsx3_engine, coqui_engine
    
    # 1. Initialize Backup Engine (pyttsx3)
    try:
        import pyttsx3
        pyttsx3_engine = pyttsx3.init()
        pyttsx3_engine.setProperty('rate', 160)
    except Exception:
        pass

    # 2. Initialize Coqui TTS (Heavy Mode)
    if config.MODE == 'default':
        try:
            from TTS.api import TTS
            print("   🧠 Loading Human Voice Model (Coqui TTS)...")
            device = "cuda" if torch.cuda.is_available() else "cpu"
            coqui_engine = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
            print("   ✅ Human Voice Model Loaded.")
        except Exception as e:
            print(f"   ⚠️ Coqui TTS Init Failed: {e}")

    while True:
        data = speech_queue.get()
        if data is None:
            break
        
        text, lang, gender = data
        success = False
        
        # 1. Try Coqui TTS (Cloned/Human Voice) if in Default mode
        if config.MODE == 'default' and coqui_engine:
            try:
                _speak_coqui(text, lang)
                success = True
            except Exception as e:
                print(f"⚠️ Coqui Voice Failed: {e}")

        # 2. Try Optimized Cloud Voice (Edge TTS)
        if not success:
            try:
                _speak_edge(text, lang, gender)
                success = True
            except Exception as e:
                print(f"⚠️ Cloud Voice Failed (Offline?): {e}")
        
        # 3. Fallback to System Voice if all else fails
        if not success and pyttsx3_engine:
            try:
                print("   Using System Voice (Fallback)...")
                pyttsx3_engine.say(text)
                pyttsx3_engine.runAndWait()
            except Exception as e:
                print(f"❌ System Voice Error: {e}")

        speech_queue.task_done()

def _clean_text(text):
    """Removes markdown and special characters for cleaner speech."""
    import re
    # Remove markdown bold/italic
    text = text.replace("*", "").replace("_", "").replace("#", "")
    # Remove code blocks
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    # Remove URLS
    text = re.sub(r'http\S+', '', text)
    return text.strip()

# --- COQUI TTS (Human-like Cloning) ---
def _speak_coqui(text, lang):
    """Generates human-like speech using voice cloning."""
    output_file = "temp_ai_human.wav"
    speaker_wav = "my_voice.wav"
    
    text = _clean_text(text)
    if not text: return

    if not os.path.exists(speaker_wav):
        # Fallback if no user voice provided
        speaker_wav = None 
    
    # Map lang
    t_lang = "hi" if lang == "hi" else "en"
    
    print(f"   🎙️ Generating Human Voice (Cloning) - Lang: {t_lang}")
    coqui_engine.tts_to_file(
        text=text,
        speaker_wav=speaker_wav,
        language=t_lang,
        file_path=output_file
    )
    
    _play_audio(output_file)

# --- EDGE TTS (High Quality, Low CPU) ---
def _speak_edge(text, lang, gender):
    """Generates speech using Microsoft Edge Online Voices."""
    import edge_tts
    
    text = _clean_text(text)
    if not text: return

    # Select Voice based on Lang and Gender
    if lang == "hi":
        voice = "hi-IN-MadhurNeural" if gender == "male" else "hi-IN-SwaraNeural"
    else:
        voice = "en-IN-PrabhatNeural" if gender == "male" else "en-IN-NeerjaNeural"
        
    print(f"   🎙️ Generating Speech using: {voice}")
    output_file = "temp_ai_cloud.mp3"
    
    # Humanize: Slightly slower rate for better clarity and natural feel
    rate = "-5%"
    
    async def generate():
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        await communicate.save(output_file)
    
    asyncio.run(generate())
    _play_audio(output_file)

def _play_audio(file_path):
    """Helper to play audio file using pygame."""
    if os.path.exists(file_path):
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            pygame.mixer.music.unload()
        except Exception as e:
            print(f"❌ Audio Playback Error: {e}")

# --- INITIALIZATION ---
def initialize_voice_system():
    global _initialized
    if _initialized: return

    print(f"\n🎙️ Initializing Voice Engine (Mode: {config.MODE.upper()})...")
    
    # Initialize Audio Mixer
    try:
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.mixer.init()
    except Exception as e:
        print(f"❌ Audio Mixer Init Failed: {e}")

    # Start Worker
    threading.Thread(target=worker, daemon=True).start()
    _initialized = True

def is_ready():
    return _initialized

def speak_text(text: str, gender: str = None):
    if not is_ready(): return
    
    # Simple Lang detection
    is_hindi = any('\u0900' <= char <= '\u097f' for char in text)
    lang = "hi" if is_hindi else "en"
    
    # Use global/user gender if not provided
    # (In a real app, this would come from the current user session)
    
    speech_queue.put((text, lang, gender))
