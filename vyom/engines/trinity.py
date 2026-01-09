import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from vyom.core import internet # Fallback ke liye
from vyom.core import formatter # 🎨 New Formatter

# Load environment variables

load_dotenv()



# Configure Client Pool

keys_str = os.getenv("GOOGLE_API_KEYS") or os.getenv("GEMINI_API_KEY")

api_keys = [k.strip() for k in keys_str.split(',') if k.strip()] if keys_str else []

current_key_index = 0



# Fallback models with full path

FALLBACK_MODELS = [

    'gemini-2.5-flash',

    'gemini-2.0-flash',

    'gemini-2.5-pro',

    'gemini-flash-latest',

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

def generate_response(prompt, engine_type="general", history=[], user_api_key=None, attachments=[]):

    try:

        # 🖼️ Prepare Content Parts (prompt + attachments)

        content_parts = [prompt]

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



        # 1. Try with user provided key (BYOK) if exists

        if user_api_key:

            for model_id in FALLBACK_MODELS:

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

            

            for model_id in FALLBACK_MODELS:

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
