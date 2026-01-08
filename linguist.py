try:
    from langdetect import detect
except ImportError:
    import warnings
    warnings.warn("langdetect package not found; language detection will default to 'en'. Install via 'pip install langdetect'")
    def detect(text):
        return "en"
import re

class LanguageMaster:
    def __init__(self):
        # Hinglish words ka database (Taaki AI confuse na ho)
        self.hinglish_markers = [
            "kya", "kaise", "kab", "kyu", "kahan", "hai", "hum", "tum", "aap",
            "karo", "btao", "dekho", "sun", "raha", "thi", "tha", "mein", "par",
            "karna", "chahiye", "sahi", "galat", "aaj", "kal", "samajh", "gaya",
            "thik", "badhiya", "mast", "kaam", "bhai", "dost", "yaar", "open", "kholo"
        ]

    def identify_language(self, text):
        """
        Ye function pata lagata hai ki user kaunsi bhasha bol raha hai.
        """
        if not text: return "en"
        text = text.lower()

        # 1. Check for Devanagari (Pure Hindi Script)
        if re.search(r'[\u0900-\u097F]', text):
            return "hindi_script"

        # 2. Check for Hinglish Keywords (Roman Hindi)
        words = text.split()
        hinglish_score = sum(1 for w in words if w in self.hinglish_markers)
        
        # Agar sentence mein 20% se zyada Hinglish words hain
        if hinglish_score > 0 or (len(words) > 0 and hinglish_score / len(words) > 0.2):
            return "hinglish"

        # 3. Standard Detection (English/Other)
        try:
            lang = detect(text)
            return lang
        except:
            return "en"

    def get_language_instruction(self, text):
        """
        Ye LLM (Brain) ke liye strict instruction banata hai.
        """
        lang_type = self.identify_language(text)
        
        if lang_type == "hindi_script":
            return "\n[STRICT LANGUAGE RULE]: The user is writing in Devanagari Hindi. Reply ONLY in pure Hindi (Devanagari)."
        
        elif lang_type == "hinglish":
            return "\n[STRICT LANGUAGE RULE]: The user is speaking Hinglish (Hindi written in English). Reply in natural Hinglish (e.g., 'Haan bhai, main kar sakta hoon'). DO NOT reply in full English."
        
        else:
            return "\n[LANGUAGE RULE]: Reply in the same language as the user (mostly English). Keep it professional yet friendly."

# Instance banaya taaki direct use ho sake
processor = LanguageMaster()