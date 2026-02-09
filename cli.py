
import os
import sys
import uuid
import json
import time

# --- 1. SETUP PATHS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# --- CONFIGURATION ---
try:
    import vyom.config as config # type: ignore
except ImportError:
    class Config:
        MODE = "api"
    config = Config()

# Force API Mode
config.MODE = "api"

# --- IMPORTS ---
try:
    from vyom.engines import voice as voice_engine # type: ignore
    from vyom.core import automation # type: ignore
    from vyom.core import history as history_manager # type: ignore
    from vyom.core import internet # type: ignore
    from vyom.core.optimizer import performance # type: ignore
except ImportError as e:
    print(f"Error importing core modules: {e}")
    sys.exit(1)

from vyom.engines import image as image_engine # type: ignore
from vyom.engines import thinking as thinking_engine # type: ignore
from vyom.engines import math as math_engine # type: ignore
from vyom.engines import trinity as trinity_engine # type: ignore

CONFIG_FILE = "cli_config.json"

def get_device_id():
    """Gets or generates a unique device ID."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                return data.get('device_id')
        except:
            pass
    new_id = str(uuid.uuid4())
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump({"device_id": new_id}, f)
    except:
        pass
    return new_id

def setup_api_key():
    """Ensures Google API Key is present."""
    from dotenv import load_dotenv
    load_dotenv()
    
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        print("\n🔑 API KEY REQUIRED")
        print("To use Vyom AI, you need a Google Gemini API Key.")
        print("Get it for free here: https://aistudio.google.com/app/apikey")
        print("-" * 50)
        key = input("Enter your GOOGLE_API_KEY: ").strip()
        
        if key:
            # Save to .env
            with open(".env", "a") as f:
                f.write(f"\nGOOGLE_API_KEY={key}\n")
            # Reload env
            os.environ["GOOGLE_API_KEY"] = key
            # Update trinity config dynamically if needed, but it reloads env usually
            print("✅ Key saved! Restarting engine...")
            return True
        else:
            print("❌ No key provided. Exiting.")
            sys.exit(1)
            return False
    return True

def print_header():
    os.system('cls' if os.name == 'nt' else 'clear')
    from colorama import init, Fore, Style
    init()
    print(Fore.CYAN + "="*60)
    print("VYOM AI - API MODE".center(60))
    print("="*60 + Style.RESET_ALL)
    print(f"Engine: Google Gemini (Cloud)")
    print("Type 'exit' to quit, 'clear' to clean screen.")
    print("-" * 60)

def main():
    # 1. API Key Check
    setup_api_key()
    
    device_id = get_device_id()
    
    # 2. Init Voice
    print("Initializing Voice Engine...", end="", flush=True)
    try:
        voice_engine.initialize_voice_system()
        print(" Done.")
    except Exception as e:
        print(f"\nWarning: Voice engine failed to init: {e}")

    # 3. User Login/Registration
    user_profile = history_manager.get_user(device_id)
    if not user_profile:
        print("\nWelcome! Let's set up your profile.")
        name = input("Enter your name: ").strip() or "User"
        email = f"{name.lower().replace(' ', '')}_cli@local.com" 
        history_manager.register_user(device_id, name, email)
        user_profile = history_manager.get_user(device_id)
    
    # Start a new chat session
    chat = history_manager.start_new_chat(device_id)
    chat_id = chat['id'] if chat else None
    
    print_header()
    print(f"Hello, {user_profile.get('name')}! I am ready.")

    from colorama import Fore, Style

    while True:
        try:
            print(Fore.GREEN + f"\n[{user_profile.get('name', 'User')}]: " + Style.RESET_ALL, end="")
            user_input = input().strip()
            
            if not user_input: continue
            
            if user_input.lower() in ['exit', 'quit']:
                print("Goodbye!")
                break
                
            if user_input.lower() == 'clear':
                print_header()
                continue
            
            # --- PROCESS INPUT ---
            
            # 1. Automation
            auto_res = automation.simple_match(user_input)
            if auto_res:
                print(Fore.YELLOW + f"[Vyom AI]: {auto_res}" + Style.RESET_ALL)
                voice_engine.speak_text(auto_res)
                continue

            # 2. Live Data Check
            live_keywords = ['score', 'cricket', 'weather', 'stock', 'price', 'news', 'headlines', 'who won']
            if any(k in user_input.lower() for k in live_keywords):
                print(Fore.YELLOW + "[Vyom AI]: Searching live web..." + Style.RESET_ALL)
                search_res = internet.search_google(user_input)
                if search_res:
                    print(f"\n{search_res}\n")
                    voice_engine.speak_text("Here is the latest information I found.")
                    continue

            # 3. Image Generation
            is_image = any(k in user_input.lower() for k in ["generate image", "create image", "draw"])
            if is_image:
                 print(Fore.YELLOW + "[Vyom AI]: Generating image..." + Style.RESET_ALL)
                 try:
                    img_res = image_engine.generate(user_input)
                    print(f"[Vyom AI]: Image generated: {img_res}")
                 except Exception as e:
                    print(f"Failed: {e}")
                 continue

            # 4. General Intelligence
            print(Fore.YELLOW + "[Vyom AI]: Thinking..." + Style.RESET_ALL, end="", flush=True)
            
            history = history_manager.get_chat_history(device_id, chat_id) or []
            history_context = list(history)[-10:] # type: ignore 
            
            try:
                # Use trinity engine (Pure API)
                response = trinity_engine.generate_response(user_input, engine_type='general', history=history_context)
                
                # Clear "Thinking..." line
                print("\r" + " " * 20 + "\r", end="")
                
                print(Fore.CYAN + f"[Vyom AI]: {response}" + Style.RESET_ALL)
                voice_engine.speak_text(str(response))
                
                # Save to history
                history_manager.add_to_chat_history(device_id, chat_id, user_input, role="user")
                history_manager.add_to_chat_history(device_id, chat_id, str(response), role="assistant")
            except Exception as e:
                print(f"\nError: {e}")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\nCritical Error: {e}")
            pass

if __name__ == "__main__":
    main()
