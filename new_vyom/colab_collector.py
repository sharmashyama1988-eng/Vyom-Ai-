"""
Vyom AI | Data Collection Module (Colab Optimized)
Upload this to Google Colab to scrape research data.
"""

import requests
from bs4 import BeautifulSoup
import json
import os

def scrape_to_knowledge(url, output_folder="/content/drive/MyDrive/Vyom_KB"):
    """
    Scrapes a URL and saves text to a knowledge base folder.
    """
    print(f"Scraping: {url}...")
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()

        text = soup.get_text()
        # Break into lines and remove leading/trailing whitespace
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        clean_text = '\n'.join(chunk for chunk in chunks if chunk)

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        filename = url.replace("https://", "").replace("http://", "").replace("/", "_") + ".txt"
        filepath = os.path.join(output_folder, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"Source: {url}\n\n")
            f.write(clean_text)
            
        print(f"Saved to: {filepath}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

# Example usage for Colab:
# urls = ["https://en.wikipedia.org/wiki/Artificial_intelligence", "https://openai.com/blog"]
# for u in urls: scrape_to_knowledge(u)
