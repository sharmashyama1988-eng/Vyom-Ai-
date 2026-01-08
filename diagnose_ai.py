import os
from dotenv import load_dotenv
from vyom.engines import deep_thought

# Load env vars
load_dotenv()

def test_ai():
    print("--- DIAGNOSTIC START ---")
    
    # 1. Check API Key
    key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    keys_str = os.getenv("GOOGLE_API_KEYS")
    
    if not key and not keys_str:
        print("❌ CRITICAL: GEMINI_API_KEY (or GOOGLE_API_KEY) is missing in .env")
        return

    if keys_str:
        print(f"✅ Found Multiple Keys: {len(keys_str.split(','))} keys detected.")
    else:
        print(f"✅ API Key found: {key[:5]}...{key[-5:]}")

    # 2. Initialize Engine
    print("   Initializing Deep Thought Engine...")
    try:
        engine = deep_thought.DeepThoughtEngine()
        print(f"✅ Engine initialized. Type: {engine.engine_type}")
        print(f"   Is Ready: {engine.is_ready}")
    except Exception as e:
        print(f"❌ Engine Init Failed: {e}")
        return

    # 3. Test Query
    print("\n   Sending Test Query: 'Hello, who are you?'")
    try:
        response, success = engine.solve("Hello, who are you?")
        if success:
            print(f"✅ Response Received:\n{response}")
        else:
            print(f"❌ AI Failed to Reply: {response}")
    except Exception as e:
        print(f"❌ Exception during query: {e}")

if __name__ == "__main__":
    test_ai()
