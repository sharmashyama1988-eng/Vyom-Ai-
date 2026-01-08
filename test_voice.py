import sys
import os
import time

# Add project root to path
sys.path.append(os.getcwd())

try:
    from vyom import config
    print(f"Current Mode: {config.MODE}")

    print("Importing Voice Engine...")
    from vyom.engines import voice
    
    print("Initializing Voice System...")
    voice.initialize_voice_system()
    
    time.sleep(2) # Wait for thread
    
    if voice.is_ready():
        print(f"✅ Voice Engine is READY (Mode: {config.MODE}).")
        
        # Test speaking
        print("Testing speech...")
        voice.speak_text("System check complete.")
        time.sleep(2)
    else:
        print("❌ Voice Engine failed to initialize.")

except Exception as e:
    print(f"❌ Crash: {e}")