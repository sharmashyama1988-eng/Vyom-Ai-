import warnings
warnings.filterwarnings("ignore")

import wikipedia
from duckduckgo_search import DDGS
from rake_nltk import Rake
import sqlite3
import zlib  # यह है वो जादू जो साइज कम करेगा
import time
import random
import re

# --- CONFIGURATION ---
DB_NAME = "vyom_knowledge_compressed.db"
wikipedia.set_lang("en")

# --- DATABASE SETUP ---
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# टेबल बनाना (Blob का मतलब है Binary Object - यानी Compressed Data)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS knowledge (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT UNIQUE,
        category TEXT,
        tags TEXT,
        compressed_content BLOB, 
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

# --- HELPER FUNCTIONS ---
def get_keywords(text):
    r = Rake()
    r.extract_keywords_from_text(text)
    return ", ".join(r.get_ranked_phrases()[:10])

def get_ddgs_data(topic):
    try:
        results = DDGS().text(f"{topic} education facts", max_results=3)
        data = ""
        if results:
            for r in results:
                data += f"• {r['title']} - {r['body']}\n"
        return data
    except: return "Live data unavailable."

def compress_text(text):
    """टेक्स्ट को दबाकर छोटा करना (MB -> KB)"""
    return zlib.compress(text.encode("utf-8"))

# --- MAIN BOT ---
def run_db_bot(limit=5):
    """
    Runs the research bot for a specific number of new topics.
    limit: Number of new articles to fetch (default 5). Set to -1 for infinite.
    """
    print(f"🚀 ULTRA-COMPRESSED DATABASE BOT STARTED: {DB_NAME}")
    
    # पहले से मौजूद टॉपिक्स लोड करो
    try:
        cursor.execute("SELECT topic FROM knowledge")
        existing_topics = set(row[0].lower() for row in cursor.fetchall())
        print(f"✅ Loaded Memory: {len(existing_topics)} topics.")
    except:
        existing_topics = set()

    count = 0
    while True:
        if limit != -1 and count >= limit:
            print(f"🏁 Research Goal Reached ({limit} articles). Stopping...")
            break
            
        try:
            print(f"\n🔍 Hunting for knowledge ({count + 1}/{limit})...") # type: ignore
            
            # 1. Random Educational Topic Strategy
            # हम सीधे Wikipedia से रैंडम मांगेंगे (तेज़ तरीका)
            try:
                topic = wikipedia.random(1)
            except: continue

            if topic.lower() in existing_topics: # type: ignore
                continue # Duplicate check

            # Filter: कचरा हटाओ
            if "List of" in topic or re.match(r'^\d{4}$', topic):
                continue

            # 2. Fetch Data
            try:
                page = wikipedia.page(topic, auto_suggest=False)
                summary = page.summary
                content = page.content
                url = page.url
            except: continue

            if len(summary) < 300: continue # छोटा आर्टिकल नहीं चाहिए

            print(f"💎 Extracting: {topic}")

            # 3. Processing
            live_data = get_ddgs_data(topic)
            keywords = get_keywords(summary)

            # --- 4. DATA MERGING & COMPRESSION ---
            # सारा डेटा एक बड़े टेक्स्ट में मिलाओ
            full_text = f"""TOPIC: {topic}
SOURCE: {url}
TAGS: {keywords}
====================
[LIVE UPDATES]
{live_data}
====================
[SUMMARY]
{summary}
====================
[FULL CONTENT]
{content}
"""
            # जादू: साइज छोटा करो (Compress)
            compressed_blob = compress_text(full_text)
            
            # Original Size vs Compressed Size दिखाओ (ताकि तुम्हें यकीन हो)
            orig_size = len(full_text.encode('utf-8'))
            comp_size = len(compressed_blob)
            saved_percent = round((1 - comp_size/orig_size) * 100, 2) # type: ignore

            # 5. Save to Database
            cursor.execute('''
                INSERT INTO knowledge (topic, category, tags, compressed_content)
                VALUES (?, ?, ?, ?)
            ''', (topic, "General", keywords, compressed_blob))
            
            conn.commit()
            existing_topics.add(topic.lower()) # type: ignore

            print(f"✅ Saved: {topic}")
            print(f"   📉 Size: {orig_size} bytes -> {comp_size} bytes (Saved {saved_percent}%)")
            
            count += 1 # type: ignore
            time.sleep(random.randint(1, 3))

        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    run_db_bot()