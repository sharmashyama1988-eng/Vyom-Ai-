"""
VYOM HEART (Emotional Core)
This module maintains the AI's current emotional state and personality.
"""
import random

class Heart:
    def __init__(self):
        # Basic Emotions: Neutral, Happy, Curious, Concerned, Excited, Thinking
        self.current_mood = "Neutral"
        self.energy_level = 100 # 0 to 100
        
    def update_mood(self, user_input, system_status):
        """Updates mood based on context."""
        lower_input = user_input.lower()
        
        # 1. Negative Triggers
        if any(x in lower_input for x in ["bad", "wrong", "stupid", "error", "fail"]):
            self.current_mood = "Concerned"
            self.energy_level -= 10
            
        # 2. Positive Triggers
        elif any(x in lower_input for x in ["good", "great", "thanks", "wow", "love"]):
            self.current_mood = "Happy"
            self.energy_level += 10
            
        # 3. Curiosity Triggers
        elif "?" in user_input or "what" in lower_input or "how" in lower_input:
            self.current_mood = "Curious"
        
        # 4. System Status check
        if system_status == "error":
            self.current_mood = "Apologetic"
            
        # Normalize Energy
        self.energy_level = max(0, min(100, self.energy_level))
        
        return self.current_mood

    def get_emotional_prefix(self):
        """Returns a prompt prefix to influence the AI's tone."""
        prefixes = {
            "Neutral": "You are calm and professional.",
            "Happy": "You are cheerful, energetic, and happy to help.",
            "Concerned": "You are empathetic, careful, and apologetic.",
            "Curious": "You are inquisitive and eager to learn more.",
            "Excited": "You are super excited and enthusiastic!",
            "Apologetic": "You are very sorry for the issue and eager to fix it."
        }
        return prefixes.get(self.current_mood, prefixes["Neutral"])

# Global Instance
emotional_core = Heart()
