import random
import urllib.parse

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
    try:
        # 1. Prompt ko behtar banao
        clean_prompt = prompt.replace("generate image", "").replace("create image", "").strip()
        final_prompt = enhance_prompt(clean_prompt, style=style)
        
        # 2. URL Safe banao (Spaces ko %20 mein badlo)
        encoded_prompt = urllib.parse.quote(final_prompt)
        
        # 3. Random Seed (Taaki har baar alag image bane)
        seed = random.randint(1, 100000)
        
        # 4. Construct URL (Using Pollinations API - Best Free Option)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&seed={seed}&model=flux"
        if negative_prompt:
            image_url += f"&negative={urllib.parse.quote(negative_prompt)}"

        print(f"🎨 Generating Image: {final_prompt}")
        
        return f"Here is your generated art based on **'{clean_prompt}'**:\n\n![Generated Image]({image_url})"
    
    except Exception as e:
        return f"❌ Image Generation Failed: {str(e)}"