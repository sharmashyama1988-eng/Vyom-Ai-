"""
PRAKRITI SPEED COLLECTOR V2 (Clean & Fast)
==========================================
- Warnings Suppressed
- Real Progress Tracking
- Efficient Batch Collection
"""
import warnings
warnings.filterwarnings("ignore")  # Suppress all warnings

import time
import sqlite3
import random
import zlib
import os
from datetime import datetime

# Try imports
try:
    import wikipedia # type: ignore
    wikipedia.set_lang("en")
except:
    os.system("pip install -q wikipedia")
    import wikipedia # type: ignore
    wikipedia.set_lang("en")

try:
    from google import generativeai as genai # type: ignore
except:
    os.system("pip install -q google-generativeai")
    from google import generativeai as genai # type: ignore

# --- CONFIGURATION ---
GOOGLE_API_KEY = "AIzaSyCnDW2sd_Lvb92w4JEXu1WxiD79N0g_Y64"
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')

DB_NAME = "prakriti.db"
TARGET_GB = 15
TARGET_BYTES = TARGET_GB * 1024 * 1024 * 1024

# Setup DB
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
conn.execute("PRAGMA journal_mode=WAL;")
conn.execute("PRAGMA synchronous=NORMAL;")  # Balance between speed and safety
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT UNIQUE,
        category TEXT,
        content BLOB, 
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

# Topic Seeds
TOPICS = [
    "Science", "Technology", "History", "Geography", "Mathematics", "Physics", "Chemistry", 
    "Biology", "Astronomy", "Medicine", "Psychology", "Philosophy", "Art", "Music", "Literature",
    "Sports", "Politics", "Economics", "Sociology", "Anthropology", "Architecture", "Engineering",
    "Computer Science", "Programming", "Artificial Intelligence", "Machine Learning", "Robotics",
    "Space Exploration", "Climate Change", "Renewable Energy", "Quantum Physics", "Genetics"
]

def compress(text):
    return zlib.compress(text.encode("utf-8"), level=6)  # Balanced compression

def get_size():
    return os.path.getsize(DB_NAME) if os.path.exists(DB_NAME) else 0

def collect_via_api(topic, retries=2):
    """Fast collection using Google API."""
    for attempt in range(retries):
        try:
            prompt = f"Write a comprehensive, detailed article about '{topic}'. Include history, key concepts, and modern applications. Length: 2000+ words."
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text
        except:
            time.sleep(0.5)
    return None

def collect_via_wiki(topic):
    """Fallback to Wikipedia."""
    try:
        page = wikipedia.page(topic, auto_suggest=False)
        return page.content
    except:
        return None

def main():
    print(f"\n🚀 PRAKRITI SPEED COLLECTOR V2")
    print(f"=" * 50)
    print(f"🎯 Target: {TARGET_GB} GB")
    print(f"🔑 Using: Google API + Wikipedia")
    print(f"=" * 50)
    
    collected = 0
    api_count = 0
    wiki_count = 0
    
    # Load existing topics to avoid duplicates
    cursor.execute("SELECT topic FROM memory")
    known = set(row[0].lower() for row in cursor.fetchall())
    
    while True:
        size = get_size()
        size_mb = size / (1024 * 1024)
        
        if size >= TARGET_BYTES:
            print(f"\n✅ TARGET REACHED! {size_mb:.2f} MB")
            break
        
        # Progress every 10 items
        if collected % 10 == 0:
            print(f"\r💾 {size_mb:.2f} MB | Topics: {collected} (API:{api_count} Wiki:{wiki_count})", end="", flush=True)
        
        # Get topic
        base = random.choice(TOPICS)
        search_res = wikipedia.search(base, results=20)
        
        topic = None
        for t in search_res:
            if t.lower() not in known:
                topic = t
                break
        
        if not topic:
            continue
        
        # Collect content (API first, then Wiki)
        content = collect_via_api(topic)
        source = "API"
        if content:
            api_count += 1 # type: ignore
        else:
            content = collect_via_wiki(topic)
            source = "Wiki"
            if content:
                wiki_count += 1 # type: ignore
        
        if not content or len(content) < 300:
            continue
        
        # Save
        final = f"""TOPIC: {topic}
SOURCE: {source}
DATE: {datetime.now()}
=============================
{content}
"""
        blob = compress(final)
        
        try:
            cursor.execute("INSERT OR IGNORE INTO memory (topic, category, content) VALUES (?, ?, ?)", 
                          (topic, "General", blob))
            conn.commit()
            known.add(topic.lower()) # type: ignore
            collected += 1 # type: ignore
        except:
            pass
        
        time.sleep(0.1)  # Small delay to avoid rate limits
    
    print(f"\n\n✅ COMPLETE! Collected {collected} topics.")

if __name__ == "__main__":
    main()
