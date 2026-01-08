from playwright.sync_api import sync_playwright
import time

SERVER_URL = "http://localhost:5000/"


def test_send_and_retry():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(SERVER_URL, wait_until="networkidle")

        # Fill the input and send
        page.fill('#inp', 'E2E test message')
        page.click('#send-btn')

        # Wait for loader to appear and AI reply to show
        page.wait_for_selector('.msg-row.ai', timeout=15000)
        ai_msgs = page.locator('.msg-row.ai .msg-bubble')
        assert ai_msgs.count() >= 1

        # Click 'Retry' in the most recent AI message actions
        retry_btn = page.locator('.msg-row.ai').last.locator('.msg-actions button:has-text("Retry")')
        retry_btn.click()

        # Input should be prefilled with the last user message
        input_val = page.input_value('#inp')
        assert 'E2E test message' in input_val

        browser.close()
