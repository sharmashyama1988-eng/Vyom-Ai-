import sqlite3
import logging
import os

# Configure Logging
logger = logging.getLogger("KnowledgeRetriever")

DB_PATH = os.path.join(os.getcwd(), "knowledge_base.db")

def search_knowledge(query, limit=3):
    """
    Searches the SQLite FTS virtual table for relevant topics based on the query.
    """
    if not os.path.exists(DB_PATH):
        return None

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # FTS5 requires a specific query format. 
        # We can just pass the user's query, but cleaning it is better.
        # Let's create a simple FTS query by treating words as a sequence.
        # Example: "hello world" -> "hello NEAR world"
        # For now, we just pass the raw query and let FTS handle it.
        # FTS5 will parse it, handle stop words, etc.
        
        # The query now targets the FTS virtual table
        # We use MATCH for full-text search and 'rank' for ordering by relevance
        sql = '''
            SELECT title, summary, topic_keyword 
            FROM ai_knowledge_fts 
            WHERE ai_knowledge_fts MATCH ?
            ORDER BY rank 
            LIMIT ?
        '''
        
        c.execute(sql, (query, limit))
        results = c.fetchall()
        conn.close()
        
        if not results:
            return None
            
        # Format results into a string for the LLM
        knowledge_text = "### 🧠 Internal Knowledge Base Matches:\n"
        for row in results:
            title, summary, keyword = row
            knowledge_text += f"- **{title}** ({keyword}): {summary}\n"
            
        return knowledge_text

    except Exception as e:
        logger.error(f"Knowledge DB Search Failed: {e}")
        return None
