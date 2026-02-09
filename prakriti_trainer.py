"""
BALANCED COLLECTOR - Fast but не Rate Limited
==============================================
"""
import warnings
warnings.filterwarnings("ignore")

import sqlite3
import random
import time
import os
import zlib
import threading
from concurrent.futures import ThreadPoolExecutor

try:
    import wikipedia # type: ignore
    wikipedia.set_rate_limiting(True)  # Respect limits
except:
    os.system("pip install -q wikipedia")
    import wikipedia # type: ignore
    wikipedia.set_rate_limiting(True)

# Config
DB_NAME = "prakriti.db"
TARGET_GB = 15
TARGET_BYTES = TARGET_GB * 1024 * 1024 * 1024
NUM_WORKERS = 8  # Reduced to avoid blocking

# DB
db_lock = threading.Lock()
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
conn.execute("PRAGMA journal_mode=WAL;")
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS memory (id INTEGER PRIMARY KEY AUTOINCREMENT, topic TEXT UNIQUE, content BLOB)''')
conn.commit()

SEEDS = [
    "Science", "Technology", "History", "Art", "Music", "Geography", "Mathematics", 
    "Physics", "Chemistry", "Biology", "Medicine", "Philosophy", "Literature", 
    "Engineering", "Astronomy", "Economics", "Countries", "Cities", "Animals", "Plants",
    "Wars", "Inventions", "Scientists", "Artists", "Musicians", "Athletes", "Politicians",
    "Movies", "Books", "Games", "Sports", "Languages", "Religions", "Cultures",
    "Mountains", "Rivers", "Oceans", "Deserts", "Forests", "Islands", "Planets",
    "Elements", "Chemicals", "Diseases", "Treatments", "Psychology", "Sociology",
    "Anthropology", "Archaeology", "Geology", "Meteorology", "Ecology", "Genetics"
]

def compress(text):
    return zlib.compress(text.encode("utf-8"), 3)  # Balanced

stats = {"ok": 0, "skip": 0, "err": 0}
stats_lock = threading.Lock()

def worker(topic):
    try:
        page = wikipedia.page(topic, auto_suggest=False)
        if len(page.content) < 300:
            return None
        
        blob = compress(page.content)
        
        with db_lock:
            cursor.execute("INSERT OR IGNORE INTO memory (topic, content) VALUES (?, ?)", (topic, blob))
            conn.commit()
            with stats_lock:
                stats["ok"] += 1
            return len(blob)
    except wikipedia.exceptions.DisambiguationError:
        with stats_lock:
            stats["skip"] += 1
        return None
    except:
        with stats_lock:
            stats["err"] += 1
        return None

print(f"\n🚀 BALANCED COLLECTOR")
print(f"Workers: {NUM_WORKERS} | Target: {TARGET_GB} GB")
cursor.execute("SELECT COUNT(*) FROM memory")
print(f"Starting: {cursor.fetchone()[0]} topics\n")

start = time.time()
start_size = os.path.getsize(DB_NAME) if os.path.exists(DB_NAME) else 0
last_report = start
last_size = start_size

def get_topics():
    """Generate topics avoiding duplicates"""
    checked = set()
    while True:
        seed = random.choice(SEEDS)
        try:
            results = wikipedia.search(seed, results=20)
            for t in results:
                if t not in checked:
                    checked.add(t)
                    # Quick DB check
                    with db_lock:
                        cursor.execute("SELECT 1 FROM memory WHERE topic=? LIMIT 1", (t,))
                        if not cursor.fetchone():
                            yield t
        except:
            pass
        
        # Random pages
        try:
            r = wikipedia.random(1)
            if r not in checked:
                checked.add(r)
                with db_lock:
                    cursor.execute("SELECT 1 FROM memory WHERE topic=? LIMIT 1", (r,))
                    if not cursor.fetchone():
                        yield r
        except:
            pass

topic_gen = get_topics()

with ThreadPoolExecutor(max_workers=NUM_WORKERS) as exe:
    futures = set()
    
    while True:
        size = os.path.getsize(DB_NAME) if os.path.exists(DB_NAME) else 0
        
        if size >= TARGET_BYTES:
            print(f"\n✅ REACHED {size/(1024*1024):.1f} MB!")
            break
        
        # Keep workers busy
        while len(futures) < NUM_WORKERS * 3:
            try:
                topic = next(topic_gen)
                future = exe.submit(worker, topic) # type: ignore
                futures.add(future)
            except:
                break
        
        # Clean done
        futures = {f for f in futures if not f.done()}
        
        # Report
        now = time.time() # type: ignore
        if now - last_report >= 3: # type: ignore
            mb = size / (1024 * 1024) # type: ignore
            added = (size - last_size) / (1024 * 1024) # type: ignore
            speed = added / 3 # type: ignore
            
            print(f"💾 {mb:.1f} MB | +{speed:.2f} MB/s | "
                  f"✓{stats['ok']} ⊗{stats['skip']} ✗{stats['err']}", flush=True) # type: ignore
            
            last_report = now
            last_size = size
        
        time.sleep(0.1)

total = time.time() - start # type: ignore
added = (size - start_size) / (1024 * 1024) # type: ignore
print(f"\n✅ Done! +{added:.1f} MB in {total/60:.1f} min")
print(f"Avg: {added/total:.2f} MB/s | Topics: {stats['ok']}")
