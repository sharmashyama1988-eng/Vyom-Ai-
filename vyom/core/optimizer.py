"""
VYOM CORE OPTIMIZER
"iPhone-Level" Performance Manager.

Features:
1. Thread Pool for non-blocking I/O (Database writes).
2. LRU Caching for repeated queries.
3. Aggressive RAM Management (Garbage Collection).
"""

import gc
import threading
import functools
import time
from concurrent.futures import ThreadPoolExecutor
import vyom.config as config

class SystemOptimizer:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(SystemOptimizer, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized: return
        
        # Worker Pool: Background tasks (like saving history) won't block the UI
        # Increased workers for maximum speed
        self.executor = ThreadPoolExecutor(max_workers=20, thread_name_prefix="VyomWorker")
        
        # Simple In-Memory Cache for Light Mode responses
        self.response_cache = {} 
        self.max_cache_size = 200 # Increased cache size
        
        # Log startup in ASCII-safe way to avoid encoding issues
        print("System Optimizer: TURBO ACTIVE (20 Background Threads Ready)")
        self._initialized = True

    def run_in_background(self, func, *args, **kwargs):
        """
        Runs a function in a separate thread.
        Use this for DB writes, Analytics, or Cleanup.
        """
        self.executor.submit(func, *args, **kwargs)

    def cache_response(self, query, response, engine='general'):
        """
        Stores response with engine context to speed up repeated questions.
        """
        cache_key = f"{engine}:{query}"
        if len(self.response_cache) > self.max_cache_size:
            # Remove oldest item
            self.response_cache.pop(next(iter(self.response_cache)))
        
        self.response_cache[cache_key] = response

    def get_cached_response(self, query, engine='general'):
        cache_key = f"{engine}:{query}"
        return self.response_cache.get(cache_key)

    def optimize_memory(self):
        """
        Forces Garbage Collection. 
        Critical for Heavy Mode (Torch/CUDA).
        """
        gc.collect()
        
        # If using GPU/Torch, clear cache
        if config.MODE == 'default':
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except:
                pass

    def measure_performance(self, func):
        """Decorator to measure how long a function takes."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            end = time.time()
            # print(f"⏱️ {func.__name__} took {end - start:.4f}s")
            return result
        return wrapper

# Global Instance
performance = SystemOptimizer()
