"""
VYOM ENGINE - Unified Growth & Training
========================================
- Handles Bulk Data Ingestion (FineWeb-Edu, Wikipedia)
- Automates Model Training & Vector DB Updates
- Optimized for High-Speed Hardware
"""
import os
import sys
# Ensure the root project directory is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import time
import threading
import sqlite3
import zlib
from queue import Queue
from datasets import load_dataset # type: ignore
from tqdm import tqdm # type: ignore
import torch # type: ignore

# Core Brain Import
from artificial_intelligence import train_system # type: ignore

# --- CONFIGURATION ---
DB_NAME = "prakriti.db"
TARGET_GB = 15
TARGET_BYTES = TARGET_GB * 1024 * 1024 * 1024
BATCH_SIZE = 500 # Optimized for 2.x env fix
SAVE_THREADS = 8

class VyomEngine:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        self.queue = Queue(maxsize=5000)
        self.running = True
        self.setup_db()

    def setup_db(self):
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA synchronous=OFF;")
        self.conn.execute("PRAGMA cache_size=2000000;") # 2GB
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT UNIQUE,
                content BLOB,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def compress(self, text):
        return zlib.compress(text.encode("utf-8"), level=1)

    def _save_worker(self):
        local_conn = sqlite3.connect(DB_NAME)
        local_conn.execute("PRAGMA journal_mode=WAL;")
        cursor = local_conn.cursor()
        while self.running or not self.queue.empty():
            items = []
            try:
                while len(items) < BATCH_SIZE:
                    items.append(self.queue.get(timeout=0.5))
            except: pass
            if items:
                for topic, content in items:
                    try:
                        cursor.execute("INSERT OR IGNORE INTO memory (topic, content) VALUES (?, ?)", 
                                     (topic, self.compress(content)))
                    except: pass
                local_conn.commit()
                for _ in range(len(items)): self.queue.task_done()
        local_conn.close()

    def feed_ai(self, limit_gb=2):
        print(f"\n🚀 Powering up AI with High-Quality Data (Limit: {limit_gb}GB Chunks)...")
        # Start workers
        for _ in range(SAVE_THREADS):
            threading.Thread(target=self._save_worker, daemon=True).start()

        datasets = [
            ("HuggingFaceFW/fineweb-edu", "sample-10BT", "text"),
            ("wikitext", "wikitext-103-v1", "text")
        ]

        start_size = int(os.path.getsize(DB_NAME)) if os.path.exists(DB_NAME) else 0
        limit_bytes = int(limit_gb) * 1024 * 1024 * 1024

        for ds_name, subset, col in datasets:
            if not self.running: break
            print(f"📡 Streaming {ds_name}...")
            try:
                print(f"   Connecting to {ds_name}...")
                # Remove specific config 'sample-10BT' if it causes connection hang, or keep if valid.
                # 'split="train"' sometimes causes issues in streaming if not explicitly defined in repo.
                if "fineweb" in ds_name:
                     ds = load_dataset(ds_name, name=subset, split="train", streaming=True, trust_remote_code=True)
                else:
                     ds = load_dataset(ds_name, name=subset, split="train", streaming=True)
                
                print(f"   Connection established. Starting stream...")
                with tqdm(unit=" art", desc=f"Ingesting {ds_name}") as pbar:
                    for i, row in enumerate(ds):
                        text = row.get(col, "").strip()
                        if len(text) < 500: continue
                        topic = text.split('\n')[0][:120].strip()
                        self.queue.put((topic, text))
                        
                        if i % 200 == 0:
                            # Using float uniformly to satisfy linter type inference
                            current_size: float = float(os.path.getsize(DB_NAME))
                            if (current_size - float(start_size)) >= float(limit_bytes):
                                print(f"\n✅ Chunk target ({limit_gb}GB) reached.")
                                break
                            pbar.set_postfix({"DB": f"{current_size/(1024*1024):.1f}MB"})



                        pbar.update(1)
            except Exception as e:
                print(f"⚠️ Error in {ds_name}: {e}")

        self.running = False
        self.queue.join()
        print("✅ Ingestion Phase Complete.")

    def update_brain(self):
        print("\n🧠 Updating AI Vector Memory (Chroma)...")
        try:
            train_system(force=True)
            print("✅ Brain Update Complete.")
        except Exception as e:
            print(f"❌ Training Error: {e}")

def main():
    engine = VyomEngine()
    
    # 1. Grow Knowledge
    engine.feed_ai(limit_gb=2) # 2GB per run as requested
    
    # 2. Train AI
    engine.update_brain()
    
    print("\n" + "="*40)
    print("✨ AI POWERED UP SUCCESSFULLY")
    print("="*40)

if __name__ == "__main__":
    main()
