"""
AUDIO CONVERTER (MP3 Version)
Converts sample.mp3 to my_voice.wav for AI cloning.
"""
from moviepy import AudioFileClip
import os

input_file = "sample.mp3"  # 🔥 Yahan hamne change kiya
output_file = "my_voice.wav"

if os.path.exists(input_file):
    print(f"🔄 Reading {input_file}...")
    
    # Audio load karke convert karo
    clip = AudioFileClip(input_file)
    clip.write_audiofile(output_file, codec='pcm_s16le')
    
    print(f"✅ Success! '{output_file}' ban gayi hai.")
    print("🚀 Ab tum 'python server.py' chala sakte ho!")
else:
    print(f"❌ Error: '{input_file}' nahi mili! File folder mein hai na?")