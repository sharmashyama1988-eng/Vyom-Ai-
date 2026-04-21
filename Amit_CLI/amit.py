import os
import sys
from dotenv import load_dotenv

# 1. Load environment variables first
load_dotenv()

# 2. Fix search paths for module imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# 3. Import from local core
from amit_core.researcher import ResearchEngine

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    engine = ResearchEngine()
    
    clear_screen()
    print("==========================================")
    print("   AMIT AI | NEURAL SEARCH INTERFACE")
    print("==========================================")
    print(f"   Environment: Stable CLI v1.0")
    print("   Type 'exit' or 'quit' to close.")
    print("==========================================\n")

    while True:
        try:
            query = input("Amit AI > ").strip()
            
            if not query:
                continue
                
            if query.lower() in ['exit', 'quit']:
                print("\nShutting down... Goodbye!")
                break
            
            print("-" * 40)
            answer, sources = engine.research(query)
            
            print("\nANSWER:")
            print(answer)
            
            if sources:
                print("\nSOURCES:")
                for i, s in enumerate(sources):
                    print(f"[{i+1}] {s['title']} - {s['link']}")
            
            print("-" * 40 + "\n")
            
        except KeyboardInterrupt:
            print("\n\nShutting down... Goodbye!")
            break
        except Exception as e:
            print(f"\n[ERROR] An unexpected error occurred: {e}\n")

if __name__ == "__main__":
    main()
