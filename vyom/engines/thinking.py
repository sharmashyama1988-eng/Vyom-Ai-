"""
VYOM AI THINKING ENGINE
Powered by Deep Thought (LangChain + Ollama)

This module is the entry point for complex reasoning tasks.
It delegates the actual processing to the Deep Thought Engine.
"""

from . import deep_thought

def solve_with_reasoning(user_query, llm_model=None, user_api_key=None):
    """
    Solves complex queries using the Deep Thought Engine.
    
    Args:
        user_query (str): The user's question or request.
        llm_model (object): Deprecated/Unused.
        user_api_key (str): Optional. The user's personal API Key (BYOK).
        
    Returns:
        str: The AI's response.
    """
    # Delegate to the Deep Thought Engine
    answer, success = deep_thought.solve(user_query, user_api_key=user_api_key)
    
    if not success:
        # Fallback message if the engine fails
        return f"I'm having trouble thinking right now. ({answer})"
        
    return answer
