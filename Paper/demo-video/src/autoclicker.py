#!/usr/bin/env python3
"""
Lars Demo Video - Autoclicker
==============================
Automatisiert Browser-Interaktionen mit visuellen Highlights.

Features:
- Selenium WebDriver für präzise Element-Interaktion
- Visuelle Cursor-Highlights für das Video
- Wartet auf UI-Elemente (nicht nur Zeit)
- Unterstützt komplexe Interaktionen (Drag&Drop, Uploads)
"""

import time
import os
from typing import Optional, Tuple
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException

try:
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    print("Installing webdriver-manager...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "webdriver-manager"])
    from webdriver_manager.chrome import ChromeDriverManager


class AutoClicker:
    """
    Browser-Automatisierung mit visuellen Effekten für Demo-Videos.
    """

    # CSS für visuelle Highlights
    HIGHLIGHT_CSS = """
    .llars-demo-highlight {
        outline: 3px solid #FF5722 !important;
        outline-offset: 2px !important;
        animation: llars-pulse 0.5s ease-in-out infinite alternate !important;
    }
    @keyframes llars-pulse {
        from { outline-color: #FF5722; box-shadow: 0 0 10px #FF5722; }
        to { outline-color: #FFC107; box-shadow: 0 0 20px #FFC107; }
    }
    .llars-demo-cursor {
        position: fixed !important;
        width: 20px !important;
        height: 20px !important;
        border-radius: 50% !important;
        background: rgba(255, 87, 34, 0.7) !important;
        pointer-events: none !important;
        z-index: 999999 !important;
        transition: all 0.3s ease !important;
    }
    .llars-demo-cursor.clicking {
        transform: scale(1.5) !important;
        background: rgba(255, 193, 7, 0.9) !important;
    }
    """

    def __init__(
        self,
        browser_url: str = "http://localhost:55080",
        highlight_clicks: bool = True,
        typing_delay_ms: int = 50,
        headless: bool = False
    ):
        self.browser_url = browser_url
        self.highlight_clicks = highlight_clicks
        self.typing_delay = typing_delay_ms / 1000
        self.driver = None
        self.windows = {}  # Für Multi-Window Support

        self._setup_driver(headless)
        self._inject_highlight_styles()

    def _setup_driver(self, headless: bool):
        """Initialisiert Chrome WebDriver"""
        options = Options()

        if headless:
            options.add_argument('--headless')

        # Fenstergröße für Video
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')

        # Performance
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        # Disable automation indicators
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)

        # Hauptfenster registrieren
        self.windows[1] = self.driver.current_window_handle

        print(f"✓ Chrome gestartet: {self.browser_url}")

    def _inject_highlight_styles(self):
        """Injiziert CSS für visuelle Effekte"""
        script = f"""
        if (!document.getElementById('llars-demo-styles')) {{
            var style = document.createElement('style');
            style.id = 'llars-demo-styles';
            style.textContent = `{self.HIGHLIGHT_CSS}`;
            document.head.appendChild(style);
        }}
        """
        try:
            self.driver.execute_script(script)
        except Exception:
            pass  # Ignorieren wenn Seite noch nicht geladen

    def navigate(self, url: str, wait_for: Optional[str] = None):
        """Navigiert zu einer URL"""
        full_url = url if url.startswith('http') else f"{self.browser_url}{url}"
        print(f"🌐 Navigiere zu: {full_url}")

        self.driver.get(full_url)
        self._inject_highlight_styles()

        if wait_for:
            self.wait_for_element(wait_for)

        time.sleep(0.5)  # Kurze Pause für Rendering

    def wait_for_element(self, selector: str, timeout: float = 10) -> bool:
        """Wartet auf ein Element"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            return True
        except TimeoutException:
            print(f"⚠️ Timeout beim Warten auf: {selector}")
            return False

    def find_element(self, selector: str):
        """Findet ein Element mit CSS-Selector"""
        try:
            return self.driver.find_element(By.CSS_SELECTOR, selector)
        except NoSuchElementException:
            print(f"⚠️ Element nicht gefunden: {selector}")
            return None

    def highlight(self, selector: str, duration: float = 2.0):
        """Hebt ein Element visuell hervor"""
        element = self.find_element(selector)
        if not element:
            return

        # Highlight-Klasse hinzufügen
        self.driver.execute_script(
            "arguments[0].classList.add('llars-demo-highlight')",
            element
        )

        # Zum Element scrollen
        self.driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'})",
            element
        )

        time.sleep(duration)

        # Highlight entfernen
        self.driver.execute_script(
            "arguments[0].classList.remove('llars-demo-highlight')",
            element
        )

    def _show_cursor_at(self, x: int, y: int, clicking: bool = False):
        """Zeigt visuellen Cursor an Position"""
        script = f"""
        var cursor = document.getElementById('llars-demo-cursor');
        if (!cursor) {{
            cursor = document.createElement('div');
            cursor.id = 'llars-demo-cursor';
            cursor.className = 'llars-demo-cursor';
            document.body.appendChild(cursor);
        }}
        cursor.style.left = '{x}px';
        cursor.style.top = '{y}px';
        cursor.classList.{'add' if clicking else 'remove'}('clicking');
        """
        self.driver.execute_script(script)

    def click(self, selector: str, wait_for: Optional[str] = None):
        """Klickt auf ein Element mit visuellem Feedback"""
        element = self.find_element(selector)
        if not element:
            return

        # Zum Element scrollen
        self.driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'})",
            element
        )
        time.sleep(0.3)

        # Element-Position für Cursor
        location = element.location
        size = element.size
        center_x = location['x'] + size['width'] // 2
        center_y = location['y'] + size['height'] // 2

        if self.highlight_clicks:
            # Cursor bewegen
            self._show_cursor_at(center_x, center_y)
            time.sleep(0.2)

            # Highlight
            self.driver.execute_script(
                "arguments[0].classList.add('llars-demo-highlight')",
                element
            )
            time.sleep(0.1)

            # Klick-Animation
            self._show_cursor_at(center_x, center_y, clicking=True)

        # Tatsächlicher Klick
        try:
            element.click()
        except Exception:
            # Fallback: JavaScript-Klick
            self.driver.execute_script("arguments[0].click()", element)

        if self.highlight_clicks:
            time.sleep(0.2)
            self._show_cursor_at(center_x, center_y, clicking=False)

            # Highlight entfernen
            try:
                self.driver.execute_script(
                    "arguments[0].classList.remove('llars-demo-highlight')",
                    element
                )
            except Exception:
                pass

        print(f"🖱️ Click: {selector}")

        if wait_for:
            self.wait_for_element(wait_for)

        time.sleep(0.3)

    def type_text(self, selector: str, text: str, delay_ms: int = 50):
        """Tippt Text mit realistischer Verzögerung"""
        element = self.find_element(selector)
        if not element:
            return

        # Focus
        element.click()
        time.sleep(0.2)

        # Zeichen für Zeichen tippen
        for char in text:
            element.send_keys(char)
            time.sleep(delay_ms / 1000)

        print(f"⌨️ Type: {text[:30]}...")

    def clear(self, selector: str):
        """Löscht Inhalt eines Input-Felds"""
        element = self.find_element(selector)
        if element:
            element.clear()
            print(f"🗑️ Clear: {selector}")

    def drag_drop(self, source_selector: str, target_selector: str):
        """Drag & Drop zwischen zwei Elementen"""
        source = self.find_element(source_selector)
        target = self.find_element(target_selector)

        if not source or not target:
            return

        if self.highlight_clicks:
            self.highlight(source_selector, 0.5)

        actions = ActionChains(self.driver)
        actions.drag_and_drop(source, target).perform()

        if self.highlight_clicks:
            self.highlight(target_selector, 0.5)

        print(f"↔️ Drag: {source_selector} → {target_selector}")
        time.sleep(0.5)

    def scroll(self, selector: str, direction: str = "down", amount: int = 300):
        """Scrollt innerhalb eines Elements"""
        element = self.find_element(selector)
        if not element:
            # Fallback: Ganzes Fenster scrollen
            scroll_amount = amount if direction == "down" else -amount
            self.driver.execute_script(f"window.scrollBy(0, {scroll_amount})")
        else:
            scroll_amount = amount if direction == "down" else -amount
            self.driver.execute_script(
                f"arguments[0].scrollBy(0, {scroll_amount})",
                element
            )

        print(f"📜 Scroll {direction}: {amount}px")
        time.sleep(0.3)

    def upload_file(self, selector: str, file_path: str):
        """Lädt eine Datei hoch"""
        # Relativen Pfad auflösen
        abs_path = str(Path(file_path).resolve())

        element = self.find_element(selector)
        if element:
            element.send_keys(abs_path)
            print(f"📁 Upload: {file_path}")
            time.sleep(1)

    def switch_window(self, window_number: int):
        """Wechselt zwischen Browser-Fenstern"""
        if window_number not in self.windows:
            # Neues Fenster öffnen
            self.driver.execute_script("window.open('');")
            self.windows[window_number] = self.driver.window_handles[-1]

        self.driver.switch_to.window(self.windows[window_number])
        self._inject_highlight_styles()
        print(f"🪟 Window: {window_number}")

    def execute_script(self, script: str):
        """Führt JavaScript aus"""
        return self.driver.execute_script(script)

    def screenshot(self, path: str):
        """Speichert Screenshot"""
        self.driver.save_screenshot(path)
        print(f"📸 Screenshot: {path}")

    def close(self):
        """Schließt den Browser"""
        if self.driver:
            self.driver.quit()
            print("✓ Browser geschlossen")


# Test
if __name__ == '__main__':
    print("Testing AutoClicker...")

    clicker = AutoClicker(browser_url="http://localhost:55080")

    try:
        # Navigation
        clicker.navigate("/")
        time.sleep(2)

        # Screenshot
        clicker.screenshot("test_screenshot.png")

    finally:
        clicker.close()
