# Performance-oriented Imports
from vyom.core import identity
import time
import threading
import hashlib
import asyncio
from typing import Optional
from cachetools import TTLCache

# --- Caching & Instrumentation ---
# Cache system instruction for short intervals to avoid repeated expensive calls
_system_instruction_cache = TTLCache(maxsize=1, ttl=60)

def get_system_instruction_cached(refresh_interval: int = 60) -> str:
    """Return cached system instruction, refresh every `refresh_interval` seconds."""
    # TTLCache handles the TTL, so we just need to check if the key is in the cache
    if 'system_instruction' not in _system_instruction_cache:
        _system_instruction_cache['system_instruction'] = identity.get_system_instruction()
    return _system_instruction_cache['system_instruction']

# Simple in-memory cache for LLM calls keyed by (llm_func_id, prompt_hash)
_llm_cache = TTLCache(maxsize=1000, ttl=300)
_llm_cache_lock = threading.Lock()

def _cached_call(llm_func, prompt: str, ttl: int = 300):
    # Update the TTL of the cache if a different one is provided
    if _llm_cache.ttl != ttl:
        _llm_cache.ttl = ttl

    key = (id(llm_func), hashlib.sha256(prompt.encode()).hexdigest())
    
    with _llm_cache_lock:
        if key in _llm_cache:
            # Cache hit
            print(f"✅ LLM cache hit (prompt {key[1][:8]})")
            return _llm_cache[key]

    # Cache miss — call LLM and store result
    start = time.perf_counter()
    result = llm_func(prompt)
    duration = time.perf_counter() - start

    with _llm_cache_lock:
        _llm_cache[key] = result

    print(f"🔁 LLM call took {duration:.3f}s (prompt {key[1][:8]})")
    return result


# ... Other agents ...

def agent_analyst(query: str,
                  web_res: Optional[str],
                  math_res: Optional[str],
                  logic_res: Optional[str],
                  llm_func,
                  use_cache: bool = True,
                  cache_ttl: int = 300):
    """Analyst agent that prefers logic/math results, otherwise uses LLM.

    Optimizations:
    - Returns early for `logic_res` or `math_res` to avoid LLM calls.
    - Uses a cached system instruction and an optional LLM response cache.
    - Adds timing/logging for visibility into LLM latency.
    """
    if logic_res:
        return logic_res
    if math_res:
        return math_res

    # Use provided web context if available
    context_text = web_res or "No external context available."

    system_instruction = get_system_instruction_cached()

    final_prompt = f"""
{system_instruction}

CONTEXT: {context_text}
USER QUERY: {query}

ANSWER:
"""

    if use_cache:
        return _cached_call(llm_func, final_prompt, ttl=cache_ttl)
    else:
        start = time.perf_counter()
        res = llm_func(final_prompt)
        elapsed = time.perf_counter() - start
        print(f"🔁 LLM direct call took {elapsed:.3f}s")
        return res


async def agent_analyst_async(query: str,
                              web_res: Optional[str],
                              math_res: Optional[str],
                              logic_res: Optional[str],
                              llm_func,
                              use_cache: bool = True,
                              cache_ttl: int = 300):
    """Async wrapper that runs the blocking `agent_analyst` in a thread pool.

    Useful if the surrounding application is asyncio-based.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, agent_analyst, query, web_res, math_res, logic_res, llm_func, use_cache, cache_ttl)

# ... Main function ...