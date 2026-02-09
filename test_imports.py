"""
Quick test to verify all imports work correctly
"""
import sys
print("Python executable:", sys.executable)
print("Python version:", sys.version)
print("\nTesting imports...")

try:
    import torch
    print("✓ torch")
except ImportError as e:
    print(f"✗ torch: {e}")

try:
    from dotenv import load_dotenv
    print("✓ dotenv")
except ImportError as e:
    print(f"✗ dotenv: {e}")

try:
    import vyom.config
    print("✓ vyom.config")
except ImportError as e:
    print(f"✗ vyom.config: {e}")

try:
    from langchain_community.document_loaders import DirectoryLoader
    print("✓ langchain_community")
except ImportError as e:
    print(f"✗ langchain_community: {e}")

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    print("✓ langchain_text_splitters")
except ImportError as e:
    print(f"✗ langchain_text_splitters: {e}")

try:
    from langchain_chroma import Chroma
    print("✓ langchain_chroma")
except ImportError as e:
    print(f"✗ langchain_chroma: {e}")

try:
    from langchain_core.embeddings import Embeddings
    print("✓ langchain_core")
except ImportError as e:
    print(f"✗ langchain_core: {e}")

try:
    from langchain_ollama import OllamaEmbeddings
    print("✓ langchain_ollama")
except ImportError as e:
    print(f"✗ langchain_ollama: {e}")

try:
    from google import genai
    print("✓ google.genai")
except ImportError as e:
    print(f"✗ google.genai: {e}")

try:
    from datasets import load_dataset
    print("✓ datasets")
except ImportError as e:
    print(f"✗ datasets: {e}")

try:
    from tqdm import tqdm
    print("✓ tqdm")
except ImportError as e:
    print(f"✗ tqdm: {e}")

try:
    import artificial_intelligence
    print("✓ artificial_intelligence (local module)")
except ImportError as e:
    print(f"✗ artificial_intelligence: {e}")

print("\n✅ Import test complete!")
