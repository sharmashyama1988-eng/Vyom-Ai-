import os
import sys
import logging
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from google import genai
from dotenv import load_dotenv

# Load Env
load_dotenv()
GEMINI_KEY = os.getenv("GOOGLE_API_KEYS").split(',')[0] if os.getenv("GOOGLE_API_KEYS") else os.getenv("GEMINI_API_KEY")

# Configuration
DB_PATH = os.path.join(os.getcwd(), 'ai_core_memory')

class PragyanAI:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_KEY)
        self.embeddings = OllamaEmbeddings(model="mistral")
        
        # Connect to Shared Brain
        self.vector_db = Chroma(
            persist_directory=DB_PATH,
            embedding_function=self.embeddings,
            collection_name="vyom_knowledge"
        )
        print("🧠 Pragyan: Connected to Core Memory.")

    def ask(self, query):
        """Retrieves knowledge + Generates Answer"""
        print(f"\nThinking about: {query}...")
        
        # 1. RETRIEVE (Recall Memory)
        results = self.vector_db.similarity_search(query, k=3)
        context = "\n".join([doc.page_content for doc in results])
        
        if context:
            print(f"   💡 Recalled {len(results)} relevant memories.")
        else:
            print("   🌑 No specific memory found. Using general logic.")

        # 2. GENERATE (Answer)
        prompt = f"""
        You are 'Pragyan', an advanced AI.
        Use the retrieved memory below to answer the user's question accurately.
        If the memory contains real-time info from 'Guru', prioritize it.
        
        MEMORY CONTEXT:
        {context}
        
        USER QUESTION:
        {query}
        
        ANSWER:
        """
        
        response = self.client.models.generate_content(
            model='gemini-1.5-pro',
            contents=prompt
        )
        
        return response.text

if __name__ == "__main__":
    bot = PragyanAI()
    print("\n🙏 Namaste. I am Pragyan. Ask me anything.")
    print("(Type 'exit' to quit)\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            break
            
        answer = bot.ask(user_input)
        print(f"Pragyan: {answer}\n")
