import json
import os
from typing import Optional, Dict, List
from playwright.sync_api import Playwright, Browser, BrowserContext, Page, sync_playwright


class BrowserManager:
    def __init__(
        self,
        headless: bool = False,
        slow_mo: int = 0,
        cookie_path: str = "cookies.json"
    ):
        self.headless = headless
        self.slow_mo = slow_mo
        self.cookie_path = cookie_path
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def start(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo,
            args=[
                "--start-maximized",
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--allow-running-insecure-content"
            ]
        )
        self.context = self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.page = self.context.new_page()
        self.page.set_default_timeout(30000)
        return self

    def stop(self):
        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def save_cookies(self):
        if self.context:
            cookies = self.context.cookies()
            os.makedirs(os.path.dirname(self.cookie_path) or ".", exist_ok=True)
            with open(self.cookie_path, "w", encoding="utf-8") as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)

    def load_cookies(self):
        if self.context and os.path.exists(self.cookie_path):
            with open(self.cookie_path, "r", encoding="utf-8") as f:
                cookies = json.load(f)
            self.context.add_cookies(cookies)

    def go_to(self, url: str):
        if self.page:
            self.page.goto(url)

    def wait_for_navigation(self, timeout: int = 30000):
        if self.page:
            self.page.wait_for_load_state("networkidle", timeout=timeout)

    def wait_for_element(self, selector: str, timeout: int = 30000):
        if self.page:
            return self.page.wait_for_selector(selector, timeout=timeout)

    def click(self, selector: str):
        if self.page:
            self.page.click(selector)

    def type(self, selector: str, text: str):
        if self.page:
            self.page.type(selector, text)

    def get_text(self, selector: str) -> str:
        if self.page:
            element = self.page.query_selector(selector)
            return element.text_content() if element else ""

    def take_screenshot(self, path: str):
        if self.page:
            self.page.screenshot(path=path, full_page=True)

    def execute_script(self, script: str, *args):
        if self.page:
            return self.page.evaluate(script, *args)