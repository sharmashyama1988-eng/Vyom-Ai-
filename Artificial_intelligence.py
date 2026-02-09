"""
VYOM AI - TRAINING MODULE
Handles the ingestion of knowledge base documents into the Vector Database (ChromaDB).
"""
import os
import sys
import shutil
import time
import concurrent.futures
import torch # type: ignore
from dotenv import load_dotenv # type: ignore

# Ensure the root project directory is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import Configuration
import vyom.config as config # type: ignore

# --- LangChain & AI Imports (Consolidated at top for IDE indexing) ---
try:
    from langchain_community.document_loaders import DirectoryLoader, TextLoader # type: ignore
    from langchain_text_splitters import RecursiveCharacterTextSplitter # type: ignore
    from langchain_chroma import Chroma # type: ignore
    from langchain_core.embeddings import Embeddings # type: ignore
    from langchain_ollama import OllamaEmbeddings # type: ignore
    from google import genai # type: ignore
except ImportError:
    # These might fail if running in minimal env, which is handled in train_system
    pass

# Load env vars
load_dotenv()


# --- HIGH PERFORMANCE TRAINING MODULE ---
# Architecture:
# 1. Main Thread: Reads from prakriti.db (Producer) -> Pushes to Queue
# 2. Embedding Workers (20 Threads): Pull from Queue -> Call Gemini API -> Push to Save Queue
# 3. Saver Thread: Pulls from Save Queue -> Writes to ChromaDB (Sequential)

import queue
import threading

def train_system(force=False):
    """
    High-Performance Multi-Threaded Training.
    Reads from DB -> Embeds in Parallel -> Saves Sequentially.
    """
    print("\n------------------------------------------------")
    print("🚀 VYOM AI: HIGH-PERFORMANCE TRAINING ENGINE")
    print("------------------------------------------------")

    # --- API KEY & SETUP ---
    api_keys_str = os.getenv("GOOGLE_API_KEYS")
    api_key_single = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    USER_PROVIDED_KEY = "AIzaSyDCHgac7XE5A_EpbRbTbENCBJL5CLD0H7Y"
    
    api_key = None
    if api_keys_str: api_key = api_keys_str.split(',')[0].strip()
    elif api_key_single: api_key = api_key_single
    else: api_key = USER_PROVIDED_KEY
    
    if not api_key:
        print("❌ Error: No API Key found. Cannot allow high-speed embedding.")
        return

    print(f"   🔑 API Key: {api_key[:5]}...")

    # --- QUEUES ---
    # raw_queue: holds (topic, text_content)
    # embedding_queue: holds (documents_with_embeddings)
    raw_queue = queue.Queue(maxsize=200) # Buffer
    embedding_queue = queue.Queue(maxsize=200) 
    
    # Flags
    is_loading_done = False
    
    # --- WORKER FUNCTIONS ---
    
    def producer_db_reader():
        """Reads compressed data from Prakriti DB and pushes text to raw_queue."""
        nonlocal is_loading_done
        try:
            prakriti_path = os.path.join(os.getcwd(), 'prakriti.db')
            if not os.path.exists(prakriti_path):
                print("❌ Prakriti DB not found.")
                is_loading_done = True
                return

            import sqlite3
            import zlib
            
            conn = sqlite3.connect(prakriti_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT Count(*) FROM memory")
            total = cursor.fetchone()[0]
            print(f"   📊 Total Items to Process: {total}")
            
            BATCH_SIZE = 1000
            offset = 0
            
            while offset < total:
                cursor.execute(f"SELECT topic, content FROM memory LIMIT {BATCH_SIZE} OFFSET {offset}")
                rows = cursor.fetchall()
                if not rows: break
                
                for topic, compressed_content in rows:
                    try:
                        text = zlib.decompress(compressed_content).decode("utf-8")
                        raw_queue.put((topic, text)) # Blocks if full
                    except: pass
                
                print(f"      [Reader] Processed {offset + len(rows)} / {total}", end='\r')
                offset += BATCH_SIZE
            
            conn.close()
            print("\n   ✅ [Reader] All data read from DB.")
        except Exception as e:
            print(f"   ❌ [Reader] Error: {e}")
        finally:
            is_loading_done = True

    def worker_embedder(worker_id):
        """Pulls text, calls Gemini API, pushes ready-to-save docs to embedding_queue."""
        client = genai.Client(api_key=api_key)
        
        while True:
            try:
                # Timeout allows checking is_loading_done
                item = raw_queue.get(timeout=2) 
            except queue.Empty:
                if is_loading_done: break
                continue
                
            topic, text = item
            
            # Simple Text Splitter (Manual to avoid overhead)
            # Just take first 2000 chars for now to speed up, or split properly
            chunks = [text[i:i+2000] for i in range(0, len(text), 2000)]
            
            processed_docs = []
            
            try:
                # Batch Embed Request
                batch_text = [c.replace("\n", " ") for c in chunks]
                # API Call
                result = client.models.embed_content(
                    model="text-embedding-004", contents=batch_text
                )
                
                if result.embeddings:
                    from langchain_core.documents import Document
                    for i, vector in enumerate(result.embeddings):
                        processed_docs.append(
                            (Document(page_content=chunks[i], metadata={"topic": topic}), vector.values)
                        )
                
                # Push to Saver
                if processed_docs:
                    embedding_queue.put(processed_docs)
                    
            except Exception as e:
                # print(f"W{worker_id} Error: {e}", end='\r')
                pass
            
            raw_queue.task_done()

    def consumer_saver():
        """Pulls embeddings and saves to ChromaDB (Single Threaded Write)."""
        db_path = os.path.join(os.getcwd(), 'ai_core_memory')
        
        # Init Chroma ONCE
        # We need a dummy embedding function because Chroma requires it, 
        # but we are providing pre-computed embeddings!
        class NullEmbeddings(Embeddings):
            def embed_documents(self, texts): return []
            def embed_query(self, text): return []

        vector_store = Chroma(
            persist_directory=db_path,
            embedding_function=NullEmbeddings(),
            collection_name="vyom_knowledge"
        )
        
        count = 0
        while True:
            try:
                # Bulk save if possible? No, stream it.
                batch_data = embedding_queue.get(timeout=2)
            except queue.Empty:
                if is_loading_done and raw_queue.empty() and embedding_queue.empty():
                    break
                continue
            
            # Unpack items
            # batch_data is list of (doc, vector)
            docs = [x[0] for x in batch_data]
            ids = [f"{count}_{i}" for i in range(len(docs))]
            embeddings = [x[1] for x in batch_data]
            
            try:
                # Chroma add_texts or add_documents usually takes embeddings arg?
                # Actually standard Chroma.add_documents RE-EMBEDS.
                # We must use `collection.add` directly or `add_embeddings`.
                # Langchain Chroma wrapper: `add_documents` doesn't take embeddings.
                # We need to access the underlying collection.
                vector_store._collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=[d.page_content for d in docs],
                    metadatas=[d.metadata for d in docs]
                )
                count += len(docs)
                if count % 100 == 0:
                     print(f"      💾 [Saver] Saved {count} chunks to Brain...   ", end='\r')
            except Exception as e:
                print(f"      ❌ [Saver] Error: {e}")
            
            embedding_queue.task_done()
            
    # --- EXECUTION ---
    
    # 1. Start Reader
    reader_thread = threading.Thread(target=producer_db_reader, daemon=True)
    reader_thread.start()
    
    # 2. Start Saver
    saver_thread = threading.Thread(target=consumer_saver, daemon=True)
    saver_thread.start()
    
    # 3. Start Workers
    NUM_WORKERS = 15 # 15 threads for API calls
    print(f"   🚀 Spawning {NUM_WORKERS} Embedding Workers...")
    workers = []
    for i in range(NUM_WORKERS):
        t = threading.Thread(target=worker_embedder, args=(i,), daemon=True)
        t.start()
        workers.append(t)
        
    # Join
    reader_thread.join()
    for t in workers: t.join()
    saver_thread.join()
    
    print("\n🎉 HIGH PERFORMANCE TRAINING COMPLETE!")


if __name__ == "__main__":
    train_system()


if __name__ == "__main__":
    # Allow CLI arguments to force training or set mode
    if "--force" in sys.argv:
        config.MODE = 'default' # Force default mode context
        train_system(force=True)
    else:
        # Check if we have an API Key (Cloud Mode)
        # Unified check
        keys_exist = os.getenv("GOOGLE_API_KEYS") or os.getenv("GOOGLE_API_KEY")
        
        if keys_exist:
            # If we have a key, we can train in Light mode without asking
            print(f"✨ Auto-detecting Cloud Key... Running in {config.MODE.upper()} mode.")
            train_system()
        elif config.MODE == 'light':
             # Ask user only if NO key is found
             print("You are currently in LIGHT mode.")
             choice = input("Do you want to switch to HEAVY mode and train? (y/n): ").strip().lower()
             if choice == 'y':
                 config.MODE = 'default'
                 train_system(force=True)
             else:
                 train_system()
        else:
            train_system()
