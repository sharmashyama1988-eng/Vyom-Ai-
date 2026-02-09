import os
import sqlite3
import glob

DB_PATH = os.path.join(os.getcwd(), "knowledge_base.db")
KNOWLEDGE_DIR = os.path.join(os.getcwd(), "knowledge_base")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Drop existing tables to ensure a clean slate
    c.execute('DROP TABLE IF EXISTS ai_knowledge')
    c.execute('DROP TABLE IF EXISTS ai_knowledge_fts')

    # Schema using FTS5 for fast full-text search
    # This is a virtual table, not a standard one.
    c.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS ai_knowledge_fts USING fts5(
            title, 
            summary, 
            topic_keyword,
            content='ai_knowledge',
            content_rowid='id'
        )
    ''')
    # Create the actual content table
    c.execute('''
        CREATE TABLE IF NOT EXISTS ai_knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            summary TEXT,
            topic_keyword TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn

def ingest_files():
    conn = init_db()
    c = conn.cursor()
    
    # Get all .txt files recursively
    files = glob.glob(os.path.join(KNOWLEDGE_DIR, "**", "*.txt"), recursive=True)
    
    print(f"Found {len(files)} text files in {KNOWLEDGE_DIR}")
    
    count = 0
    for file_path in files:
        try:
            filename = os.path.basename(file_path)
            title = os.path.splitext(filename)[0]
            
            # Simple deduplication
            c.execute("SELECT id FROM ai_knowledge WHERE title = ?", (title,))
            if c.fetchone():
                continue
                
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().strip()
                
            if not content:
                continue
                
            # Naive summary (first 500 chars) or full content if short
            # Since this is for RAG context, we might want to store chunks, 
            # but sticking to the existing schema which seems to expect 'summary' as the content payload.
            summary = content
            
            # Use directory name as topic keyword if available
            parent_dir = os.path.basename(os.path.dirname(file_path))
            topic_keyword = parent_dir if parent_dir != "knowledge_base" else "General"
            
            # Insert into the main table first
            c.execute('''
                INSERT INTO ai_knowledge (title, summary, topic_keyword)
                VALUES (?, ?, ?)
            ''', (title, summary, topic_keyword))
            
            # Now insert into the FTS table, linking it
            # The FTS table will automatically index the content
            last_id = c.lastrowid
            c.execute('''
                INSERT INTO ai_knowledge_fts (rowid, title, summary, topic_keyword)
                VALUES (?, ?, ?, ?)
            ''', (last_id, title, summary, topic_keyword))

            count += 1
            if count % 100 == 0:
                print(f"Ingested {count} files...")
                conn.commit()
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            
    conn.commit()
    conn.close()
    print(f"✅ Successfully ingested {count} new files into knowledge_base.db")

if __name__ == "__main__":
    ingest_files()
