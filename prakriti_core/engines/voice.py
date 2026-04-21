"""
PRAKRITI AI VOICE ENGINE (API Based)
Uses Edge TTS (Cloud) for high quality, 
and pyttsx3 (System) as fallback.
"""
import threading
import os
import queue
import time
import sys
import asyncio
import requests

try:
    import pygame
except ImportError:
    pygame = None

from prakriti_core import config

# Global Queue
speech_queue = queue.Queue()

# State
pyttsx3_engine = None
_initialized = False

# --- SHARED WORKER ---
def worker():
    """Processes the speech queue."""
    global pyttsx3_engine
    
    # Check if voice is disabled via Env
    if os.environ.get("DISABLE_VOICE") == "true":
        return

    # 1. Initialize Backup Engine (pyttsx3)
    try:
        import pyttsx3
        pyttsx3_engine = pyttsx3.init()
        pyttsx3_engine.setProperty('rate', 160)
    except Exception:
        pass

    while True:
        data = speech_queue.get()
        if data is None:
            break
        
        text, lang, gender = data
        success = False
        
        # 1. Try ElevenLabs (Premium Cloud Voice) if API Key exists
        if config.ELEVENLABS_API_KEY:
            try:
                _speak_elevenlabs(text, lang, gender)
                success = True
            except Exception as e:
                print(f"⚠️ ElevenLabs Voice Failed: {e}")

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

# --- ELEVENLABS TTS (Premium Cloud) ---
def _speak_elevenlabs(text, lang, gender):
    """Generates ultra-high quality speech using ElevenLabs API."""
    text = _clean_text(text)
    if not text: return

    # Default Voices
    voice_id = "21m00Tcm4labaDqWkj35" if gender == "female" else "TxGEqnHW4m3z4H957S0A"
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": config.ELEVENLABS_API_KEY
    }
    
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1" if lang != "hi" else "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    print(f"   🎙️ ElevenLabs Voice: {voice_id} (Lang: {lang})")
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        output_file = "temp_ai_eleven.mp3"
        with open(output_file, "wb") as f:
            f.write(response.content)
        _play_audio(output_file)
    else:
        raise Exception(f"ElevenLabs API Error: {response.text}")

# --- EDGE TTS (High Quality, Low CPU) ---
def _speak_edge(text, lang, gender):
    """Generates speech using Microsoft Edge Online Voices with High-Fidelity settings."""
    import edge_tts
    
    text = _clean_text(text)
    if not text: return

    # --- Natural Indian Voices Selection ---
    if lang == "hi":
        # Swara is highly expressive, Madhur is deep and clear
        voice = "hi-IN-SwaraNeural" if gender == "female" else "hi-IN-MadhurNeural"
    else:
        # Neerja and Prabhat are the latest, most natural sounding Indian-English voices
        voice = "en-IN-NeerjaNeural" if gender == "female" else "en-IN-PrabhatNeural"
        
    print(f"   🎙️ High-Fidelity Voice: {voice}")
    output_file = "temp_ai_cloud.mp3"
    
    # --- Humanization Parameters ---
    rate = "-10%"
    pitch = "+0Hz"
    
    async def generate():
        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        await communicate.save(output_file)
    
    asyncio.run(generate())
    _play_audio(output_file)

def _play_audio(file_path):
    """Helper to play audio file using pygame."""
    if pygame is None or pygame.mixer.get_init() is None:
        print("   🔇 Audio playback skipped (Server/No Audio Device)")
        return

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

    print(f"\n🎙️ Initializing Voice Engine...")
    
    # Initialize Audio Mixer
    try:
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.mixer.init()
        pygame.mixer.music.set_volume(0.5) 
    except Exception as e:
        print(f"❌ Audio Mixer Init Failed: {e}")

    # Start Worker
    threading.Thread(target=worker, daemon=True).start()
    _initialized = True

def set_volume(level: float):
    """Sets the volume (0.0 to 1.0)."""
    if pygame and pygame.mixer.get_init():
        try:
            level = max(0.0, min(1.0, level))
            pygame.mixer.music.set_volume(level)
            print(f"   🔊 Volume set to {int(level*100)}%")
        except Exception as e:
            print(f"⚠️ Volume Control Error: {e}")

def is_ready():
    return _initialized

def stop():
    """Stops all current and pending speech immediately."""
    # 1. Clear Queue
    with speech_queue.mutex:
        speech_queue.queue.clear()
    
    # 2. Stop Cloud/Pygame Audio
    if pygame and pygame.mixer.get_init():
        pygame.mixer.music.stop()
        
    # 3. Stop System Audio
    if pyttsx3_engine:
        try:
            pyttsx3_engine.stop()
        except:
            pass
            
    print("   🔇 Audio Stopped by User Action.")

def speak_text(text: str, gender: str = None):
    if not is_ready(): return
    
    is_hindi = any('\u0900' <= char <= '\u097f' for char in text)
    lang = "hi" if is_hindi else "en"
    
    speech_queue.put((text, lang, gender))
