import sqlite3
import logging
import os
import zlib

# Configure Logging
logger = logging.getLogger("KnowledgeRetriever")

# List of databases to check, in order of priority
# 1. 'prakriti.db' - The massive 3-hour scrape (High Quality)
# 2. 'vyom_knowledge_compressed.db' - Auto-Research bot (Continuous)
# 3. 'knowledge_base.db' - Legacy
DB_FILES = {
    "prakriti": "prakriti.db",
    "research": "vyom_knowledge_compressed.db",
    "legacy": "knowledge_base.db"
}

def decompress_data(blob):
    """Decompresses zlib data if possible, else returns as string."""
    try:
        if isinstance(blob, bytes):
            return zlib.decompress(blob).decode('utf-8')
        return str(blob)
    except:
        return str(blob)

def search_knowledge(query, limit=2):
    """
    Searches all available local databases for knowledge.
    Returns a combined string of findings.
    """
    final_output = ""
    found_count = 0
    
    # Clean query for SQL LIKE (Simple search)
    search_term = f"%{query}%"
    
    for db_name, db_file in DB_FILES.items():
        if not os.path.exists(db_file):
            continue
            
        try:
            conn = sqlite3.connect(db_file)
            c = conn.cursor()
            
            # Different DBs have slightly different schemas, so we try standardized queries
            results = []
            
            try:
                # 1. Try Prakriti/Research Schema (topic, content/compressed_content)
                # We prioritize exact topic matches, then content matches
                if "prakriti" in db_name or "research" in db_name:
                    sql = """
                        SELECT topic, content 
                        FROM memory 
                        WHERE topic LIKE ? OR category LIKE ? 
                        ORDER BY timestamp DESC LIMIT ?
                    """
                    # Handle schema difference: research uses 'compressed_content' and 'knowledge' table
                    if "research" in db_name:
                         sql = """
                            SELECT topic, compressed_content 
                            FROM knowledge 
                            WHERE topic LIKE ? OR tags LIKE ? 
                            ORDER BY created_at DESC LIMIT ?
                        """
                    
                    c.execute(sql, (search_term, search_term, limit))
                    rows = c.fetchall()
                    
                    for r in rows:
                        topic = r[0]
                        content = decompress_data(r[1])
                        # Extract a snippet if too long
                        snippet = content[:500] + "..." if len(content) > 500 else content # type: ignore
                        results.append(f"[{db_name.upper()} MEMORY] Topic: {topic}\n{snippet}")

            except Exception:
                # Fallback or different schema
                pass

            conn.close()
            
            if results:
                for res in results:
                    final_output += f"{res}\n\n"
                    found_count += 1 # type: ignore
                    
            if found_count >= limit:
                 break # Stop if we found enough good info

        except Exception as e:
            logger.error(f"Error reading {db_name}: {e}")

    if not final_output:
        return None
        
    return f"### 🧠 INTERNAL MEMORY RETRIEVAL:\n{final_output}"

