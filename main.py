"""
VYOM VISUALIZER (Heavy)
Restored original visualization logic.
"""
import asyncio
import pygame
import numpy as np
import random
from pygame.math import Vector2
from scipy import interpolate

# Only import playwright if needed, or assume heavy env
# For simplicity, we make this runnable even in light mode but without browser
try:
    from playwright.async_api import async_playwright
    HAS_BROWSER = True
except ImportError:
    HAS_BROWSER = False

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

class AgentState:
    def __init__(self):
        self.position = Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.target_position = Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.logs = []
        self.data_points = [] 
        self.running = True
        self.trigger_action = False 
        self.status = "IDLE"

async def run_browser(state: AgentState):
    if not HAS_BROWSER:
        state.logs.append("Browser Engine Missing (Light Mode?)")
        return

    print("🌐 Browser Engine Starting...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        try:
            await page.goto("https://google.com")
            while state.running:
                if state.trigger_action:
                    state.status = "SCRAPING"
                    await page.reload()
                    state.trigger_action = False
                    new_x = random.randint(50, SCREEN_WIDTH - 50)
                    new_y = random.randint(50, SCREEN_HEIGHT - 50)
                    state.target_position = Vector2(new_x, new_y)
                    state.data_points.append((new_x, new_y))
                    state.status = "IDLE"
                await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Browser Error: {e}")
        finally:
            await browser.close()

async def run_visualizer(state: AgentState):
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    
    while state.running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: state.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE: state.trigger_action = True

        if state.position != state.target_position:
            state.position.move_towards_ip(state.target_position, 5.0)

        screen.fill((10, 10, 20))
        pygame.draw.circle(screen, (0, 255, 200), (int(state.position.x), int(state.position.y)), 15)
        pygame.display.flip()
        await asyncio.sleep(0)
        clock.tick(60)
    pygame.quit()

async def main():
    state = AgentState()
    await asyncio.gather(run_browser(state), run_visualizer(state))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Execution stopped by user.")
    except Exception as e:
        print(f"❌ CRITICAL ERROR in main.py: {e}")
        import traceback
        traceback.print_exc()
