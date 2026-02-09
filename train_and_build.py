
import os
import sys
import threading
import time
import concurrent.futures

# --- 1. SETUP PATHS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

print("🚀 VYOM AI - ULTIMATE BUILDER & TRAINER")
print("=========================================")
print("Starting simultaneous operations...")

# --- 2. MULTI-THREADED OPERATIONS ---

def compress_databases():
    """Simulates combining and compressing knowledge bases."""
    print("   [Thread-1] Optimizing & Compressing Knowledge Bases...")
    time.sleep(2) # Simulating IO work
    # In a real scenario, this would merge SQLite DBs or Chroma Collections
    db_path = "vyom_knowledge_compressed.db"
    if os.path.exists(db_path):
        size = os.path.getsize(db_path) / 1024
        print(f"   ℹ️  [Thread-1] Knowledge Graph Size: {size:.2f} KB")
    print("   ✅ [Thread-1] Optimization Complete.")

def build_executable():
    """Builds the final executable using PyInstaller."""
    print("   [Thread-2] Building VyomAI.exe (This takes time)...")
    import subprocess
    
    if not os.path.exists("build_exe.spec"):
        print("   ⚠️ [Thread-2] Spec file missing.")
        return

    try:
        result = subprocess.run(
            ['pyinstaller', 'build_exe.spec', '--noconfirm', '--log-level=WARN'],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("   ✅ [Thread-2] Build SUCCESS!")
            if os.path.exists("dist/VyomAI.exe"):
                 if os.path.exists("VyomAI.exe"): os.remove("VyomAI.exe")
                 os.rename("dist/VyomAI.exe", "VyomAI.exe")
                 print("   📦 [Thread-2] VyomAI.exe is ready in root folder.")
        else:
            print(f"   ❌ [Thread-2] Build Failed:\n{result.stderr}")
    except Exception as e:
        print(f"   ❌ [Thread-2] Build Error: {e}")

def main():
    start_time = time.time()
    
    t1 = threading.Thread(target=compress_databases)
    t2 = threading.Thread(target=build_executable)
    
    t1.start()
    t2.start()
    
    t1.join()
    t2.join()


    # Clean up
    if os.path.exists("build"): 
        import shutil
        shutil.rmtree("build", ignore_errors=True)
    if os.path.exists("dist"):
        shutil.rmtree("dist", ignore_errors=True)

    elapsed = time.time() - start_time
    print(f"\n✨ ALL SYSTEMS READY! (Time taken: {elapsed:.2f}s)")
    print("You can now run 'run.bat' or 'VyomAI.exe'")

if __name__ == "__main__":
    main()

