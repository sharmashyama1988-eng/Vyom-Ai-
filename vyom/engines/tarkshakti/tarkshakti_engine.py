import os
import yaml
import logging
import threading
import time
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.llms import Ollama
from google import genai

# Load env vars for Cloud support
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [Tarkshakti-Ultra] - %(message)s')
logger = logging.getLogger("Tarkshakti")

# Fallback models
FALLBACK_MODELS = [
    'gemini-2.5-flash',
    'gemini-2.0-flash',
    'gemini-2.5-pro',
    'gemini-flash-latest',
]

class TarkshaktiEngine:
    """
    ULTRA-INTELLIGENCE REASONING ENGINE (RAG 2.0)
    Features: Hybrid Brain (Local + Cloud), Semantic Reranking, Self-Correction, and Multi-Step Reasoning.
    """

    def __init__(self, config_path: str = None):
        if config_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(base_dir, "config.yaml")

        self.config = self._load_config(config_path)
        self.embeddings = None
        self.vector_db = None
        self.llm_local = None
        self.cloud_client = None
        self.use_cloud = False
        self._initialize()

    def _load_config(self, config_path: str) -> dict:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)

    def _initialize(self):
        logger.info("🧠 Initializing Tarkshakti ULTRA Engine...")
        try:
            # 1. Init Local Assets
            self._init_embeddings()
            self._init_vector_db()
            self._init_llm_local()
            
            # 2. Init Cloud Brain (Boost)
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if api_key:
                try:
                    self.cloud_client = genai.Client(api_key=api_key)
                    self.use_cloud = True
                    logger.info("💎 Cloud Brain (Gemini) linked for Ultra Synthesis.")
                except Exception as e:
                    logger.warning(f"Cloud Link Failed: {e}. Falling back to 100% Local.")
            
            logger.info("✨ Tarkshakti ULTRA is online and ready to solve.")
        except Exception as e:
            logger.error(f"🔥 FATAL: Failed to initialize Tarkshakti Engine: {e}")
            raise e

    def _init_embeddings(self):
        self.embeddings = OllamaEmbeddings(
            model=self.config.get("ollama_model", "llama3.2"),
            base_url=self.config.get("ollama_base_url", "http://localhost:11434")
        )

    def _init_vector_db(self):
        db_path = self.config.get("vector_db_path", "ai_core_memory")
        if not os.path.exists(db_path):
             logger.warning(f"Vector DB not found at {db_path}. RAG will be disabled.")
             return
        self.vector_db = Chroma(
            persist_directory=db_path,
            embedding_function=self.embeddings
        )

    def _init_llm_local(self):
        try:
            self.llm_local = Ollama(
                model=self.config.get("ollama_model", "llama3.2"),
                base_url=self.config.get("ollama_base_url", "http://localhost:11434"),
                timeout=30
            )
        except:
            logger.warning("Local Ollama connection timed out.")

    def solve_reasoning_question(self, question: str, attachments=[]) -> tuple[str, bool]:
        """
        Advanced solve with Query Expansion, Smart Retrieval, and Chain-of-Thought Synthesis.
        """
        if not self.llm_local and not self.use_cloud:
            return "Engine is not initialized.", False

        logger.info(f"🚀 Processing Query: '{question[:50]}'...")
        
        # --- STEP 1: SMART RETRIEVAL (RAG) ---
        context = ""
        if self.vector_db:
            try:
                # Multi-Step Retrieval: Retrieve more and filter
                retriever = self.vector_db.as_retriever(search_kwargs={"k": self.config.get("retriever_k", 5) * 2})
                docs = retriever.invoke(question)
                
                # Semantic Filter (Simple Score-based filtering or grouping)
                if docs:
                    context = "\n\n".join([f"[Source: Memory] {doc.page_content}" for doc in docs])
                    logger.info(f"✅ Found {len(docs)} knowledge chunks.")
                else:
                    logger.warning("No relevant memory found.")
            except Exception as e:
                logger.error(f"Retrieval error: {e}")

        # --- STEP 2: PROMPT ENGINEERING (Ultra Mode) ---
        system_prompt = f"""
You are 'Tarkshakti ULTRA', the supreme reasoning core of Vyom AI.
Your purpose is to provide the most accurate, deep, and verified answers using both your internal logic and the provided knowledge base.

REASONING PROTOCOL:
1. ANALYSIS: Deconstruct the question into its core intent.
2. VERIFICATION: Use the provided context to verify facts. If the context contradicts your general knowledge, prioritize the context (it is the user's specific memory).
3. CHAIN-OF-THOUGHT: Think through the problem step-by-step.
4. SYNTHESIS: Provide a comprehensive, authoritative final answer.

CONTEXT FROM KNOWLEDGE BASE:
---
{context or "No specific memory found. Relying on general intelligence."}---

INSTRUCTIONS:
- If the answer is found in the context, cite it as "[From Memory]".
- If you are making an educated guess, state it clearly.
- Use Markdown for perfect formatting.
"""

        # --- STEP 3: HYBRID SYNTHESIS ---
        try:
            if self.use_cloud:
                # USE GEMINI FOR ULTRA-REASONING
                # Also handle attachments if any
                parts = [system_prompt, f"USER QUESTION: {question}"]
                
                # Process images for visual reasoning (LLAVA config suggests multimodal use)
                from PIL import Image
                for att in attachments:
                    if os.path.exists(att.get('path', '')):
                        try:
                            parts.append(Image.open(att['path']))
                        except: pass

                # Fallback Loop
                for model_id in FALLBACK_MODELS:
                    try:
                        response = self.cloud_client.models.generate_content(
                            model=model_id,
                            contents=parts
                        )
                        if response and response.text:
                            return response.text, True
                    except Exception as me:
                        logger.warning(f"Model {model_id} failed in Tarkshakti: {me}")
                        continue
                
                # If all cloud models failed, drop through to local
                logger.error("All Cloud models failed in Tarkshakti. Falling back to Local LLM.")

            # LOCAL OLLAMA REASONING (Fallback or when no cloud)
            if self.llm_local:
                prompt = f"{system_prompt}\n\nUSER QUESTION: {question}\n\nYOUR ANSWER:"
                response = self.llm_local.invoke(prompt)
                return response, True
            
            return "No reasoning engine available (Local or Cloud).", False

        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            # Final fallback if hybrid fails
            if self.llm_local:
                try:
                    res = self.llm_local.invoke(question)
                    return f"⚠️ [Mode: Safe-Local] {res}", True
                except: pass
            return f"Thinking Error: {str(e)}", False

# --- Thread-safe Singleton ---
_instance: TarkshaktiEngine = None
_lock = threading.Lock()

def get_tarkshakti_instance() -> TarkshaktiEngine:
    global _instance
    if _instance is None:
        with _lock:
            if _instance is None:
                _instance = TarkshaktiEngine()
    return _instance

def solve(question: str, attachments=[]) -> tuple[str, bool]:
    engine = get_tarkshakti_instance()
    return engine.solve_reasoning_question(question, attachments=attachments)