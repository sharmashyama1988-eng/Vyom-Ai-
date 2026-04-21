"""
PRAKRITI AI - Image Generation Engine
Integrates Pollinations.ai with Prakriti for AI-powered image creation
"""
import os
import sys

# Ensure vyom_image module is accessible
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from prakriti_core_image import PollinationsImageGen

# Global generator instance
_image_gen = None

def get_generator():
    """Get or create image generator instance"""
    global _image_gen
    if _image_gen is None:
        _image_gen = PollinationsImageGen(output_dir="generated_images")
    return _image_gen

def generate_image(prompt, width=1024, height=1024):
    """
    Generate an image from text prompt
    
    Usage in Prakriti:
        User: "Generate an image of a sunset beach"
        Prakriti: [Calls this function] → Image generated!
    """
    gen = get_generator()
    filepath, _ = gen.generate(prompt, width=width, height=height)
    return filepath

def batch_generate(prompts):
    """Generate multiple images"""
    gen = get_generator()
    return gen.batch_generate(prompts)

def show_gallery():
    """Show recent images"""
    gen = get_generator()
    gen.show_gallery()

# For direct import
__all__ = ['generate_image', 'batch_generate', 'show_gallery', 'PollinationsImageGen']
