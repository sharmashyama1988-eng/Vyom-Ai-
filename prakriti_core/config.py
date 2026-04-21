import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Global Configuration for Prakriti AI (Local Mode)
MODE = "local" # Switched to Local Ollama + Embeddings

# API Keys (Legacy / Optional)
# The user has requested to remove API dependencies.
# ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY") 
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

DEVICE = "cpu" # or "cuda" if available

