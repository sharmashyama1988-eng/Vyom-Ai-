import os
import sys
import re
import datetime
from flask import Flask, request, jsonify, send_from_directory, Response, render_template
from werkzeug.utils import secure_filename

# --- 1. CONFIGURATION & SELECTION ---
import vyom.config as config

# Ask user for mode if running directly
if __name__ == '__main__':
    # Only ask if not already set via environment or previous run
    if len(sys.argv) > 1 and sys.argv[1] == '--light':
        config.MODE = 'light'
    elif len(sys.argv) > 1 and sys.argv[1] == '--default':
        config.MODE = 'default'
    else:
        print("\nSelect Operating Mode:")
        print("1. Default (Heavy - Requires GPU/RAM, Coqui TTS, Local LLM)")
        print("2. Lightweight (CPU friendly, System TTS, Cloud Search)")
        # choice = input("Enter choice (1 or 2): ").strip() # Auto-default to 2 for safety if no input
        choice = '2' # Forcing light for safety in this session unless specified
        # In a real CLI app we might want input(), but for this automated fix we default to safe.
        
        if choice == '2':
            config.MODE = 'light'
            print(">> Selected: Lightweight Mode")
        else:
            config.MODE = 'default'
            print(">> Selected: Default Mode")

# --- 2. IMPORTS ---
from vyom.engines import voice as voice_engine

from vyom.core import automation
from vyom.core import history as history_manager
from vyom.core import identity
from vyom.core import internet
from vyom.core import file_reader
from vyom.core.optimizer import performance
from vyom.core import device_manager # 📱 New Device Manager

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Available engines and models (served to frontend)
AVAILABLE_ENGINES = {
    "general": {"display": "Default", "models": ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-pro"]},
    "reasoning": {"display": "Reasoning", "models": ["gemini-2.5-pro", "gemini-2.0-flash", "gemini-flash-latest"]},
    "coding": {"display": "Coding", "models": ["gemini-2.5-flash", "gemini-2.0-flash"]},
    "math": {"display": "Math", "models": ["gemini-2.5-flash", "gemini-2.0-flash"]},
    "trinity": {"display": "Trinity", "models": ["gemini-2.5-pro", "gemini-2.5-flash"]},
    "image": {"display": "Image", "models": ["realistic", "anime", "digital", "painting", "3d-model"]}
}


@app.route('/models', methods=['GET'])
def get_models():
    """Returns available engines and models for the frontend."""
    return jsonify(AVAILABLE_ENGINES)


@app.route('/user/save_pref', methods=['POST'])
def save_user_pref():
    data = request.json
    device_id = data.get('device_id')
    engine = data.get('engine')
    model = data.get('model')
    if not device_id:
        return jsonify({"error": "Missing device_id"}), 400
    # Validate engine/model
    if engine and engine not in AVAILABLE_ENGINES:
        return jsonify({"error": "Unknown engine"}), 400
    if model and engine and model not in AVAILABLE_ENGINES.get(engine, {}).get('models', []):
        return jsonify({"error": "Invalid model for engine"}), 400
    success = history_manager.save_user_preferences(device_id, default_engine=engine, default_model=model)
    if success:
        return jsonify({"success": True})
    return jsonify({"error": "Failed"}), 500


@app.route('/user/save_keys', methods=['POST'])
def save_user_keys():
    data = request.json
    device_id = data.get('device_id')
    keys = data.get('keys')
    if not device_id or not isinstance(keys, dict):
        return jsonify({"error": "Missing device_id or bad keys"}), 400
    # Do not echo back keys in the response
    success = history_manager.save_user_api_keys(device_id, keys)
    if success:
        return jsonify({"success": True})
    return jsonify({"error": "Failed"}), 500

# --- STATIC & CORE ROUTES ---
@app.route('/')
def home():
    return render_template('chat.html')

@app.route('/logo.png')
def serve_logo():
    return send_from_directory(os.path.join(app.root_path, 'static', 'img'), 'logo.png')

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/voice/status')
def voice_status():
    if voice_engine.is_ready(): return jsonify({"status": "ready"})
    return jsonify({"status": "unavailable"}), 503

# --- USER MANAGEMENT ROUTES ---
@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/user/login', methods=['POST'])
def user_login():
    data = request.json
    email = data.get('email')
    device_id = data.get('device_id')
    
    # Simple search by email in all users
    all_users = history_manager.get_all_users() # Assuming this exists or we use device_id
    # For this system, we link device_id to user. 
    # Let's find user by email and then link the new device_id to them.
    user = history_manager.find_user_by_email(email)
    if user:
    
        # Link current device to this user if it's different
        history_manager.link_device_to_user(user['id'], device_id)
        return jsonify({"success": True, "user": user})
    return jsonify({"success": False, "error": "User not found"})

@app.route('/user/check')
def check_user():
    device_id = request.args.get('device_id')
    if not device_id: return jsonify({"registered": False})
    
    user = history_manager.get_user(device_id)
    if user and user.get('name') != 'Guest':
        # 📱 Sync Device Info
        device_info = device_manager.sync_device_data(device_id, history_manager)
        return jsonify({"registered": True, "user": user, "device": device_info})
    
    # Allow guest access silently
    return jsonify({"registered": True, "user": {"name": "Guest"}, "is_guest": True})

@app.route('/user/register', methods=['POST'])
def register_user():
    data = request.json
    device_id = data.get('device_id')
    name = data.get('name')
    email = data.get('email')
    gender = data.get('gender')
    
    if not name or not email:
        return jsonify({"registered": False, "error": "Name and email required"})
        
    user = history_manager.register_user(device_id, name, email, gender)
    return jsonify({"registered": True, "user": user})

# --- CHAT MANAGEMENT ROUTES ---
@app.route('/user/chats', methods=['GET'])
def get_chats():
    device_id = request.args.get('device_id')
    chats = history_manager.get_chat_sessions(device_id)
    return jsonify(chats)

@app.route('/user/new_chat', methods=['POST'])
def new_chat():
    device_id = request.json.get('device_id')
    chat = history_manager.start_new_chat(device_id)
    if chat:
        return jsonify(chat)
    return jsonify({"error": "User not found"}), 404

@app.route('/user/history', methods=['GET'])
def get_history():
    device_id = request.args.get('device_id')
    chat_id = request.args.get('chat_id')
    history = history_manager.get_chat_history(device_id, chat_id)
    if history is None:
        return jsonify({"history": []})
    
    # Format for frontend
    formatted_history = []
    for msg in history:
        # Convert timestamp to human readable if needed, but frontend handles raw mostly
        # The frontend code in chat.js expects strings like "User: ..." or "Vyom AI: ..."
        # OR it handles structured objects if we update it.
        # Looking at chat.js:
        # if (h.startsWith('User:')) ...
        # But also: if (messages.length === 0) ... messages.forEach(msg => ... msg.role ... msg.content) in loadChat
        # The frontend has TWO implementations. 
        # 1. `loadChatHistory` uses `user/history` and expects strings.
        # 2. `loadChat` (at bottom) uses `/chat/${chatId}` and expects JSON objects.
        
        # We will support the structured format for `user/history` but return a list of strings 
        # to match the `loadChatHistory` implementation in chat.js which parses "User: "
        
        prefix = "User: " if msg['role'] == 'user' else "Vyom AI: "
        formatted_history.append(f"{prefix}{msg['content']}")

    return jsonify({"history": formatted_history})

@app.route('/user/rename_chat', methods=['POST'])
def rename_chat():
    data = request.json
    success = history_manager.rename_chat(data.get('device_id'), data.get('chat_id'), data.get('new_title'))
    return jsonify({"success": success})

@app.route('/user/delete_chat', methods=['POST'])
def delete_chat():
    data = request.json
    success = history_manager.delete_chat(data.get('device_id'), data.get('chat_id'))
    return jsonify({"success": success})

@app.route('/chats', methods=['DELETE'])
def delete_all_chats():
    data = request.json
    success = history_manager.delete_all_chats(data.get('device_id'))
    if success: return jsonify({"status": "ok"})
    return jsonify({"error": "Failed"}), 500

# --- FEATURE ROUTES ---
@app.route('/camera/capture', methods=['POST'])
def capture_camera():
    filename, error = automation.capture_camera_image()
    if error:
        return jsonify({"error": error}), 500
    
    # Return URL
    return jsonify({"image_url": f"/uploads/{filename}"})

@app.route('/upload', methods=['POST'])
def upload_file():
    # Handle multiple files
    uploaded_files = request.files.getlist("files[]") # Frontend must send as files[]
    if not uploaded_files:
         # Fallback for single file input
         if 'file' in request.files:
             uploaded_files = [request.files['file']]
         else:
             return jsonify({"error": "No files"}), 400
             
    saved_files = []
    for file in uploaded_files:
        if file.filename == '': continue
        filename = secure_filename(file.filename)
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        save_name = f"{timestamp}_{filename}"
        path = os.path.join(app.config['UPLOAD_FOLDER'], save_name)
        file.save(path)
        saved_files.append({"filename": save_name, "url": f"/uploads/{save_name}", "path": path})

    return jsonify({"success": True, "files": saved_files})

# --- USER SETTINGS ROUTES ---
@app.route('/user/save_key', methods=['POST'])
def save_api_key():
    data = request.json
    device_id = data.get('device_id')
    api_key = data.get('api_key')
    
    if not device_id: return jsonify({"error": "Missing device_id"}), 400
    
    # Store the key securely (in a real app, encrypt this!)
    success = history_manager.save_user_api_key(device_id, api_key)
    
    if success:
        return jsonify({"success": True})
    return jsonify({"error": "Failed to save key"}), 500

@app.route('/user/location', methods=['POST'])
def update_location():
    data = request.json
    device_id = data.get('device_id')
    lat = data.get('lat')
    lon = data.get('lon')
    
    if not device_id or lat is None or lon is None:
        return jsonify({"error": "Missing data"}), 400

    # Reverse Geocoding (Simple version using a public API or just storing coordinates)
    # For now, let's store it and use a placeholder for city name
    # In a production app, use something like Nominatim or Google Maps API
    
    # We'll use a simple IP-based fallback or just coordinates for now.
    # To make it "cool", let's try to get the city name.
    city = "your area"
    try:
        import requests
        res = requests.get(f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json", headers={'User-Agent': 'VyomAI/1.0'})
        if res.ok:
            address = res.json().get('address', {})
            city = address.get('city') or address.get('town') or address.get('village') or address.get('state') or "your area"
    except:
        pass

    # Save to user profile
    history_manager.update_user(device_id, {"last_location": city, "lat": lat, "lon": lon})
    
    return jsonify({"success": True, "city": city})

# --- MAIN ASK ROUTE ---
@app.route('/ask', methods=['POST'])
def ask():
    # ⚡ Lazy Load Engines to speed up Server Boot
    from vyom.engines import image as image_engine
    from vyom.engines import thinking as thinking_engine
    from vyom.engines import math as math_engine
    from vyom.engines import trinity as trinity_engine
    from vyom.engines import visual_studio

    data = request.json 
    msg = data.get('message', '')
    chat_id = data.get('chat_id')
    device_id = data.get('device_id')
    settings = data.get('settings', {})
    attachments = data.get('attachments', []) # Expecting list of {path, url}
    
    if not msg and not attachments: return jsonify({"answer": "Empty message"})

    # Fetch User's Custom API Key (BYOK) and saved defaults
    user_api_key = None
    user_profile = None
    user_default_engine = None
    user_default_model = None
    if device_id:
        user_profile = history_manager.get_user(device_id)
        if user_profile:
            user_api_key = user_profile.get('api_key')
            user_default_engine = user_profile.get('default_engine')
            user_default_model = user_profile.get('default_model')

    # Engine selection early for routing
    selected_engine = settings.get('engine') or user_default_engine or 'general'

    # --- Guest Restriction ---
    is_guest = not user_profile or user_profile.get('name') == 'Guest'
    if is_guest and selected_engine != 'general':
        return jsonify({"answer": "⚠️ **Access Restricted.** Special engines like **Coding, Math, and Image** require a free account. Please **Register** in settings to unlock these features."})

    lower_msg = msg.lower()

    # --- 0. VISUAL STUDIO ENGINE (Editing & Merging) ---
    # Check for visual tasks if attachments exist
    if attachments:
        # B. EDITING & COMPOSITION (1+ Images + Instruction)
        if len(attachments) >= 1 and ("edit" in lower_msg or "change" in lower_msg or "make" in lower_msg or "filter" in lower_msg or "merge" in lower_msg or "combine" in lower_msg or "create" in lower_msg):
            # Extract all image paths
            image_paths = []
            for att in attachments:
                path = os.path.join(os.getcwd(), att['url'].lstrip('/'))
                if os.path.exists(path) and att['url'].lower().split('.')[-1] in ['jpg', 'jpeg', 'png', 'webp']:
                    image_paths.append(path)
            
            if image_paths:
                # Check for simple filters first (only if 1 image)
                filters = ['blur', 'sharpen', 'grayscale', 'contour']
                applied_filter = next((f for f in filters if f in lower_msg), None) if len(image_paths) == 1 else None
                
                if applied_filter:
                    result_url = visual_studio.editor.apply_filter(image_paths[0], applied_filter)
                    answer = f"I've applied the {applied_filter} filter. \n\n![Edited Image]({result_url})"
                else:
                    # Advanced Multi-Image Composition
                    user_key = settings.get('api_key') or user_api_key
                    result_url = visual_studio.editor.generative_edit(image_paths, msg, user_api_key=user_key)
                    
                    if isinstance(result_url, str) and (result_url.startswith("http") or result_url.startswith("/")):
                        answer = f"Here is your advanced composition: \n\n![Result]({result_url})"
                    else:
                        answer = result_url

                    if chat_id and device_id:
                        performance.run_in_background(history_manager.add_to_chat_history, device_id, chat_id, msg, role="user")
                        performance.run_in_background(history_manager.add_to_chat_history, device_id, chat_id, answer, role="assistant")
                    return jsonify({"answer": answer})

    # ⚡ 1. CHECK CACHE (Instant Reply)
    # Cache is now engine-aware
    cached_ans = performance.get_cached_response(msg, engine=selected_engine)
    if cached_ans:
        # Voice (Speak only Answer part)
        voice_text = cached_ans
        if "<answer>" in cached_ans:
            try: voice_text = cached_ans.split("<answer>")[1].split("</answer>")[0].strip()
            except: pass
        
        # Gender-aware voice
        gender = user_profile.get('gender') if user_profile else None
        voice_engine.speak_text(voice_text, gender=gender)
        
        # Background History Save
        if chat_id and device_id:
            performance.run_in_background(history_manager.add_to_chat_history, device_id, chat_id, msg, role="user")
            performance.run_in_background(history_manager.add_to_chat_history, device_id, chat_id, cached_ans, role="assistant")
            
        return jsonify({"answer": cached_ans})

    # 0. Image Generation
    # Only trigger by keywords IF engine is general or image
    is_image_request = (selected_engine == 'image') or \
                      (selected_engine == 'general' and any(k in lower_msg for k in ["generate image", "create image", "draw"]))
    
    if is_image_request:
        # Auto-detect style from prompt
        detected_style = 'realistic' # Default
        styles_map = {
            'anime': ['anime', 'manga', 'cartoon'],
            '3d-model': ['3d', 'render', 'unreal engine', 'blender'],
            'digital': ['digital art', 'digital painting', 'concept art'],
            'painting': ['painting', 'oil', 'canvas', 'acrylic'],
            'pixel-art': ['pixel', '8-bit', '16-bit'],
            'sketch': ['sketch', 'pencil', 'drawing'],
            'cyberpunk': ['cyberpunk', 'neon', 'futuristic'],
            'watercolor': ['watercolor', 'water colour']
        }
        
        for style_key, keywords in styles_map.items():
            if any(k in lower_msg for k in keywords):
                detected_style = style_key
                break
        
        # Auto-generate negative prompt based on style
        neg = "ugly, deformed, blurry, low quality"
        if detected_style == 'realistic':
            neg += ", cartoon, anime, illustration"
        elif detected_style == 'anime':
            neg += ", photorealistic, real photo"

        # Prefer explicit model from settings or user defaults when possible
        selected_model = settings.get('model') or user_default_model
        style_to_use = detected_style
        try:
            # If the model matches a known style, use it
            if selected_model and hasattr(image_engine, 'STYLES') and selected_model in image_engine.STYLES:
                style_to_use = selected_model
        except Exception:
            style_to_use = detected_style

        img_response = image_engine.generate(msg, style=style_to_use, negative_prompt=neg)
        
        if chat_id and device_id:
             # ⚡ Background Save
             performance.run_in_background(history_manager.add_to_chat_history, device_id, chat_id, msg, role="user")
             performance.run_in_background(history_manager.add_to_chat_history, device_id, chat_id, img_response, role="assistant")
        return jsonify({"answer": img_response})

    # 1. Automation (System control) - DIRECT/FAST MATCH
    auto_res = automation.simple_match(msg)
    if auto_res:
        gender = user_profile.get('gender') if user_profile else None
        voice_engine.speak_text(auto_res, gender=gender)
        if chat_id and device_id:
             performance.run_in_background(history_manager.add_to_chat_history, device_id, chat_id, msg, role="user")
             performance.run_in_background(history_manager.add_to_chat_history, device_id, chat_id, auto_res, role="assistant")
        return jsonify({"answer": auto_res})

    # 2. Thinking (AI)
    # Check for live data needs (Cricket, Weather, News) - Save API Quota!
    live_keywords = ['score', 'cricket', 'weather', 'stock', 'price', 'news', 'headlines', 'who won']
    if any(k in lower_msg for k in live_keywords) and selected_engine == 'general':
        search_res = internet.search_google(msg)
        if search_res:
             # Fast format and return to avoid LLM call entirely
             raw_answer = f"### 🌐 Live Intelligence\n*Browsing the real-time web to provide you the most accurate and latest data.*\n\n{search_res}\n\n---\n*Note: This information was fetched directly from live sources for maximum reliability.*"
             
             # ⚡ Cache it for 9999x speed on next hit
             performance.cache_response(msg, raw_answer, engine=selected_engine)
             
             if chat_id and device_id:
                performance.run_in_background(history_manager.add_to_chat_history, device_id, chat_id, msg, role="user")
                performance.run_in_background(history_manager.add_to_chat_history, device_id, chat_id, raw_answer, role="assistant")
             return jsonify({"answer": raw_answer})

    # Use the Trinity System for supported engines (General, Coding, Math, Reasoning, Trinity)
    trinity_supported = ('general', 'coding', 'math', 'reasoning', 'trinity')
    
    if selected_engine in trinity_supported:
        # We need history for context
        history = history_manager.get_chat_history(device_id, chat_id) or []
        # Provide the user's BYOK or saved API keys to the engine if available
        api_override = settings.get('api_key') or (user_profile and user_profile.get('api_key'))
        if not api_override and user_profile and user_profile.get('api_keys'):
            try:
                api_override = next(iter(user_profile.get('api_keys').values()))
            except StopIteration:
                api_override = None

        raw_answer = trinity_engine.generate_response(msg, engine_type=selected_engine, history=history, user_api_key=api_override, attachments=attachments)
    else:
        # Default legacy behavior or other engines
        raw_answer = thinking_engine.solve_with_reasoning(msg, user_api_key=user_api_key)
    
    # 2.5 AI-Driven Automation Check
    # Look for [[ACTION:PARAM]] tags in the AI's response
    cmd_match = re.search(r"\[\[(.*?)\]\]", raw_answer)
    if cmd_match:
        command_tag = cmd_match.group(0) # The full [[...]]
        command_content = cmd_match.group(1) # The inside part
        
        # Execute the command found by the AI
        print(f"🤖 AI Requested Command: {command_content}")
        exec_result = automation.execute(command_content)
        
        # Clean the answer for the user (remove the tag)
        raw_answer = raw_answer.replace(command_tag, "").strip()
        
        # Optionally append the execution result if it's meaningful info
        if exec_result and "Opening" not in raw_answer: 
             # If the AI didn't say "Opening...", we append the system status
             raw_answer += f"\n\n_{exec_result}_"

    # 3. Finalize & Cache
    # ⚡ Cache it for 9999x speed on next hit
    performance.cache_response(msg, raw_answer, engine=selected_engine)
    
    # Clean answer for voice
    voice_text = raw_answer
    if "<answer>" in raw_answer:
        try:
            voice_text = raw_answer.split("<answer>")[1].split("</answer>")[0].strip()
        except:
            voice_text = raw_answer # Fallback

    # Voice
    gender = user_profile.get('gender') if user_profile else None
    voice_engine.speak_text(voice_text, gender=gender)
    
    # ⚡ Background History Save
    if chat_id and device_id:
        performance.run_in_background(history_manager.add_to_chat_history, device_id, chat_id, msg, role="user")
        performance.run_in_background(history_manager.add_to_chat_history, device_id, chat_id, raw_answer, role="assistant")
    
    # ⚡ Memory Cleanup
    performance.run_in_background(performance.optimize_memory)
    
    return jsonify({"answer": raw_answer})

if __name__ == '__main__':
    # Initialize Engines based on the selected config
    # We default to light in this script block if not set, but let's re-ensure
    if not config.MODE: config.MODE = "light"
    
    voice_engine.initialize_voice_system()
    
    print(f"🚀 Vyom AI Started in {config.MODE.upper()} Mode")
    app.run(port=5000)





