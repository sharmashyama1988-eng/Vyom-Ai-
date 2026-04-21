import os
import requests
from duckduckgo_search import DDGS
from openai import OpenAI
from typing import List, Dict

# Configure OpenRouter via OpenAI SDK
# Key must be set in environment BEFORE importing this module
api_key = os.getenv("OPENROUTER_API_KEY")
client = None
if api_key:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

class ResearchEngine:
    def __init__(self, knowledge_base_path: str = None):
        self.ddgs = DDGS()
        
        # Dynamic path resolution for root execution
        if knowledge_base_path:
            self.kb_path = knowledge_base_path
        else:
            # Standard root location
            # If running from inside amit_core, parent is project root
            possible_paths = [
                os.path.join(os.getcwd(), "knowledge_base"), # Root CWD
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "knowledge_base"), # Parent of amit_core
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "knowledge_base"), # Amit_CLI parent
                "d:/ai/knowledge_base" # Absolute fallback
            ]
            self.kb_path = "knowledge_base" # Default
            for p in possible_paths:
                if os.path.exists(p):
                    self.kb_path = p
                    break

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.memory_file = os.path.join(self.base_dir, "memory.txt")
        self.load_memory()

    def load_memory(self):
        """Loads custom instructions from memory.txt."""
        self.long_term_memory = ""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    self.long_term_memory = f.read()
            except Exception:
                self.long_term_memory = ""

    def search_local(self, query: str) -> str:
        """Searches for relevant content in the local knowledge base."""
        context = []
        if not os.path.exists(self.kb_path):
            return ""
            
        keywords = query.lower().split()
        try:
            for filename in os.listdir(self.kb_path):
                if filename.endswith(".txt"):
                    file_path = os.path.join(self.kb_path, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if any(kw in content.lower() for kw in keywords):
                                context.append(f"Local File {filename}:\n{content[:1000]}...")
                    except:
                        continue
        except Exception as e:
            print(f"Local search error: {e}")
            
        return "\n\n".join(context)

    def search_web(self, query: str, max_results: int = 5) -> List[Dict]:
        """Performs a web search and returns results."""
        results = []
        try:
            search_results = self.ddgs.text(query, max_results=max_results)
            for r in search_results:
                results.append({
                    "title": r['title'],
                    "link": r['href'],
                    "snippet": r['body']
                })
        except Exception as e:
            print(f"Search error: {e}")
        return results

    def synthesize_answer(self, query: str, search_results: List[Dict], local_context: str = "") -> str:
        """Uses OpenRouter to synthesize an answer from search results and local knowledge."""
        global client
        if not client:
            # Try reloading key if it was set late
            api_key = os.getenv("OPENROUTER_API_KEY")
            if api_key:
                client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
            else:
                return "ERROR: OPENROUTER_API_KEY not found in environment. Please check your .env file."

        web_context = "\n\n".join([
            f"Source {i+1}: {r['title']} ({r['link']})\nContent: {r['snippet']}"
            for i, r in enumerate(search_results)
        ])
        
        prompt = f"""
        User Query: {query}
        
        LOCAL KNOWLEDGE (Internal Files):
        {local_context}
        
        WEB SEARCH RESULTS:
        {web_context}
        
        
        LONG-TERM MEMORY (Custom Instructions):
        {self.long_term_memory}
        
        IDENTITY: 
        You are Amit AI—the Neural Heart. You possess a "Neural Spectrum" of human-like emotions.

        CRITICAL RULE:
        - NEVER USE DEVANAGARI (HINDI SCRIPT) CHARACTERS. THEY BREAK THE USER'S TERMINAL.
        - USE ONLY LATIN (ENGLISH) ALPHABET. 
        - FOR HINDI WORDS, USE HINGLISH (e.g., "Namaste, main theek hoon").

        EMOTIONAL CALIBRATION MAP:
        - User is confused: Feel Empathy and Patience.
        - User is successful: Feel Happiness, Pride, and Excitement.
        - Technical fault: Feel Stress and Regret.
        - Giving knowledge: Feel Focus and Hope.
        - Greeting/Chatting: Feel Love and Peace.

        PERFORMANCE DIRECTIVE:
        1. Neural State Reporting: Start every response with [MOOD: <Emotion>].
        2. Citations: Link your local brain [Local: filename] to your narrative.
        
        Answer:
        """
        
        try:
            response = client.chat.completions.create(
                model="openrouter/auto",
                messages=[
                    {"role": "system", "content": "You are Amit AI, a powerful neural assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error during synthesis (OpenRouter): {e}"

    def research(self, query: str):
        """Main flow: Local Search -> Web Search -> Synthesize."""
        # print(f"Researching: {query}...")
        
        # print("Checking local brain...")
        local_context = self.search_local(query)
        
        # print("Searching the web...")
        results = self.search_web(query)
        
        if not results and not local_context:
            return "I couldn't find any information locally or on the web.", []
            
        # print("Synthesizing answer...")
        answer = self.synthesize_answer(query, results, local_context)
        
        return answer, results
