"""
PRAKRITI BULK INGESTOR - High Speed (20MB/s Target)
===================================================
- Strategy: Stream high-quality datasets (Wikipedia/FineWeb-Edu) directly.
- Optimization: Batch commits + zlib compression + multi-threaded ingestion.
"""
import sqlite3
import zlib
import os
import time
from datasets import load_dataset # type: ignore
from tqdm import tqdm # type: ignore

DB_NAME = "prakriti.db"
TARGET_GB = 15
TARGET_BYTES = TARGET_GB * 1024 * 1024 * 1024

class PrakritiIngestor:
    def __init__(self, db_name=DB_NAME):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name, check_same_thread=False)
        self.setup_db()
        self.stats = {"count": 0, "bytes": 0}

    def setup_db(self):
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA synchronous=OFF;")
        self.conn.execute("PRAGMA cache_size=1000000;")
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

    def run(self):
        print(f"🚀 Initializing High-Speed Stream: Wikitext (Educational)...")
        # Load Wikitext (Stable Wikipedia-based educational corpus)
        ds = load_dataset("wikitext", "wikitext-103-v1", split="train", streaming=True, trust_remote_code=True) # type: ignore
        
        batch = []
        batch_size = 50
        start_time = time.time()
        
        # Determine current DB size
        initial_size = os.path.getsize(self.db_name) if os.path.exists(self.db_name) else 0
        
        print(f"💾 Current DB Size: {initial_size/(1024*1024):.1f} MB")
        print(f"🎯 Goal: {TARGET_GB} GB")
        
        with tqdm(unit=" articles", desc="Ingesting") as pbar:
            for i, row in enumerate(ds):
                # Wikitext uses 'text' field. We can use the first line or a chunk for 'topic'
                content = row['text'].strip()
                if not content or len(content) < 200: continue
                
                # Simple topic extraction (First sentence or header)
                topic = content.split('\n')[0][:100] if '\n' in content else content[:50]
                
                batch.append((topic, content))
                
                if len(batch) >= batch_size:
                    self._save_batch(batch)
                    pbar.update(len(batch))
                    batch = []
                    
                    # Performance check
                    db_size = os.path.getsize(self.db_name)
                    if db_size >= TARGET_BYTES:
                        print(f"\n✅ SUCCESS! Reached {TARGET_GB}GB target.")
                        break
                    
                    # Update Speedometer
                    elapsed = time.time() - start_time
                    mb_total = db_size / (1024 * 1024)
                    speed = (db_size - initial_size) / (1024 * 1024) / elapsed if elapsed > 0 else 0 # type: ignore
                    pbar.set_postfix({"Size": f"{mb_total:.1f}MB", "Speed": f"{speed:.2f}MB/s"})

    def _save_batch(self, items):
        cursor = self.conn.cursor()
        for topic, content in items:
            blob = self.compress(content)
            try:
                cursor.execute("INSERT OR IGNORE INTO memory (topic, content) VALUES (?, ?)", (topic, blob))
            except:
                pass
        self.conn.commit()

if __name__ == "__main__":
    try:
        ingestor = PrakritiIngestor()
        ingestor.run()
    except KeyboardInterrupt:
        print("\n⏹ Ingestion paused by user.")
