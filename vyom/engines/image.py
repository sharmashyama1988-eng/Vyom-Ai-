import random
import urllib.parse
import os
import time
from datetime import datetime
from PIL import Image
import io

# Optional: Google GenAI Integration
try:
    from google import genai
    from google.genai import types
    from dotenv import load_dotenv
    load_dotenv()
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

# --- 🎨 PROMPT ENHANCER ---
# Ye dictionary simple prompts ko "Professional" prompts mein badal degi
STYLES = {
    "realistic": "hyper-realistic, 8k resolution, cinematic lighting, photorealistic, detailed texture, ray tracing, unreal engine 5 render",
    "anime": "anime style, studio ghibli style, vibrant colors, detailed background, high quality drawing",
    "digital": "digital art, concept art, sharp focus, illustration, futuristic, cyberpunk vibe",
    "painting": "oil painting style, brush strokes, artistic, vincent van gogh style, masterpiece",
    "3d-model": "3d model, blender render, cycles render, high poly, detailed",
    "pixel-art": "pixel art, 8-bit, 16-bit, retro, classic video game style",
    "fantasy": "fantasy art, epic, detailed, matte painting, lord of the rings style",
    "steampunk": "steampunk, victorian, gears, cogs, detailed, intricate",
    "cyberpunk": "cyberpunk, futuristic, neon, Blade Runner style, high tech",
    "vaporwave": "vaporwave, retro, 80s, 90s, neon, palm trees, surreal",
    "pencil-drawing": "pencil drawing, sketch, black and awhite, detailed shading",
    "watercolor": "watercolor painting, soft, blended colors, artistic",
}

def enhance_prompt(user_prompt, style="realistic"):
    """
    User ke simple prompt ko 'Pro' prompt mein convert karta hai.
    """
    base_enhancement = "masterpiece, 8k, highly detailed, sharp focus, professional composition, award winning"
    
    # Agar user ne specific style select kiya hai to wo add karo, nahi to default realistic
    style_keywords = STYLES.get(style, STYLES["realistic"])
    
    # Final 'Pro' Prompt
    # If the prompt is already long/complex (likely from Visual Studio), we don't over-stuff it
    if len(user_prompt.split()) > 50:
        enhanced_prompt = f"{user_prompt}, {style_keywords}, cinematic lighting"
    else:
        enhanced_prompt = f"{user_prompt}, {style_keywords}, {base_enhancement}"
        
    return enhanced_prompt

# --- 🖼️ GENERATOR FUNCTION ---
def generate(prompt, style="realistic", negative_prompt="", width=1024, height=768):
    """
    Image generate karta hai aur Markdown wapas karta hai.
    """
    # 1. Prompt ko behtar banao
    clean_prompt = prompt.replace("generate image", "").replace("create image", "").strip()
    final_prompt = enhance_prompt(clean_prompt, style=style)
    
    # --- PRIORITY 1: Google Imagen 3 (High Quality) ---
    if HAS_GENAI:
        api_key = os.getenv("IMAGEN_API_KEY")
        if api_key:
            try:
                print(f"🎨 Generating with Google Imagen 3: {clean_prompt}...")
                client = genai.Client(api_key=api_key)
                
                response = client.models.generate_images(
                    model='imagen-3.0-generate-001',
                    prompt=final_prompt,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                        aspect_ratio="1:1" if width==height else "16:9" 
                    )
                )
                
                if response.generated_images:
                    # Decode and Save
                    image_bytes = response.generated_images[0].image.image_bytes
                    
                    # Ensure uploads dir exists
                    upload_dir = os.path.join(os.getcwd(), 'uploads')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    filename = f"gen_img_{int(time.time())}.png"
                    filepath = os.path.join(upload_dir, filename)
                    
                    image = Image.open(io.BytesIO(image_bytes))
                    image.save(filepath)
                    
                    return f"Here is your **Imagen 3** generated masterpiece based on **'{clean_prompt}'**:\n\n![Generated Image](/uploads/{filename})"
                    
            except Exception as e:
                print(f"⚠️ Imagen 3 Failed (Quota/Auth?): {e}. Falling back...")

    # --- PRIORITY 2: Pollinations.ai (Free Fallback) ---
    try:
        # 2. URL Safe banao (Spaces ko %20 mein badlo)
        encoded_prompt = urllib.parse.quote(final_prompt)
        
        # 3. Random Seed (Taaki har baar alag image bane)
        seed = random.randint(1, 100000)
        
        # 4. Construct URL (Using Pollinations API - Best Free Option)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&seed={seed}&model=flux"
        if negative_prompt:
            image_url += f"&negative={urllib.parse.quote(negative_prompt)}"

        print(f"🎨 Generating Image (Pollinations): {final_prompt}")
        
        return f"Here is your generated art based on **'{clean_prompt}'**:\n\n![Generated Image]({image_url})"
    
    except Exception as e:
        return f"❌ Image Generation Failed: {str(e)}"