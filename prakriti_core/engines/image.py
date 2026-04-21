"""
PRAKRITI IMAGE ANALYSIS ENGINE - Vision AI
========================================
Analyzes images and provides detailed insights

Features:
- Text extraction (OCR)
- Object detection
- Scene description
- Color analysis
- Face detection
- Image properties
"""
import os
import io
import base64
from pathlib import Path
from PIL import Image
import pytesseract # type: ignore
import cv2 # type: ignore
import numpy as np
from collections import Counter

# Google GenAI for advanced vision (if available)
try:
    from google import genai
    from google.genai import types
    from dotenv import load_dotenv
    load_dotenv()
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

class ImageAnalyzer:
    def __init__(self):
        """Initialize image analyzer with local and API capabilities"""
        self.api_key = os.getenv("GOOGLE_API_KEY") if HAS_GENAI else None
        
        # Local capabilities
        self.has_ocr = self._check_tesseract()
        self.has_cv = True  # OpenCV is in requirements
        
    def _check_tesseract(self):
        """Check if Tesseract is installed"""
        try:
            pytesseract.get_tesseract_version()
            return True
        except:
            return False
    
    def analyze(self, image_path, detailed=True):
        """
        Comprehensive image analysis
        
        Args:
            image_path (str): Path to image file
            detailed (bool): Include detailed AI description
            
        Returns:
            dict: Analysis results
        """
        if not os.path.exists(image_path):
            return {"error": f"Image not found: {image_path}"}
        
        print(f"\n👁️ Analyzing Image: {os.path.basename(image_path)}")
        
        results = {
            "file": os.path.basename(image_path),
            "path": image_path,
        }
        
        # 1. Basic Properties
        results["properties"] = self._get_properties(image_path)
        
        # 2. Color Analysis
        results["colors"] = self._analyze_colors(image_path)
        
        # 3. Text Extraction (OCR)
        results["text"] = self._extract_text(image_path)
        
        # 4. Object/Face Detection
        results["detection"] = self._detect_objects(image_path)
        
        # 5. AI Description (if API available)
        if detailed and self.api_key and HAS_GENAI:
            results["ai_description"] = self._ai_analyze(image_path)
        
        return results
    
    def _get_properties(self, image_path):
        """Extract basic image properties"""
        try:
            img = Image.open(image_path)
            return {
                "format": img.format,
                "mode": img.mode,
                "size": f"{img.width}x{img.height}",
                "width": img.width,
                "height": img.height,
                "file_size_kb": round(os.path.getsize(image_path) / 1024, 2)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _analyze_colors(self, image_path):
        """Analyze dominant colors in image"""
        try:
            img = Image.open(image_path)
            img = img.resize((150, 150))  # Reduce size for speed
            img = img.convert('RGB')
            
            # Get all pixels
            pixels = list(img.getdata())
            
            # Find dominant colors
            color_counter = Counter(pixels)
            dominant = color_counter.most_common(5)
            
            colors = []
            for rgb, count in dominant:
                hex_color = '#{:02x}{:02x}{:02x}'.format(*rgb)
                colors.append({
                    "hex": hex_color,
                    "rgb": rgb,
                    "percentage": round((count / len(pixels)) * 100, 2)
                })
            
            return colors
        except Exception as e:
            return {"error": str(e)}
    
    def _extract_text(self, image_path):
        """Extract text using OCR"""
        if not self.has_ocr:
            return {
                "status": "OCR not available",
                "message": "Install Tesseract: https://github.com/tesseract-ocr/tesseract"
            }
        
        try:
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img)
            
            # Clean up
            text = text.strip()
            
            return {
                "found": len(text) > 0,
                "text": text if text else "No text detected",
                "length": len(text)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _detect_objects(self, image_path):
        """Detect faces and basic objects using OpenCV"""
        try:
            img = cv2.imread(image_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Face detection using Haar Cascade
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            return {
                "faces": {
                    "count": len(faces),
                    "detected": len(faces) > 0,
                    "locations": [
                        {"x": int(x), "y": int(y), "w": int(w), "h": int(h)}
                        for (x, y, w, h) in faces
                    ] if len(faces) > 0 else []
                }
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _ai_analyze(self, image_path):
        """Advanced AI analysis using Google Gemini Vision"""
        try:
            print("   🤖 Running AI Vision Analysis...")
            
            client = genai.Client(api_key=self.api_key)
            
            # Read image
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            
            # Create prompt for comprehensive analysis
            prompt = """Analyze this image in detail and provide:
1. Main Subject: What is the primary focus?
2. Scene Description: Describe the overall scene
3. Objects: List all visible objects
4. Mood/Atmosphere: What feeling does it convey?
5. Quality Assessment: Technical quality (lighting, composition, clarity)
6. Suggestions: What could be improved?

Be specific and detailed."""
            
            response = client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_bytes(
                                data=image_bytes,
                                mime_type="image/jpeg"
                            ),
                            types.Part.from_text(prompt)
                        ]
                    )
                ]
            )
            
            return {
                "status": "success",
                "description": response.text
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def generate_summary(self, analysis):
        """Generate human-readable summary from analysis"""
        summary = []
        
        # Properties
        if "properties" in analysis and "error" not in analysis["properties"]:
            props = analysis["properties"]
            summary.append(f"📏 **Image Properties:**")
            summary.append(f"   - Size: {props['size']}")
            summary.append(f"   - Format: {props['format']}")
            summary.append(f"   - File Size: {props['file_size_kb']} KB")
        
        # Colors
        if "colors" in analysis and isinstance(analysis["colors"], list):
            summary.append(f"\n🎨 **Dominant Colors:**")
            for i, color in enumerate(analysis["colors"][:3], 1):
                summary.append(f"   {i}. {color['hex']} ({color['percentage']}%)")
        
        # Text
        if "text" in analysis and analysis["text"].get("found"):
            summary.append(f"\n📝 **Extracted Text:**")
            text = analysis["text"]["text"]
            preview = text[:200] + "..." if len(text) > 200 else text
            summary.append(f"   {preview}")
        
        # Detection
        if "detection" in analysis:
            faces = analysis["detection"].get("faces", {})
            if faces.get("count", 0) > 0:
                summary.append(f"\n👤 **Face Detection:**")
                summary.append(f"   - {faces['count']} face(s) detected")
        
        # AI Description
        if "ai_description" in analysis and analysis["ai_description"].get("status") == "success":
            summary.append(f"\n🤖 **AI Analysis:**")
            summary.append(f"{analysis['ai_description']['description']}")
        
        return "\n".join(summary)

# Quick analysis function for easy import
def analyze(image_path, detailed=True):
    """
    Quick image analysis
    
    Usage:
        from prakriti_core.engines import image
        result = image.analyze("photo.jpg")
        print(result)
    """
    analyzer = ImageAnalyzer()
    analysis = analyzer.analyze(image_path, detailed=detailed)
    summary = analyzer.generate_summary(analysis)
    
    return {
        "raw": analysis,
        "summary": summary
    }

# Backward compatibility - keep generate function but deprecate
def generate(prompt, style="realistic", negative_prompt="", width=1024, height=768):
    """
    DEPRECATED: Image generation moved to vyom_image.py
    Use: from prakriti_core.engines import vision
    """
    return "⚠️ Image generation has moved. Use 'python vyom_image.py' or import prakriti_core.engines.vision"