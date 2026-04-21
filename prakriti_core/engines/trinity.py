import os
import sys
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from prakriti_core.core import internet # type: ignore
from prakriti_core.core import formatter # type: ignore
from prakriti_core.core import knowledge # type: ignore

# Smart Language & Context Processing
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    import linguist  # type: ignore
    import supervisor  # type: ignore
    LANGUAGE_SUPPORT = True
except ImportError:
    LANGUAGE_SUPPORT = False
    print("⚠️ Warning: linguist/supervisor modules not found. Advanced features disabled.")

# Base Configuration
CUSTOM_MODEL_PATH = "./Prakriti"
BASE_MODEL_NAME = "HuggingFaceTB/SmolLM2-135M" # Tiny but effective fallback foundation

# Global State for Model (Loaded Once)
_model = None
_tokenizer = None
_pipe = None

def get_system_instruction(engine_type):
    return formatter.get_system_instruction(engine_type)

def classify_query(prompt):
    """
    AI-Powered Query Classification for Intelligent Routing
    Returns: 'internet', 'local', or 'hybrid'
    """
    prompt_lower = prompt.lower()
    
    # 1. INTERNET REQUIRED (Real-time / Latest data)
    internet_keywords = [
        'news', 'latest', 'today', 'current', 'now', 'recent',
        'weather', 'score', 'stock', 'price', 'trending',
        'aaj', 'abhi', 'latest', 'taza khabar', 'match',
        'election', 'update', 'breaking'
    ]
    
    # 2. LOCAL LLM PREFERRED (Logic, Code, General Knowledge)
    local_keywords = [
        'code', 'program', 'function', 'algorithm', 'explain',
        'kaise', 'kya hai', 'batao', 'samjhao', 'define',
        'calculate', 'solve', 'write', 'create', 'how to',
        'what is', 'tell me about', 'prakriti'
    ]
    
    # 3. HYBRID (Both needed - Knowledge + Verification)
    hybrid_keywords = [
        'compare', 'difference', 'vs', 'better', 'best',
        'review', 'opinion', 'recommend', 'suggest'
    ]
    
    # Classification Logic
    internet_score = sum(1 for kw in internet_keywords if kw in prompt_lower)
    local_score = sum(1 for kw in local_keywords if kw in prompt_lower)
    hybrid_score = sum(1 for kw in hybrid_keywords if kw in prompt_lower)
    
    # Decision
    if internet_score > local_score and internet_score > hybrid_score:
        return 'internet'
    elif hybrid_score > 0:
        return 'hybrid'
    else:
        return 'local'

def load_local_engine():
    """
    Loads your custom-built LLM into memory.
    """
    global _model, _tokenizer, _pipe
    
    if _pipe is not None:
        return _pipe

    model_path = CUSTOM_MODEL_PATH if os.path.exists(CUSTOM_MODEL_PATH) else BASE_MODEL_NAME
    print(f"\n⚙️ Trinity: Loading Neural Engine ({model_path})...")
    
    try:
        # Load from disk or Hub
        _tokenizer = AutoTokenizer.from_pretrained(model_path)
        _model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" # Uses GPU if available, else CPU
        )
        
        # Create Pipeline
        _pipe = pipeline(
            "text-generation",
            model=_model,
            tokenizer=_tokenizer,
            max_new_tokens=512,
            truncation=True,
            temperature=0.7,
            do_sample=True,
            top_k=50,
            top_p=0.95,
        )
        print("✅ Trinity: Engine Online.")
        return _pipe
    except Exception as e:
        print(f"❌ Failed to load LLM: {e}")
        return None


def generate_response(prompt, engine_type="general", history=[], user_api_key=None, attachments=[], model=None):
    try:
        # 🌍 LANGUAGE DETECTION (Hinglish Support)
        language_instruction = ""
        if LANGUAGE_SUPPORT:
            language_instruction = linguist.processor.get_language_instruction(prompt)
            print(f"🗣️ Language: {linguist.processor.identify_language(prompt)}")
        
        # 🤖 INTELLIGENT ROUTING
        query_type = classify_query(prompt)
        print(f"🎯 Trinity: Route = {query_type.upper()}")
        
        system_instruction = get_system_instruction(engine_type) + language_instruction
        
        # ========== ROUTE 1: INTERNET ONLY ==========
        if query_type == 'internet':
            print("🌐 Trinity: Using Internet (Real-time Data)")
            search_data = internet.search_google(prompt)
            if search_data:
                return f"### 🌍 Live Internet Results:\n\n{search_data}"
            else:
                return "⚠️ Could not fetch internet data. Please check your connection."
        
        # ========== ROUTE 2: HYBRID MODE ==========
        elif query_type == 'hybrid':
            print("⚡ Trinity: Hybrid Mode (Internet + Local AI)")
            
            # Step 1: Get internet data
            internet_data = internet.search_google(prompt)
            
            # Step 2: Get local knowledge
            local_knowledge = knowledge.search_knowledge(prompt)
            
            # Step 3: Clean context using supervisor (remove irrelevant data)
            if LANGUAGE_SUPPORT and supervisor:
                if internet_data:
                    internet_data = supervisor.guard.clean_context(prompt, internet_data)
                    print("   ✓ Context cleaned by supervisor")
            
            # Step 4: Combine and send to LLM for synthesis
            context_block = ""
            if internet_data:
                context_block += f"### INTERNET SOURCES:\n{internet_data}\n\n"
            if local_knowledge:
                context_block += f"### LOCAL KNOWLEDGE:\n{local_knowledge}\n\n"
            
            if not context_block:
                context_block = "[No additional context available]\n"
            
            full_prompt = (
                f"<|im_start|>system\n{system_instruction}\n<|im_end|>\n"
                f"<|im_start|>user\n{context_block}User Question: {prompt}\n<|im_end|>\n"
                f"<|im_start|>assistant\n"
            )
            
            generator = load_local_engine()
            if generator:
                outputs = generator(full_prompt)
                if outputs and len(outputs) > 0:
                    answer = outputs[0]['generated_text'].replace(full_prompt, "").strip()
                    answer = answer.split("<|im_end|>")[0].strip()
                    return f"### 🧠 Hybrid Analysis:\n\n{answer}"
            
            # Fallback: Return raw data
            return context_block
        
        # ========== ROUTE 3: LOCAL LLM ONLY ==========
        else:  # query_type == 'local'
            print("🧠 Trinity: Using Local AI (Prakriti)")
            
            # Check Internal Knowledge Base (RAG)
            internal_knowledge = knowledge.search_knowledge(prompt)
            
            if internal_knowledge:
                print(f"   ✓ Found {len(internal_knowledge)} chars from knowledge base")
                context_block = f"CONTEXT:\n{internal_knowledge}\n"
            else:
                context_block = ""
            
            full_prompt = (
                f"<|im_start|>system\n{system_instruction}\n<|im_end|>\n"
                f"<|im_start|>user\n{context_block}{prompt}\n<|im_end|>\n"
                f"<|im_start|>assistant\n"
            )
            
            # Load Engine
            generator = load_local_engine()
            
            if not generator:
                return "⚠️ **Neural Engine Error:** Prakriti model not available. Please run `python train_prakriti.py` first."
            
            # Generate
            outputs = generator(full_prompt)
            
            # Extract response
            if outputs and len(outputs) > 0:
                generated_text = outputs[0]['generated_text']
                answer = generated_text.replace(full_prompt, "").strip()
                answer = answer.split("<|im_end|>")[0].strip()
                return answer
                
            return "⚠️ I couldn't generate a thought."

    except Exception as e:
        # 🛡️ ULTIMATE FALLBACK: Web Search
        print(f"⚠️ Critical Error: {e}. Falling back to internet...")
        search_data = internet.search_google(prompt)
        if search_data:
             return f"⚠️ **System Error.** Here's what I found online:\n\n{search_data}"
        return f"⚠️ Critical Error: {str(e)}"
