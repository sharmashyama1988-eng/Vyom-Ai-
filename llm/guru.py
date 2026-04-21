import os
import time
import random
import logging
import requests
from bs4 import BeautifulSoup
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.document_loaders import WikipediaLoader
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from google import genai
from dotenv import load_dotenv

# Load Env
load_dotenv()
GEMINI_KEY = os.getenv("GOOGLE_API_KEYS").split(',')[0] if os.getenv("GOOGLE_API_KEYS") else os.getenv("GEMINI_API_KEY")

# Configuration
DB_PATH = os.path.join(os.getcwd(), 'ai_core_memory')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [GURU] - %(message)s')
logger = logging.getLogger("Guru")

class GuruTrainer:
    def __init__(self):
        self.search_tool = DuckDuckGoSearchRun()
        self.client = genai.Client(api_key=GEMINI_KEY)
        self.embeddings = OllamaEmbeddings(model="mistral")
        
        # Connect to the Shared Brain (Pragyan's Memory)
        self.vector_db = Chroma(
            persist_directory=DB_PATH,
            embedding_function=self.embeddings,
            collection_name="Prakriti_knowledge"
        )
        
        self.topics_of_interest = [
            "Latest AI developments 2025",
            "SpaceX Starship updates",
            "Quantum Computing breakthroughs",
            "Global economic trends",
            "New programming languages",
            "Medical science discoveries",
            "Cybersecurity threats 2025"
        ]

    def fetch_internet_data(self, topic):
        """Searches DDGS/Google for real-time info."""
        try:
            logger.info(f"🔍 Searching Internet for: {topic}")
            results = self.search_tool.invoke(topic)
            return results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return None

    def fetch_wikipedia(self, topic):
        """Fetches detailed Wiki data."""
        try:
            loader = WikipediaLoader(query=topic, load_max_docs=1)
            docs = loader.load()
            if docs:
                return docs[0].page_content[:2000] # Limit size
        except:
            return None

    def synthesize_and_train(self, raw_data, topic):
        """Uses Gemini to summarize data into 'Knowledge Chunks'."""
        if not raw_data: return

        prompt = f"""
        You are 'Guru', the AI Teacher. 
        Read this raw data about '{topic}' and extract the core facts.
        Format it as a clear knowledge entry.
        
        RAW DATA:
        {raw_data}
        
        OUTPUT FORMAT:
        [Fact]: <The core information>
        """
        
        try:
            response = self.client.models.generate_content(
                model='gemini-1.5-flash', # Fast model for training
                contents=prompt
            )
            knowledge_chunk = response.text
            
            # 🧠 INJECT INTO MEMORY (Training)
            self.vector_db.add_texts(
                texts=[knowledge_chunk],
                metadatas=[{"source": "Guru-Realtime", "topic": topic, "timestamp": str(time.time())}]
            )
            logger.info(f"✅ TRAINED: Learned new facts about '{topic}'. Memory Updated.")
            
        except Exception as e:
            logger.error(f"Training failed: {e}")

    def start_auto_training(self):
        """Continuous Loop"""
        logger.info("🧘 Guru is entering deep meditation (Auto-Training Mode)...")
        print(">> Guru is running. Press Ctrl+C to stop.")
        
        while True:
            # 1. Pick a random topic or discover new one
            topic = random.choice(self.topics_of_interest)
            
            # 2. Gather Data
            data_web = self.fetch_internet_data(topic)
            
            # 3. Process & Train
            if data_web:
                self.synthesize_and_train(data_web, topic)
            
            # 4. Rest (Don't spam APIs)
            sleep_time = 60 # Train every 60 seconds
            logger.info(f"💤 Resting for {sleep_time}s...")
            time.sleep(sleep_time)

if __name__ == "__main__":
    guru = GuruTrainer()
    guru.start_auto_training()
