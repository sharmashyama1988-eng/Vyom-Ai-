import sqlite3
import logging
import os
import zlib
import time

# Configure Logging
logger = logging.getLogger("KnowledgeRetriever")

# List of databases to check, in order of priority
DB_FILES = {
    "prakriti": "prakriti.db",
    "research": "vyom_knowledge_compressed.db",
    "legacy": "knowledge_base.db"
}

# --- VECTOR DB SETUP ---
try:
    from langchain_chroma import Chroma # type: ignore
    from langchain_huggingface import HuggingFaceEmbeddings # type: ignore
    HAS_VECTOR_DB = True
except ImportError:
    HAS_VECTOR_DB = False

def decompress_data(blob):
    """Decompresses zlib data if possible, else returns as string."""
    try:
        if isinstance(blob, bytes):
            return zlib.decompress(blob).decode('utf-8')
        return str(blob)
    except:
        return str(blob)

def search_vector_memory(query, limit=3):
    """
    Searches the semantic vector database (ai_core_memory).
    """
    if not HAS_VECTOR_DB: return ""
    
    db_path = os.path.join(os.getcwd(), 'ai_core_memory')
    if not os.path.exists(db_path): return ""

    try:
        # Load Local Embedding Model (Must match training)
        embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        vector_store = Chroma(
            persist_directory=db_path,
            embedding_function=embedding_model,
            collection_name="vyom_knowledge"
        )
        
        # Search
        results = vector_store.similarity_search(query, k=limit)
        
        output = ""
        for i, doc in enumerate(results):
             output += f"[VECTOR MEMORY] Context: {doc.page_content}\n"
             
        return output

    except Exception as e:
        logger.error(f"Vector DB Error: {e}")
        return ""

def search_knowledge(query, limit=2):
    """
    Searches all available local databases (SQL + Vector) for knowledge.
    Returns a combined string of findings.
    """
    final_output = ""
    found_count = 0
    
    # 1. Search Vector DB (Semantic)
    vector_results = search_vector_memory(query, limit=2)
    if vector_results:
        final_output += f"### 🧠 VECTOR MEMORY (Semantic):\n{vector_results}\n\n"
        found_count += 1

    # 2. Search SQL DBs (Keyword)
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
                if "prakriti" in db_name or "research" in db_name:
                    sql = """
                        SELECT topic, content 
                        FROM memory 
                        WHERE topic LIKE ? OR category LIKE ? 
                        ORDER BY timestamp DESC LIMIT ?
                    """
                    # Handle schema difference
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
                        results.append(f"[{db_name.upper()} SQL] Topic: {topic}\n{snippet}")

            except Exception:
                pass

            conn.close()
            
            if results:
                for res in results:
                    final_output += f"{res}\n\n"
                    found_count += 1
                    
            if found_count >= (limit + 1): # Heuristic limit
                 break 

        except Exception as e:
            logger.error(f"Error reading {db_name}: {e}")

    if not final_output:
        return None
        
    return f"### 🧠 INTERNAL MEMORY RETRIEVAL:\n{final_output}"

