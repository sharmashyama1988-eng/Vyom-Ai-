import re

class TopicGuard:
    def __init__(self):
        # Ye wo words hain jo aksar AI ko bhatka dete hain
        self.stop_words = ["as an ai", "i cannot", "however", "in general", "context based"]
        
    def clean_context(self, query, context):
        """
        Ye function Web Search ke kachre (Irrelevant Data) ko saaf karta hai
        taaki AI confuse na ho.
        """
        if not context: return "No external context available."
        
        # Query ke main keywords nikalo
        keywords = [w for w in query.lower().split() if len(w) > 3]
        
        relevant_lines = []
        lines = context.split('\n')
        
        for line in lines:
            # Sirf wahi line rakho jisme query se juda kuch ho
            if any(k in line.lower() for k in keywords):
                relevant_lines.append(line)
        
        # Agar filtering ke baad sab kuch udd gaya, to original wapas de do
        if not relevant_lines:
            return context
            
        return "\n".join(relevant_lines)

    def get_strict_prompt(self, query, context):
        """
        Ye prompt AI ko topic se hilne nahi dega.
        Ismein 'Negative Prompting' use ki gayi hai.
        """
        clean_ctx = self.clean_context(query, context)
        
        return f"""
        *** STRICT INSTRUCTIONS (DO NOT IGNORE) ***
        ROLE: You are a Precision AI. You DO NOT chat vaguely. You answer EXACTLY what is asked.
        
        USER QUESTION: "{query}"
        
        VERIFIED FACTS (SOURCE OF TRUTH):
        {clean_ctx}
        
        RULES:
        1. STICK TO THE TOPIC: If the question is about "Downloading Office", DO NOT talk about "What is Office".
        2. NO FLUFF: Do not say "Here is the answer" or "I hope this helps". Just give the steps/answer.
        3. SOURCE ADHERENCE: Use the 'VERIFIED FACTS' above. If the answer is not there, use your internal knowledge but keep it relevant.
        4. STYLE: Speak like a pro developer (Hinglish). Direct & Sharp.
        
        YOUR ANSWER:
        """

# Instance banaya taaki direct import ho sake
guard = TopicGuard()