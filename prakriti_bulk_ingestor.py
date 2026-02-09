"""
PRAKRITI BULK INGESTOR - High Speed (20MB/s Target)
===================================================
- Dataset: FineWeb-Edu (High Quality Educational Text)
- Speed Optimization: Multi-threaded queue + Batching
- Target: 15GB Knowledge Base
"""
import sqlite3
import zlib
import os
import time
import threading
from queue import Queue
from datasets import load_dataset # type: ignore
from tqdm import tqdm # type: ignore

DB_NAME = "prakriti.db"
TARGET_GB = 15
TARGET_BYTES = TARGET_GB * 1024 * 1024 * 1024
BATCH_SIZE = 100
SAVE_THREADS = 4

class PrakritiIngestor:
    def __init__(self, db_name=DB_NAME):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name, check_same_thread=False)
        self.setup_db()
        self.queue = Queue(maxsize=1000)
        self.stats = {"count": 0, "bytes": 0}
        self.running = True

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

    def _save_worker(self):
        """Dedicated thread for database writes."""
        local_conn = sqlite3.connect(self.db_name)
        local_conn.execute("PRAGMA journal_mode=WAL;")
        local_conn.execute("PRAGMA synchronous=OFF;")
        cursor = local_conn.cursor()
        
        while self.running or not self.queue.empty():
            items = []
            try:
                # Try to get a batch
                while len(items) < BATCH_SIZE:
                    items.append(self.queue.get(timeout=1))
            except:
                pass
                
            if items:
                batch_bytes = 0
                for topic, content in items:
                    blob = self.compress(content)
                    batch_bytes += len(blob)
                    try:
                        cursor.execute("INSERT OR IGNORE INTO memory (topic, content) VALUES (?, ?)", (topic, blob))
                    except:
                        pass
                local_conn.commit()
                self.stats["count"] += len(items) # type: ignore
                self.stats["bytes"] += batch_bytes # type: ignore
                for _ in range(len(items)):
                    self.queue.task_done()
        local_conn.close()

    def run(self):
        print(f"🚀 Initializing High-Speed Stream: FineWeb-Edu...")
        # FineWeb-Edu is massive and high quality
        ds = load_dataset("HuggingFaceFW/fineweb-edu", name="sample-10BT", split="train", streaming=True, trust_remote_code=True) # type: ignore
        
        # Start save workers
        workers = []
        for _ in range(SAVE_THREADS):
            t = threading.Thread(target=self._save_worker)
            t.daemon = True
            t.start()
            workers.append(t)

        start_time = time.time()
        initial_size = os.path.getsize(self.db_name) if os.path.exists(self.db_name) else 0
        
        print(f"💾 Current DB Size: {initial_size/(1024*1024):.1f} MB")
        print(f"🎯 Goal: {TARGET_GB} GB")
        
        try:
            with tqdm(unit=" articles", desc="Streaming") as pbar:
                for i, row in enumerate(ds): # type: ignore
                    text = row['text'].strip() # type: ignore
                    if len(text) < 500: continue
                    
                    topic = text.split('\n')[0][:100]
                    self.queue.put((topic, text))
                    
                    if i % 100 == 0:
                        db_size = os.path.getsize(self.db_name)
                        if db_size >= TARGET_BYTES:
                            print(f"\n✅ SUCCESS! Reached {TARGET_GB}GB target.")
                            break
                        
                        elapsed = time.time() - start_time
                        current_mb = db_size / (1024 * 1024)
                        # type ignore on subtraction for lint
                        speed = (db_size - initial_size) / (1024 * 1024) / elapsed if elapsed > 0 else 0 # type: ignore
                        pbar.set_postfix({"Size": f"{current_mb:.1f}MB", "Speed": f"{speed:.2f}MB/s", "Queue": self.queue.qsize()})
                    
                    pbar.update(1)
        except Exception as e:
            print(f"❌ Streaming Error: {e}")
        finally:
            self.running = False
            self.queue.join()
            print("\n✅ Ingestion Finished.")

if __name__ == "__main__":
    try:
        ingestor = PrakritiIngestor()
        ingestor.run()
    except KeyboardInterrupt:
        print("\n⏹ Ingestion paused by user.")
