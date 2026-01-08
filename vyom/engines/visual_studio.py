import os
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
from google import genai
from google.genai import types
from vyom.engines import image as image_gen_engine
import numpy as np

# Configure API (Reuse the one from trinity or env)
api_key = os.getenv("GEMINI_API_KEY")

class VisualStudio:
    def __init__(self):
        self.upload_folder = 'uploads'

    def load_image(self, path):
        return Image.open(path).convert("RGBA")

    def save_image(self, img, prefix="edit_"):
        filename = f"{prefix}{os.urandom(4).hex()}.png"
        path = os.path.join(self.upload_folder, filename)
        img.save(path, format="PNG")
        return f"/uploads/{filename}"

    def smart_merge(self, path1, path2, mode="horizontal"):
        """
        Merges two images intelligently.
        Modes: 'horizontal', 'vertical', 'blend', 'overlay'
        """
        try:
            img1 = self.load_image(path1)
            img2 = self.load_image(path2)

            # Resize to match the smaller dimension
            if mode in ['horizontal', 'blend', 'overlay']:
                # Match height
                target_h = min(img1.height, img2.height)
                img1 = ImageOps.fit(img1, (int(img1.width * target_h / img1.height), target_h))
                img2 = ImageOps.fit(img2, (int(img2.width * target_h / img2.height), target_h))
            elif mode == 'vertical':
                # Match width
                target_w = min(img1.width, img2.width)
                img1 = ImageOps.fit(img1, (target_w, int(img1.height * target_w / img1.width)))
                img2 = ImageOps.fit(img2, (target_w, int(img2.height * target_w / img2.width)))

            # Process
            if mode == 'horizontal':
                new_img = Image.new('RGBA', (img1.width + img2.width, img1.height))
                new_img.paste(img1, (0, 0))
                new_img.paste(img2, (img1.width, 0))
            
            elif mode == 'vertical':
                new_img = Image.new('RGBA', (img1.width, img1.height + img2.height))
                new_img.paste(img1, (0, 0))
                new_img.paste(img2, (0, img1.height))
            
            elif mode == 'blend':
                # Resize img2 to match img1 exactly for blending
                img2 = img2.resize(img1.size)
                new_img = Image.blend(img1, img2, alpha=0.5)
            
            elif mode == 'overlay':
                img2 = img2.resize(img1.size)
                # Simple composite
                new_img = Image.alpha_composite(img1, img2)

            return self.save_image(new_img, "merge_")

        except Exception as e:
            return f"Merge Error: {str(e)}"

    def generative_edit(self, image_paths, instruction, user_api_key=None):
        """
        Advanced Multi-Image Composition & Editing.
        Uses Gemini Vision to analyze multiple images and create a master prompt for Flux.
        """
        try:
            effective_key = user_api_key or api_key
            if not effective_key:
                return "⚠️ API Key missing."

            client = genai.Client(api_key=effective_key)
            
            # Step 1: Analyze all provided images
            model_id = 'gemini-2.5-flash'
            
            content_list = ["You are an expert image compositor and prompt engineer. Analyze these images and the user's instruction to create a single, highly detailed master prompt for a state-of-the-art image generator (Flux)."]
            
            for path in image_paths:
                if os.path.exists(path):
                    content_list.append(Image.open(path))
            
            content_list.append(f"\nUSER INSTRUCTION: {instruction}")
            content_list.append("\nTASK: Create a single, cohesive prompt that merges elements from these images according to the instruction. Describe style, lighting, composition, and specific object placements precisely.")

            response = client.models.generate_content(
                model=model_id,
                contents=content_list
            )
            master_prompt = response.text
            
            # Step 2: Generate the final image using the Flux engine
            print(f"🎨 Advanced Composition Prompt: {master_prompt[:100]}...")
            return image_gen_engine.generate(master_prompt)
            
        except Exception as e:
            return f"Advanced Edit Error: {str(e)}"

    def apply_filter(self, img_path, filter_name):
        """
        Applies standard filters.
        Filters: 'blur', 'sharpen', 'grayscale', 'sepia', 'contour'
        """
        try:
            img = self.load_image(img_path)
            
            if filter_name == 'blur':
                img = img.filter(ImageFilter.GaussianBlur(5))
            elif filter_name == 'sharpen':
                img = img.filter(ImageFilter.SHARPEN)
            elif filter_name == 'grayscale':
                img = img.convert("L").convert("RGBA")
            elif filter_name == 'contour':
                img = img.filter(ImageFilter.CONTOUR)
            elif filter_name == 'detail':
                img = img.filter(ImageFilter.DETAIL)
            
            return self.save_image(img, f"filter_{filter_name}_")
        except Exception as e:
            return f"Filter Error: {str(e)}"

# Singleton instance
editor = VisualStudio()