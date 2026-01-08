"""
VYOM AI - TRAINING MODULE
Handles the ingestion of knowledge base documents into the Vector Database (ChromaDB).
"""
import os
import sys
import shutil
import time
from dotenv import load_dotenv

# Import Configuration
import vyom.config as config

# Load env vars
load_dotenv()

def train_system(force=False):
    """
    Reads text files from 'knowledge_base', creates embeddings, 
    and saves them to the local ChromaDB.
    """
    # 1. Mode Check
    # If we have an API Key, we can train even in "Light" mode because it uses Cloud Embeddings.
    
    # Support for Multiple Keys (Load Balancer)
    api_keys_str = os.getenv("GOOGLE_API_KEYS")
    api_key_single = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    
    api_key = None
    if api_keys_str:
        # Take the first key for training (Training doesn't need rotation usually, just one valid key)
        api_key = api_keys_str.split(',')[0].strip()
    elif api_key_single:
        api_key = api_key_single
    
    if config.MODE == 'light' and not force and not api_key:
        print("⚠️  TRAINING SKIP ⚠️")
        print("   Current Mode: LIGHT")
        print("   Vector Database training requires 'Default' (Heavy) mode or a Google API Key.")
        print("   To force training, run: python Artificial_intelligence.py --force")
        return

    print(f"\n🧠 STARTING TRAINING SEQUENCE (Mode: {config.MODE.upper()})")
    print("   Target: Ingesting 'knowledge_base' into Vector DB...")

    try:
        # --- Imports (Only needed for training) ---
        from langchain_community.document_loaders import DirectoryLoader, TextLoader
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from langchain_chroma import Chroma
        from langchain_core.embeddings import Embeddings
        
        # --- Paths ---
        kb_path = os.path.join(os.getcwd(), 'knowledge_base')
        db_path = os.path.join(os.getcwd(), 'ai_core_memory')
        
        if not os.path.exists(kb_path):
            print(f"❌ Error: Knowledge Base directory not found: {kb_path}")
            return

        # --- 2. Load Documents ---
        print("   📂 Loading documents (Lazy Loading)...")
        # Fix: Explicitly specify UTF-8 encoding to avoid Windows cp1252 errors
        loader = DirectoryLoader(kb_path, glob="*.txt", loader_cls=TextLoader, loader_kwargs={'encoding': 'utf-8'})
        
        # Optimization: Use lazy_load to avoid OOM on large datasets
        docs = list(loader.lazy_load())
        
        if not docs:
            print("   ⚠️ No documents found in knowledge_base.")
            return
            
        print(f"   ✅ Loaded {len(docs)} documents.")

        # --- 3. Split Text ---
        print("   ✂️  Splitting text into chunks...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            add_start_index=True
        )
        splits = text_splitter.split_documents(docs)
        print(f"   ✅ Created {len(splits)} chunks.")

        # --- 4. Initialize Embeddings ---
        embeddings = None
        
        if api_key:
            print("   💎 Detected Google API Key. Using Gemini Cloud Embeddings (Optimized).")
            try:
                from google import genai
                
                # Custom Wrapper for Gemini Embeddings (avoids extra pip install)
                class GeminiEmbeddings(Embeddings):
                    def __init__(self, key):
                        self.client = genai.Client(api_key=key)
                        
                    def embed_documents(self, texts):
                        # Use Batch API to reduce request count
                        all_embeddings = []
                        batch_size = 10 # Google allows batches
                        
                        for i in range(0, len(texts), batch_size):
                            batch = texts[i:i+batch_size]
                            try:
                                # Clean text
                                batch = [t.replace("\n", " ") for t in batch]
                                
                                # API Call (Batch)
                                # New SDK: client.models.embed_content
                                result = self.client.models.embed_content(
                                    model="text-embedding-004", # Newer model
                                    contents=batch
                                )
                                # Result structure: result.embeddings list of objects
                                if result.embeddings:
                                    # Extract values from embedding objects
                                    current_batch_embeddings = [e.values for e in result.embeddings]
                                    all_embeddings.extend(current_batch_embeddings)
                                
                                # Rate Limit Guard (Free Tier safety)
                                time.sleep(2) 
                                
                            except Exception as e:
                                print(f"\n      ⚠️ Batch failed ({e}). Retrying individually...")
                                # Fallback: Item by item
                                for text in batch:
                                    try:
                                        res = self.client.models.embed_content(
                                            model="text-embedding-004",
                                            contents=text
                                        )
                                        # Single result: res.embeddings[0].values
                                        if res.embeddings:
                                             all_embeddings.append(res.embeddings[0].values)
                                        time.sleep(4) # Slow down significantly
                                    except Exception as ex:
                                        print(f"      ❌ Drop: {ex}")
                        
                        return all_embeddings
                    
                    def embed_query(self, text):
                        # Clean text
                        text = text.replace("\n", " ")
                        try:
                            result = self.client.models.embed_content(
                                model="text-embedding-004",
                                contents=text
                            )
                            return result.embeddings[0].values
                        except:
                            time.sleep(2) # Retry once
                            result = self.client.models.embed_content(
                                model="text-embedding-004",
                                contents=text
                            )
                            return result.embeddings[0].values
                
                embeddings = GeminiEmbeddings(api_key)
            except Exception as e:
                print(f"   ❌ Gemini Init Failed: {e}. Falling back to Local...")
        
        if not embeddings:
            print("   🔌 Connecting to Ollama (llama3.2) - LOCAL HEAVY PROCESS...")
            from langchain_ollama import OllamaEmbeddings
            embeddings = OllamaEmbeddings(model="llama3.2")

        # --- 5. Create/Update Vector DB ---
        print(f"   💾 Saving to ChromaDB at {db_path}...")
        
        # Initialize Chroma
        vector_store = Chroma(
            persist_directory=db_path,
            embedding_function=embeddings,
            collection_name="vyom_knowledge"
        )
        
        # Optimization: Batch processing for ChromaDB
        # Use smaller batch size to avoid long waits between updates
        batch_size = 10
        total_batches = (len(splits) + batch_size - 1) // batch_size
        
        print(f"   ⏳ Processing {len(splits)} chunks in {total_batches} batches...")
        
        for i in range(0, len(splits), batch_size):
            batch = splits[i:i+batch_size]
            vector_store.add_documents(documents=batch)
            print(f"      - Batch {i//batch_size + 1}/{total_batches} saved.", end='\r')
        
        print("\n🎉 TRAINING COMPLETE!")
        print(f"   The AI now remembers {len(splits)} new facts from the knowledge base.")

    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("   Ensure you have installed: langchain-ollama, langchain-chroma, langchain-community, google-generativeai")
    except Exception as e:
        print(f"\n❌ Training Failed: {e}")
        if not api_key:
            print("   Is Ollama running? (Run 'ollama serve' in another terminal)")

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