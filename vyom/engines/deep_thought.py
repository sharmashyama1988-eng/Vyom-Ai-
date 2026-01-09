"""
VYOM DEEP THOUGHT ENGINE (Hybrid)
Supports:
1. Google Gemini (Cloud - BEST/Recommended) - Requires API Key
2. DuckDuckGo (Light - Backup) - If no API Key
3. LangChain/Ollama (Heavy - Legacy) - Requires GPU
"""

import logging
import threading
import os
import time
from vyom import config
from dotenv import load_dotenv
from google import genai  # NEW SDK

# Load env variables (API Keys)
load_dotenv(override=True)

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [DeepThought] - %(message)s')
logger = logging.getLogger("DeepThought")

# Fallback models
FALLBACK_MODELS = [
    'gemini-2.5-flash',
    'gemini-2.0-flash',
    'gemini-2.5-pro',
    'gemini-flash-latest',
]

class DeepThoughtEngine:
    _instance = None
    _lock = threading.Lock()
    
    # ... (rest of the class)

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DeepThoughtEngine, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        # We re-init partially to pick up new config/keys if they changed
        # but keep the singleton structure. 
        if getattr(self, "_initialized", False):
            return
            
        self.mode = config.MODE
        self.is_ready = False
        self.engine_type = "unknown"
        self.api_keys = []
        self.current_key_index = 0
        
        # Always init search as backup
        self._init_light()
        
        try:
            # 1. Check for Gemini API Keys (Load Balancer)
            load_dotenv(override=True)
            keys_str = os.getenv("GOOGLE_API_KEYS") or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            
            if keys_str:
                # Support comma separated keys
                self.api_keys = [k.strip() for k in keys_str.split(',') if k.strip()]
                if self.api_keys:
                    logger.info(f"💎 Found {len(self.api_keys)} Gemini API Keys! System is POWERFUL.")
                    self.engine_type = "gemini"
                    self.is_ready = True
            
            # 2. Fallback to Mode-based init
            if not self.api_keys:
                if self.mode == "default":
                    self._init_heavy()
                    self.engine_type = "ollama"
                else:
                    self.engine_type = "duckduckgo"
                    self.is_ready = True # Search is ready at least
            
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize engine: {e}")
            self.is_ready = False

    def _get_active_key(self):
        """Returns the current active key."""
        if not self.api_keys: return None
        return self.api_keys[self.current_key_index % len(self.api_keys)]

    def _rotate_key(self):
        """Switches to the next available key."""
        if not self.api_keys: return
        self.current_key_index += 1
        logger.info(f"🔄 Switching to API Key #{self.current_key_index % len(self.api_keys) + 1}...")

    def _init_heavy(self):
        """Initialize Ollama (Local Heavy)."""
        try:
            from langchain_ollama import OllamaLLM
            self.llm = OllamaLLM(model="llama3.2", temperature=0.7)
            logger.info("✅ Ollama LLM Connected.")
            self.is_ready = True
        except ImportError:
            pass

    def _init_light(self):
        """Initialize Search Tool (Local Light)."""
        # We now use the vyom.core.internet module directly to save on dependencies (langchain)
        try:
            from vyom.core import internet
            # Create a simple wrapper to match the expected interface if needed, 
            # or just use internet.search_google directly in solve()
            self.search = internet
            logger.info("✅ Search Engine Ready (Light).")
            self.is_ready = True
        except Exception as e:
            logger.error(f"Search Init Failed: {e}")
            self.search = None

    def solve(self, query, user_api_key=None):
        """
        Solves the query with Multi-Key Support & Auto-Fallback.
        Gemini (Key 1) -> Gemini (Key 2) -> ... -> Web Search.
        """
        gemini_success = False
        final_response = ""

        # --- 1. TRY GEMINI (Cloud Brain) ---
        if self.engine_type == "gemini" or user_api_key:
            
            # If user provided a specific key, try ONLY that key
            if user_api_key:
                for model_id in FALLBACK_MODELS:
                    final_response, gemini_success = self._try_gemini(query, user_api_key, model_id)
                    if gemini_success: break
            else:
                # Otherwise, try our pool of system keys (Rotation)
                for _ in range(len(self.api_keys)):
                    key = self._get_active_key()
                    for model_id in FALLBACK_MODELS:
                        response, success = self._try_gemini(query, key, model_id)
                        if success:
                            final_response = response
                            gemini_success = True
                            break
                    
                    if gemini_success:
                        break
                    
                    # If all models failed for this key, rotate and try next key
                    self._rotate_key()
            
            if gemini_success:
                return final_response, True
                
            # If we reached here, ALL Gemini keys and models failed.
            logger.warning("⚠️ All Gemini Keys and Models failed. Switching to Search Fallback.")

        # --- 2. TRY OLLAMA (Local Brain) ---
        elif self.engine_type == "ollama":
            try:
                from langchain_core.prompts import PromptTemplate
                template = "Answer this: {query}"
                prompt = PromptTemplate.from_template(template)
                chain = prompt | self.llm
                res = chain.invoke({"query": query})
                return res, True
            except:
                pass 

        # --- 3. FALLBACK: WEB SEARCH (The Safety Net) ---
        # This block MUST run if Gemini failed
        try:
            # Check for simple identity questions to avoid unnecessary search
            if "who are you" in query.lower():
                    return "I am Vyom, your AI assistant. (Currently in Offline/Search Mode).", True

            if self.search:
                logger.info("Performing Search Fallback...")
                # self.search is now the internet module
                res = self.search.search_google(query)
                return f"⚠️ **Cloud Busy (Rate Limits).**\nHere is what I found on the web:\n\n{res}", True
            else:
                 # Try re-initializing search if it was None
                 self._init_light()
                 if self.search:
                     res = self.search.search_google(query)
                     return f"⚠️ **Cloud Busy.**\nWeb Result:\n\n{res}", True
                     
        except Exception as se:
            logger.error(f"Search Failed: {se}")
            # Absolute final fallback if even search dies
            return "I am currently offline. Please check your internet connection or try again in a minute.", False
        
        return "System limits reached. Please wait 60 seconds.", False

    def _try_gemini(self, query, key, model_id):
        """Helper to try a specific key and model using the NEW Google Gen AI SDK."""
        try:
            # Initialize Client
            client = genai.Client(api_key=key)
            
            # System Prompt with Automation Instructions
            from vyom.core import formatter
            system_instruction = formatter.get_system_instruction("general")
            
            # Generate Content
            response = client.models.generate_content(
                model=model_id,
                contents=query,
                config={'system_instruction': system_instruction}
            )
            if response and response.text:
                return response.text, True
            return None, False
            
        except Exception as e:
            if "429" in str(e):
                logger.warning(f"Model {model_id} failed (Quota): {e}")
            elif "404" in str(e):
                logger.warning(f"Model {model_id} not found: {e}")
            else:
                logger.error(f"Gemini SDK Error with {model_id}: {e}")
            return None, False

# --- Module Level Interface ---

def solve(query, user_api_key=None):
    engine = DeepThoughtEngine()
    return engine.solve(query, user_api_key)