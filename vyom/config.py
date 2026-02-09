import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Global Configuration for Vyom AI (API Mode Only)
MODE = "api" 

# API Keys
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

DEVICE = "cpu"
