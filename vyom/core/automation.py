import os
import webbrowser
import datetime
import platform
import subprocess
import urllib.parse
import re

# --- AUTOMATION TOOLS ---

def capture_camera_image():
    """Captures a single frame from the default camera."""
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return None, "Could not open camera."
        
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return None, "Failed to capture frame."
            
        if not os.path.exists("uploads"):
            os.makedirs("uploads")
            
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"capture_{timestamp}.jpg"
        path = os.path.join("uploads", filename)
        
        cv2.imwrite(path, frame)
        
        return filename, None
        
    except ImportError:
        return None, "Camera access requires 'opencv-python'. Please install it."
    except Exception as e:
        return None, f"Camera error: {e}"

def open_website(url_or_name):
    """Opens a website based on a name or URL."""
    sites = {
        "google": "https://google.com",
        "youtube": "https://youtube.com",
        "gmail": "https://mail.google.com",
        "github": "https://github.com",
        "stackoverflow": "https://stackoverflow.com",
        "reddit": "https://reddit.com",
        "chatgpt": "https://chat.openai.com",
        "whatsapp": "https://web.whatsapp.com",
        "spotify": "https://open.spotify.com"
    }
    
    target = url_or_name.lower().strip()
    
    if target in sites:
        url = sites[target]
    elif target.startswith("http"):
        url = target
    else:
        # Default to google search if not a known site/url
        url = f"https://www.google.com/search?q={target}"
        
    print(f"🌍 Opening: {url}")
    webbrowser.open(url)
    return f"Opening {target}..."

def get_system_time():
    return f"The time is {datetime.datetime.now().strftime('%I:%M %p')}."

def take_screenshot(url=None):
    """Takes a screenshot of a webpage (if URL) or desktop."""
    if not url:
        # Try local desktop screenshot
        try:
            from PIL import ImageGrab
            if not os.path.exists("uploads"): os.makedirs("uploads")
            path = f"uploads/screen_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            ImageGrab.grab().save(path)
            return f"✅ Desktop Screenshot saved: {path} [[IMAGE:{path}]]"
        except Exception:
            return "Desktop screenshot failed. Please ensure 'pillow' is installed."
        
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url)
            if not os.path.exists("uploads"): os.makedirs("uploads")
            path = f"uploads/web_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            page.screenshot(path=path)
            browser.close()
            return f"✅ Web Screenshot saved: {path}"
    except Exception as e:
        return f"Error: {e}"

def control_media(action):
    """Controls System Media/Volume (Windows Only for now)."""
    if platform.system() != "Windows": return "Media control is only optimized for Windows currently."
    
    try:
        import ctypes
        # Virtual Key Codes
        VK_VOLUME_UP = 0xAF
        VK_VOLUME_DOWN = 0xAE
        VK_VOLUME_MUTE = 0xAD
        VK_MEDIA_PLAY_PAUSE = 0xB3
        
        if action == "VOL_UP":
            for _ in range(5): ctypes.windll.user32.keybd_event(VK_VOLUME_UP, 0, 0, 0)
            return "Increased volume."
        elif action == "VOL_DOWN":
            for _ in range(5): ctypes.windll.user32.keybd_event(VK_VOLUME_DOWN, 0, 0, 0)
            return "Decreased volume."
        elif action == "PLAY_PAUSE":
            ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
            return "Media toggled."
    except:
        return "Failed to control media."

def play_on_youtube(query):
    """Searches and plays a video on YouTube directly."""
    clean_query = query.replace("play", "").replace("on youtube", "").strip()
    search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(clean_query)}"
    # Hum direct first result pe bhi bhej sakte hain using 'auto-play' trick
    # Lekin search results dikhana safer hai
    webbrowser.open(search_url)
    return f"Playing {clean_query} on YouTube..."

def fetch_india_news(city=None):
    """Fetches top headlines from India or a specific city."""
    from vyom.core import internet
    query = f"latest top news headlines in {city}" if city else "latest top news headlines India"
    news_data = internet.search_google(query)
    location_label = city if city else "India"
    return f"Here are the top headlines from **{location_label}** right now:\n\n{news_data}"

def run_system_command(app_name):
    """Runs a local system command or application."""
    try:
        if platform.system() == "Windows":
            if app_name == "calculator":
                subprocess.Popen("calc.exe")
            elif app_name == "notepad":
                subprocess.Popen("notepad.exe")
            elif app_name == "explorer":
                subprocess.Popen("explorer.exe")
            return f"Opening {app_name}..."
        return f"System commands are not yet supported on {platform.system()}."
    except Exception as e:
        return f"Failed to open {app_name}: {e}"

def execute(command_str):
    """
    Parses a command string from the AI and executes it.
    """
    if not command_str: return None
    
    # Handle [[ACTION:PARAM]] or [[ACTION]]
    command_str = command_str.replace("[[", "").replace("]]", "")
    parts = command_str.split(":", 1)
    action = parts[0].upper().strip()
    param = parts[1].strip() if len(parts) > 1 else ""

    if action == "OPEN":
        return open_website(param)
    elif action == "TIME":
        return get_system_time()
    elif action == "SCREENSHOT":
        return take_screenshot(param)
    elif action == "CALC" or action == "CALCULATOR":
        return run_system_command("calculator")
    elif action == "NOTEPAD":
        return run_system_command("notepad")
    elif action == "EXPLORER" or action == "FILES":
        return run_system_command("explorer")
    elif action == "VOL_UP":
        return control_media("VOL_UP")
    elif action == "VOL_DOWN":
        return control_media("VOL_DOWN")
    elif action == "PLAY":
        return control_media("PLAY_PAUSE")
    elif action == "YOUTUBE":
        return play_on_youtube(param)
    elif action == "SHORTS":
        webbrowser.open("https://www.youtube.com/shorts")
        return "Opening YouTube Shorts..."
    elif action == "NEWS":
        return fetch_india_news(param)
    
    return None

# Legacy/Direct match support (for app.py fallback)
def simple_match(msg):
    # High Priority: Check for direct bracketed commands from executeQuick
    bracket_match = re.search(r"\[\[(.*?)\]\]", msg)
    if bracket_match:
        return execute(bracket_match.group(1))

    msg = msg.lower()
    if "open google" in msg: return execute("OPEN:google")
    if "open youtube" in msg: return execute("OPEN:youtube")
    if "time" in msg: return execute("TIME")
    return None