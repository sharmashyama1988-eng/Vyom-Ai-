"""
PRAKRITI BULK HARVESTER (20MB/s Target)
=======================================
- Engine: Raw MediaWiki API (Bulk Fetch)
- Throughput: 50 articles/request
- Concurrency: Multi-threaded producer-consumer
- Database: SQLite WAL (Supercharged)
"""
import warnings
warnings.filterwarnings("ignore")

import sqlite3
import random
import time
import os
import zlib
import threading
import requests # type: ignore
from queue import Queue
from concurrent.futures import ThreadPoolExecutor

# --- CONFIGURATION ---
DB_NAME = "prakriti.db"
TARGET_GB = 15
TARGET_BYTES = TARGET_GB * 1024 * 1024 * 1024
NUM_WORKERS = 30  # Increased for more parallelism
API_URL = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "PrakritiHarvester/3.0 (contact: prakriti@example.com) requests/2.0"}

# DB Setup (Thread-safe)
db_lock = threading.Lock()
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
conn.execute("PRAGMA journal_mode=WAL;")
conn.execute("PRAGMA synchronous=OFF;")
conn.execute("PRAGMA cache_size=500000;") # ~500MB cache
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS memory (id INTEGER PRIMARY KEY AUTOINCREMENT, topic TEXT UNIQUE, content BLOB)''')
conn.commit()

# Stats
stats = {"ok": 0, "bytes": 0, "errors": 0}
stats_lock = threading.Lock()

def compress(text):
    return zlib.compress(text.encode("utf-8"), 1) # Level 1 = Fastest

def fetch_bulk(titles):
    """Fetch content for 50 titles in ONE call"""
    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "explaintext": True,
        "titles": "|".join(titles)
    }
    try:
        response = requests.get(API_URL, params=params, headers=HEADERS, timeout=10)
        data = response.json()
        pages = data.get("query", {}).get("pages", {})
        
        results = []
        for p_id in pages:
            p_data = pages[p_id]
            title = p_data.get("title")
            content = p_data.get("extract")
            if title and content and len(content) > 500:
                results.append((title, content))
        return results
    except Exception:
        return []

def worker():
    """Consumes titles from queue and fetches bulk data"""
    while True:
        batch = []
        # Pull 20 titles from queue (Wikipedia prop=extracts limit)
        for _ in range(20):
            if not title_queue.empty():
                batch.append(title_queue.get())
        
        if not batch:
            time.sleep(0.5)
            continue
            
        # Fetch data in bulk
        items = fetch_bulk(batch)
        
        if items:
            with db_lock:
                for title, content in items:
                    blob = compress(content)
                    try:
                        cursor.execute("INSERT OR IGNORE INTO memory (topic, content) VALUES (?, ?)", (title, blob))
                    except:
                        pass
                # Commit every 100 articles to reduce IO overhead
                if stats["ok"] % 100 == 0:
                    conn.commit()
            
            with stats_lock:
                stats["ok"] += len(items)
                stats["bytes"] += sum(len(compress(c)) for _, c in items)
                # print(f"\n📦 Worker: Saved {len(items)} articles.") # Silent to reduce console lag
        else:
            with stats_lock:
                stats["errors"] += 1
            # Put back in queue or discard? For now discard to avoid loops
        
        # Mark tasks done
        for _ in range(len(batch)):
            title_queue.task_done()

title_queue = Queue(maxsize=1000)

def producer():
    """Systematically discovers topics via AllPages"""
    print("📡 Producer started: Systematic Discovery Mode...")
    letters = "abcdefghijklmnopqrstuvwxyz"
    while True:
        if title_queue.full():
            time.sleep(1)
            continue
            
        start_char = random.choice(letters) + random.choice(letters)
        params = {
            "action": "query",
            "format": "json",
            "list": "allpages",
            "apnamespace": 0,
            "aplimit": 50,
            "apfrom": start_char
        }
        try:
            resp = requests.get(API_URL, params=params, headers=HEADERS, timeout=5)
            if resp.status_code != 200:
                time.sleep(5)
                continue
            data = resp.json()
            titles = [p["title"] for p in data.get("query", {}).get("allpages", [])]
            random.shuffle(titles) # Mix things up
            for t in titles:
                title_queue.put(t)
        except Exception:
            time.sleep(2)

# Start Producer
threading.Thread(target=producer, daemon=True).start()

# Start Workers
for _ in range(NUM_WORKERS):
    threading.Thread(target=worker, daemon=True).start()

print(f"\n🚀 PRAKRITI BULK HARVESTER v3")
print(f"Workers: {NUM_WORKERS} | Target: {TARGET_GB} GB")
cursor.execute("SELECT COUNT(*) FROM memory")
print(f"Starting Base: {cursor.fetchone()[0]} topics\n")

start_time = time.time()
start_db_size = os.path.getsize(DB_NAME) if os.path.exists(DB_NAME) else 0
last_report = start_time
last_bytes = stats["bytes"] # type: ignore
last_db_size = start_db_size

try:
    while True:
        db_size = os.path.getsize(DB_NAME) if os.path.exists(DB_NAME) else 0
        
        if db_size >= TARGET_BYTES:
            print(f"\n✅ TARGET REACHED! Final Size: {db_size/(1024*1024):.1f} MB")
            break
            
        now = time.time()
        if (now - last_report) >= 3: # type: ignore
            # Speed calculations
            # DB Write Speed (Actual expansion on disk)
            db_delta = (db_size - last_db_size) / (1024 * 1024) # type: ignore
            write_speed = db_delta / (now - last_report) # type: ignore
            
            # Data Collection Speed (Compressed data in memory)
            data_delta = (stats["bytes"] - last_bytes) / (1024 * 1024) # type: ignore
            collect_speed = data_delta / (now - last_report) # type: ignore
            
            size_mb = db_size / (1024 * 1024)
            
            print(f"\r💾 {size_mb:.1f} MB | Speed: {write_speed:.2f} MB/s | " # type: ignore
                  f"✓{stats['ok']} Topics | ✗{stats['errors']} Errors | Queue: {title_queue.qsize()}", end="", flush=True) # type: ignore
            
            last_report = now
            last_bytes = stats["bytes"] # type: ignore
            last_db_size = db_size
            
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\n\n⏹ Stop requested. Saving and exiting...")

final_db_size = os.path.getsize(DB_NAME) if os.path.exists(DB_NAME) else 0
print(f"Final Count: {stats['ok']} new topics.")
print(f"Final Size: {final_db_size/(1024*1024):.1f} MB")
