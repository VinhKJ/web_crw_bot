"""
scenario_runner.py
------------------

Defines the ScenarioRunner class responsible for executing a series of
actions against a web page using Selenium. Each action is represented
as a dictionary containing a ``type`` and associated parameters. The
runner supports navigation, clicking, typing, key presses, scrolling,
waiting and data extraction. Logs are emitted via callbacks to allow
integration with a GUI.

Example action specification::

    {
        "type": "click",
        "selector": "button.submit",
        "description": "Click the submit button"
    }

The runner is designed to be used from a background thread to
prevent blocking the GUI event loop. It accepts optional callbacks
for logging and for delivering extracted data to the caller.
"""

from __future__ import annotations

import time
from typing import List, Dict, Callable, Any, Optional

try:
    from selenium import webdriver  # type: ignore
    from selenium.webdriver.common.by import By  # type: ignore
    from selenium.webdriver.common.keys import Keys  # type: ignore
    from selenium.webdriver.chrome.service import Service as ChromeService  # type: ignore
    from selenium.webdriver.chrome.options import Options as ChromeOptions  # type: ignore
except ImportError:
    webdriver = None  # type: ignore
    By = None  # type: ignore
    Keys = None  # type: ignore

Action = Dict[str, Any]


class ScenarioRunner:
    """
    Executes a list of actions sequentially using Selenium.

    Parameters
    ----------
    headless : bool
        Whether to run the browser in headless mode. Defaults to True.
    """

    def __init__(self, headless: bool = True) -> None:
        if webdriver is None:
            raise RuntimeError(
                "selenium is not installed. Please install it to use ScenarioRunner."
            )
        options = ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        # Create a Chrome service; this will look for chromedriver on PATH
        self.driver = webdriver.Chrome(options=options)
        self._stopped = False

    def stop(self) -> None:
        """Signal the runner to stop gracefully."""
        self._stopped = True

    def close(self) -> None:
        """Clean up and close the browser."""
        try:
            self.driver.quit()
        except Exception:
            pass

    def run(
        self,
        actions: List[Action],
        log_callback: Optional[Callable[[str], None]] = None,
        result_callback: Optional[Callable[[List[Dict[str, str]]], None]] = None,
    ) -> None:
        """
        Execute each action in the provided list. If a log_callback is
        provided, messages describing the progress will be sent there.
        When an 'extract' action is executed, the extracted data will be
        passed to result_callback.

        Parameters
        ----------
        actions : List[Action]
            List of action dictionaries.
        log_callback : Callable[[str], None], optional
            Function to call with log messages.
        result_callback : Callable[[List[Dict[str, str]]], None], optional
            Function to call with extracted data when extraction occurs.
        """

        def log(msg: str) -> None:
            if log_callback:
                log_callback(msg)
        
        for idx, action in enumerate(actions, start=1):
            if self._stopped:
                log("Scenario interrupted by user.")
                break
            action_type = action.get("type")
            description = action.get("description", action_type)
            log(f"({idx}/{len(actions)}) Executing: {description}")
            try:
                if action_type == "open_url":
                    url = action.get("url")
                    if url:
                        self.driver.get(url)
                        log(f"Navigated to {url}")
                elif action_type == "click":
                    selector = action.get("selector")
                    if selector:
                        elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        elem.click()
                        log(f"Clicked element {selector}")
                elif action_type == "type":
                    selector = action.get("selector")
                    text = action.get("text", "")
                    if selector:
                        elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        elem.clear()
                        elem.send_keys(text)
                        log(f"Typed text into {selector}")
                elif action_type == "keypress":
                    key = action.get("key")
                    # send key to active element or body
                    body = self.driver.switch_to.active_element
                    if key and body:
                        # Map friendly names to Keys constants if provided
                        key_lower = str(key).lower()
                        key_attr = None
                        # Map some common keys
                        mapping = {
                            "enter": Keys.ENTER,
                            "tab": Keys.TAB,
                            "escape": Keys.ESCAPE,
                            "backspace": Keys.BACKSPACE,
                        }
                        key_attr = mapping.get(key_lower, key)
                        body.send_keys(key_attr)
                        log(f"Sent key '{key}'")
                elif action_type == "scroll":
                    direction = action.get("direction", "down").lower()
                    amount = action.get("amount", 500)
                    # Scroll by amount pixels; negative for up
                    delta = int(amount) if direction == "down" else -int(amount)
                    self.driver.execute_script("window.scrollBy(0, arguments[0]);", delta)
                    log(f"Scrolled {'down' if delta > 0 else 'up'} by {abs(delta)} pixels")
                elif action_type == "wait":
                    seconds = action.get("seconds", 1)
                    time.sleep(float(seconds))
                    log(f"Waited for {seconds} seconds")
                elif action_type == "extract":
                    selector = action.get("selector")
                    all_elements = action.get("all", True)
                    if selector:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        results: List[Dict[str, str]] = []
                        for element in elements:
                            text = element.text
                            results.append({"text": text})
                        log(f"Extracted {len(results)} elements using {selector}")
                        if result_callback:
                            result_callback(results)
                else:
                    log(f"Unknown action type: {action_type}")
            except Exception as e:
                log(f"Error executing action '{description}': {e}")
        log("Scenario completed")