import os

def setup():
    print("="*50)
    print("      VYOM AI - CLOUD BRAIN SETUP      ")
    print("="*50)
    print("\nTo give your AI super-intelligence without using RAM/CPU,")
    print("we need a FREE Google Gemini API Key.")
    print("\n⚠️  IMPORTANT: I cannot generate this key for you.")
    print("   You must get it yourself (it takes 30 seconds).")
    
    print("\n--- INSTRUCTIONS ---")
    print("1. Open this link: https://aistudio.google.com/app/apikey")
    print("2. Click 'Create API key'")
    print("3. Copy the key (it starts with 'AIza...')")
    
    key = input("\n👉 Paste your API Key here: ").strip()
    
    if not key:
        print("❌ No key provided. Exiting.")
        return
        
    if not key.startswith("AIza"):
        print("⚠️  Warning: That doesn't look like a valid Google API key.")
        confirm = input("Are you sure? (y/n): ")
        if confirm.lower() != 'y':
            return

    # Save to .env file
    with open(".env", "w") as f:
        f.write(f"GOOGLE_API_KEY={key}")
        
    print("\n✅ SUCCESS! API Key saved.")
    print("   Your AI is now powered by Google Gemini (Cloud).")
    print("   You can now run 'python app.py'")

if __name__ == "__main__":
    setup()
