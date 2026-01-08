"""
VYOM AI INTERNET MODULE (No-API Version)
Uses DuckDuckGo to fetch live search results.
"""
from duckduckgo_search import DDGS

def search_google(query):
    """
    Internet se live data nikalta hai bina API key ke.
    """
    try:
        # Keywords saaf karo (Search query optimize karo)
        clean_query = query.replace("search for", "").replace("google", "").replace("search", "").strip()
        
        print(f"🌍 Searching Internet for: {clean_query}...")
        
        results_text = ""
        
        # DuckDuckGo se Top 5 results nikalo (Better coverage)
        with DDGS() as ddgs:
            # News specific keywords optimize recency
            search_args = {"keywords": clean_query, "max_results": 4}
            
            # If news related, use news search for recency
            news_keywords = ['news', 'score', 'weather', 'stock', 'today', 'latest']
            if any(k in clean_query.lower() for k in news_keywords):
                results = list(ddgs.news(clean_query, max_results=4))
            else:
                results = list(ddgs.text(clean_query, max_results=4))
            
            if not results:
                return None
            
            formatted_results = []
            for i, r in enumerate(results):
                title = r.get('title', 'No Title')
                body = r.get('body', r.get('snippet', ''))
                href = r.get('href', r.get('link', '#'))
                date = r.get('date', '')
                
                date_str = f" *({date})*" if date else ""
                
                item = f"### {i+1}. {title}{date_str}\n{body}\n\n🔗 [Read More]({href})"
                formatted_results.append(item)

            return "\n\n---\n\n".join(formatted_results)

    except Exception as e:
        print(f"❌ Internet Error: {e}")
        return None