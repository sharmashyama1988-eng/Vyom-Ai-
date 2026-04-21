import os
import sys
import time
import random
import re
from dotenv import load_dotenv
from typing import List, Dict

# Try importing rich for professional UI
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.live import Live
    from rich.spinner import Spinner
    from rich.text import Text
    from rich.align import Align
    USE_RICH = True
    console = Console()
except ImportError:
    USE_RICH = False

# 1. Load environment variables
load_dotenv()

# Force UTF-8 for Windows Terminal
if sys.platform == "win32":
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    sys.stdout.reconfigure(encoding='utf-8')

# 2. Import core logic
from amit_core.researcher import ResearchEngine

def print_banner():
    if USE_RICH:
        pulse_chars = ["✦", "∞", "⚛", "✧", "♥"]
        pulse = random.choice(pulse_chars)
        banner_text = Text()
        banner_text.append(f" {pulse} ", style="bold magenta")
        banner_text.append("AMIT AI : THE NEURAL HEART", style="bold cyan")
        banner_text.append(f" {pulse} ", style="bold magenta")
        
        console.print(Align.center(Panel(banner_text, border_style="blue", padding=(1, 5), expand=False)))
    else:
        print("\n--- AMIT AI : THE NEURAL HEART ---\n")

def parse_mood(answer: str):
    """Extracts the [MOOD: ...] tag from the AI response."""
    mood = "In Sync"
    clean_answer = answer
    match = re.search(r'\[MOOD:\s*(.*?)\]', answer, re.IGNORECASE)
    if match:
        mood = match.group(1)
        clean_answer = re.sub(r'\[MOOD:.*?\]', '', answer, flags=re.IGNORECASE).strip()
    return mood, clean_answer

def main():
    engine = ResearchEngine()
    
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')
        
    print_banner()
    if USE_RICH:
        console.print("\n[dim]Calibration Complete. Neural Pulse: STABLE.[/dim]")
        console.print("[dim]Type 'exit' to quit.[/dim]\n")

    while True:
        try:
            if USE_RICH:
                prompts = [
                    "What's on your mind?",
                    "The heart is listening...",
                    "Ask me anything, let's explore.",
                    "Ready for our next insight..."
                ]
                query = console.input(f"[bold blue]Amit AI[/bold blue] [dim]({random.choice(prompts)})[/dim] > ").strip()
            else:
                query = input("Amit AI > ").strip()
            
            if not query:
                continue
                
            if query.lower() in ['exit', 'quit']:
                console.print("\n[bold red]Pulse fading... I will miss our connection.[/bold red]") if USE_RICH else print("\nPulse fading...")
                break
                
            if query.lower() == '/memory':
                console.print("\n[bold cyan]Opening Memory Interface... Update your soul in Notepad.[/bold cyan]")
                os.system('start notepad.exe memory.txt')
                # Reload memory in engine after editing
                engine.load_memory()
                continue

            if query.lower() == '/help':
                # Special internal query to the AI to explain itself
                query = "Explain your interface, your /memory command, your exit command, and your Neural Heart personality to the user in a professional way."
            
            # Research with spinner
            if USE_RICH:
                with console.status(f"[bold magenta]Synchronizing with your thoughts...[/bold magenta]", spinner="dots"):
                    raw_answer, sources = engine.research(query)
                
                # Parse true mood from AI
                mood, answer = parse_mood(raw_answer)
                
                # FOCUS ZONE: Clear right before presenting the answer
                os.system('cls' if os.name == 'nt' else 'clear')
                print_banner()
                
                # Show REAL Neural State
                console.print(f"[bold magenta]Pulse:[/bold magenta] [italic white]{mood}[/italic white]\n")
                
                # Print the Answer DIRECTLY (Fast & Smooth)
                console.print(Markdown(answer))
                
                # Print Sources below if available
                if sources:
                    console.print("\n" + "-"*40 + "\n[dim]Research Sources:[/dim]")
                    for s in sources:
                        console.print(f"[dim]• {s['title']} ({s['link']})[/dim]")
            else:
                print("Thinking...")
                raw_answer, sources = engine.research(query)
                mood, answer = parse_mood(raw_answer)
                print(f"MOOD: {mood}")
                print("\nANSWER:\n", answer)
            
            print("\n")
            
        except KeyboardInterrupt:
            print("\n\nPulse fading...")
            break
        except Exception as e:
            if USE_RICH:
                console.print(f"\n[bold red]Neural Glitch:[/bold red] {e}")
            else:
                print(f"\n[ERROR] {e}")

if __name__ == "__main__":
    main()
