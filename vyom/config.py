import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Global Configuration for Vyom AI

# Options: "default" (Heavy/GPU), "light" (CPU/Low RAM)
# NOTE: For GT 730 (Compute 3.5), 'default' (Local LLM) will be very slow on CPU.
# We default to 'light' to use Cloud API (Gemini) which is instant, while using Local Hardware for Voice/Automation.
MODE = "light" 

# API Keys
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# Hardware Checks
try:
    from vyom.utils.hardware import HardwareConfig
    DEVICE = HardwareConfig.DEVICE
except ImportError:
    DEVICE = "cpu"

