import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from vyom.core import internet # Fallback ke liye
from vyom.core import formatter # 🎨 New Formatter
from vyom.core import knowledge # 🧠 Internal Memory

# Load environment variables

load_dotenv()




# Configure Client Pool

keys_str = os.getenv("GOOGLE_API_KEYS") or os.getenv("GEMINI_API_KEY")

api_keys = [k.strip() for k in keys_str.split(',') if k.strip()] if keys_str else []

current_key_index = 0



# Fallback models with full path

FALLBACK_MODELS = [

    'gemini-3-pro',

]



def get_active_key():

    global current_key_index

    if not api_keys: return None

    return api_keys[current_key_index % len(api_keys)]



def rotate_key():

    global current_key_index

    if not api_keys: return

    current_key_index += 1

    print(f"🔄 Trinity: Switching to API Key #{current_key_index % len(api_keys) + 1}...")



def get_system_instruction(engine_type):
    return formatter.get_system_instruction(engine_type)

def generate_response(prompt, engine_type="general", history=[], user_api_key=None, attachments=[], model=None):

    try:

        # 🖼️ Prepare Content Parts (prompt + attachments)

        # 🧠 0. Check Internal Knowledge Base (Auto-Learner Data)
        internal_knowledge = knowledge.search_knowledge(prompt)
        final_prompt = prompt
        
        if internal_knowledge:
            print(f"🧠 Trinity: Found internal knowledge for this query.")
            final_prompt = f"{internal_knowledge}\n\n### User Query:\n{prompt}"
        
        content_parts = [final_prompt]

        if attachments:

            from PIL import Image

            for att in attachments:

                path = att.get('path')

                if path and os.path.exists(path):

                    try:

                        img = Image.open(path)

                        content_parts.append(img)

                    except Exception as ie:

                        print(f"Failed to load attachment {path}: {ie}")

        # 🚀 0.5. TRY LOCAL AI (KOBOLDPP -> OLLAMA)
        # Only if no attachments
        if not attachments:
            try:
                import requests
                import json
                
                # A. TRY KOBOLDPP (Preferred for GT 730)
                kobold_url = "http://localhost:5001/api/v1/generate"
                
                # Simple check if Kobold is running
                try:
                    # Quick ping (Kobold doesn't have a standard ping, so we just assume it works if port is open or try a dummy gen)
                    # Actually, we'll just try to generate directly.
                    pass 
                except:
                    pass

                # Kobold Payload
                payload_kobold = {
                    "prompt": f"{get_system_instruction(engine_type)}\n\n{final_prompt}\n\nResponse:",
                    "max_length": 512,
                    "temperature": 0.7
                }

                print(f"🐉 Trinity: Checking KoboldCPP (Port 5001)...")
                try:
                    response = requests.post(kobold_url, json=payload_kobold, timeout=2) # Fast check
                    if response.status_code == 200:
                        data = response.json()
                        res_text = data.get("results", [{}])[0].get("text", "").strip()
                        if res_text:
                            print("🐉 Trinity: KoboldCPP Success!")
                            return res_text
                except:
                    print("🐉 KoboldCPP not responding. Trying Ollama...")

                # B. TRY OLLAMA (Fallback)
                ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
                local_model = os.getenv("OLLAMA_MODEL", "mistral") 
                timeout_sec = int(os.getenv("OLLAMA_TIMEOUT", "5")) # Short timeout
                
                print(f"🦙 Trinity: Attempting Local Ollama ({local_model})...")
                
                payload_ollama = {
                    "model": local_model,
                    "prompt": f"{get_system_instruction(engine_type)}\n\n{final_prompt}",
                    "stream": False,
                    "options": {"temperature": 0.7}
                }
                
                response = requests.post(ollama_url, json=payload_ollama, timeout=timeout_sec)
                
                if response.status_code == 200:
                    data = response.json()
                    res_text = data.get("response", "")
                    if res_text:
                        print("🦙 Trinity: Ollama Success!")
                        return res_text
                    
            except Exception as e:
                print(f"⚠️ Local AI Failed: {str(e)}. Falling back to Cloud API...")

        # 1. Try with user provided key (BYOK) if exists

        if user_api_key:
            # If specific model requested, try it first, but fallback to others if it fails
            models_to_try = [model] if model else []
            for m in FALLBACK_MODELS:
                if m not in models_to_try:
                    models_to_try.append(m)
            
            for model_id in models_to_try:

                try:

                    client = genai.Client(api_key=user_api_key)

                    response = client.models.generate_content(

                        model=model_id,

                        contents=content_parts,

                        config=types.GenerateContentConfig(

                            system_instruction=get_system_instruction(engine_type),

                            temperature=0.7

                        )

                    )

                    if response and response.text:

                        return response.text

                except Exception as e:

                    print(f"⚠️ User Key + Model {model_id} failed: {e}")

            return "⚠️ Your personal API key failed. Please check it in settings."



        # 2. Try with system keys pool (Rotation)

        if not api_keys:

            return "⚠️ System API Keys missing. Please configure .env file."



        for _ in range(len(api_keys)):

            eff_key = get_active_key()

            client = genai.Client(api_key=eff_key)

            
            # If specific model requested, try it first, but fallback to others if it fails
            models_to_try = [model] if model else []
            for m in FALLBACK_MODELS:
                if m not in models_to_try:
                    models_to_try.append(m)

            for model_id in models_to_try:

                try:

                    # ⚡ Try model

                    response = client.models.generate_content(

                        model=model_id,

                        contents=content_parts,

                        config=types.GenerateContentConfig(

                            system_instruction=get_system_instruction(engine_type),

                            temperature=0.7

                        )

                    )

                    if response and response.text:

                        return response.text

                except Exception as e:

                    print(f"⚠️ Model {model_id} failed with current key: {e}")

                    continue # Try next model

            

            # If all models failed for this key, rotate and try next key

            rotate_key()

        

        # 🛡️ ULTIMATE FALLBACK: If all keys/models fail, search the web

        print("🌍 All AI models and keys failed. Using Web Search Fallback...")

        search_data = internet.search_google(prompt)

        if search_data:

            return f"⚠️ **AI Engines Busy (Rate Limits).** But I found this on the web:\n\n{search_data}"

            

        return "⚠️ System is temporarily overloaded. Please try again in a moment."



    except Exception as e:

        return f"⚠️ Engine Error: {str(e)}"
