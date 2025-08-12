#!/usr/bin/env python3

"""
Xiaohongshu Account Manager
Manages multiple Xiaohongshu accounts with separate Chrome profiles.
This script is now self-contained and includes all browser automation logic.
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
import time
import random
import traceback

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys

from config import settings


# ==============================================================================
# BROWSER AUTOMATION LOGIC
# ==============================================================================

def sanitize_for_chromedriver(text: str) -> str:
    """Removes non-BMP characters that crash ChromeDriver on Windows."""
    return "".join(c for c in text if c <= '\uFFFF')


def setup_browser(headless=False, user_data_dir=None):
    """Setup Chrome browser with anti-detection settings"""
    print("Setting up browser...")
    options = Options()
    if user_data_dir:
        expanded_path = Path(user_data_dir).expanduser().absolute()
        expanded_path.mkdir(parents=True, exist_ok=True)
        options.add_argument(f"--user-data-dir={expanded_path}")
        print(f"Using profile directory: {expanded_path}")
    if headless:
        options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--window-size=1366,788")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    print("Browser setup complete")
    return driver


def human_delay(min_sec=1, max_sec=3):
    """Add human-like random delays"""
    time.sleep(random.uniform(min_sec, max_sec))


def dismiss_modals(driver):
    """Try to dismiss any popups or overlays."""
    print("Dismissing any popups...")
    try:
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        time.sleep(2)  # Give modal time to close
        print("   Attempted to dismiss with ESC key.")
    except Exception:
        pass


def check_login_and_navigate(driver):
    """Check login status and navigate to the creator page."""
    print("Navigating directly to creator page...")
    driver.get("https://creator.xiaohongshu.com/publish/publish?source=official")
    time.sleep(8)  # Increased wait for page load
    dismiss_modals(driver)
    print("Checking Creator Platform login status...")
    on_login_page = any(driver.find_elements(By.XPATH, indicator) for indicator in
                        ["//input[contains(@placeholder, '手机号')]", "//button[contains(text(), '登录')]"])
    if on_login_page:
        print("Please complete the Creator Platform login in the browser.")
        input("Press Enter after you are logged in and see the publishing interface...")
        time.sleep(3)
    else:
        print("Already logged into Creator Platform.")
    print("   Verifying access to posting interface...")
    try:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(), '发布笔记') or contains(text(), '添加图片') or @type='file']")))
        print("Successfully accessed posting interface!")
        time.sleep(3)  # Pause after verification
        return True
    except TimeoutException:
        print("Could not verify access to posting interface after waiting.")
        return False


def switch_to_graphic_tab(driver):
    """Switch to the graphic tab and verify the switch."""
    print("Switching to graphic tab...")
    try:
        wait = WebDriverWait(driver, 10)
        tab_xpath = "//span[text()='上传图文']/parent::div[contains(@class, 'creator-tab')]"
        parent_div = wait.until(EC.presence_of_element_located((By.XPATH, tab_xpath)))
        if "active" in parent_div.get_attribute("class"):
            print("Already on graphic tab.")
            time.sleep(3)  # Pause even if already on tab
            return True
        print("   Scrolling tab into view and clicking...")
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", parent_div)
        time.sleep(2)
        try:
            parent_div.click()
        except Exception:
            driver.execute_script("arguments[0].click();", parent_div)
        print("   Verifying tab switch...")
        time.sleep(3)  # Increased pause for tab to become active
        refreshed_div = driver.find_element(By.XPATH, tab_xpath)
        if "active" in refreshed_div.get_attribute("class"):
            print("Tab switch successful and verified!")
            time.sleep(3)  # Pause after successful switch
            return True
        else:
            print("Verification failed, but proceeding as the click was sent.")
            return True
    except Exception as e:
        print(f"An unexpected error occurred while switching tabs: {e}")
        return False


def upload_images(driver, image_paths):
    """Upload images with a robust strategy."""
    print(f"Uploading {len(image_paths)} image(s)...")
    abs_paths = [str(Path(p).absolute()) for p in image_paths]
    if not switch_to_graphic_tab(driver):
        return False
    try:
        file_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']")))
        file_input.send_keys('\n'.join(abs_paths))
        print("Image file path(s) sent to input.")
        print("   Confirming upload by waiting for title field to be ready...")
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='填写标题']")))
        print("Upload confirmed! Title field is now available.")
        time.sleep(3)  # Pause after upload confirmation
        return True
    except TimeoutException:
        print("Upload timed out. The title field did not become available after upload.")
        return False
    except Exception as e:
        print(f"Image upload failed: {e}")
        return False


def fill_content(driver, title, description):
    """Fill in the post content with human-like typing."""
    print("Filling in post content...")
    try:
        # Sanitize text to remove characters that crash ChromeDriver
        safe_title = sanitize_for_chromedriver(title)
        safe_description = sanitize_for_chromedriver(description)

        if title != safe_title:
            print("   Sanitized title to remove special characters.")
        if description != safe_description:
            print("   Sanitized description to remove special characters.")

        # --- Fill Title ---
        title_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='填写标题']"))
        )
        for char in safe_title:
            title_input.send_keys(char)
            time.sleep(random.uniform(0.03, 0.08))
        print("Title filled.")

        print("   Pausing for UI to stabilize after filling title...")
        time.sleep(3)

        # --- Fill Description ---
        desc_editor = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".ql-editor, [contenteditable='true']"))
        )

        print("   Scrolling to and clicking description editor...")
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", desc_editor)
        time.sleep(1)

        print("   Pausing for 3 seconds before clicking description box...")
        time.sleep(3)

        desc_editor.click()

        print("   Pausing for 2 seconds for editor to initialize...")
        time.sleep(2)

        print("   Typing description with periodic pauses...")
        last_pause_time = time.time()
        for char in safe_description:
            desc_editor.send_keys(char)
            time.sleep(random.uniform(0.02, 0.05))
            if time.time() - last_pause_time > 2:
                print("      ...pausing...")
                time.sleep(random.uniform(2, 3))
                last_pause_time = time.time()

        print("Description filled.")

        print("   Pausing for UI to stabilize after filling description...")
        time.sleep(3)

        return True
    except Exception as e:
        print(f"Failed to fill content: {e}")
        driver.save_screenshot("fill_content_error.png")
        print("   Screenshot of the error page saved as fill_content_error.png")
        return False


def publish_post(driver):
    """Publish the post with robust verification."""
    print("Publishing post...")
    try:
        publish_button_xpath = "//button[.//span[text()='发布']]"
        print("   Waiting for the publish button to be clickable...")
        publish_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, publish_button_xpath))
        )
        print("   Scrolling to the publish button...")
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", publish_button)
        time.sleep(1)
        print("   Clicking publish button using JavaScript...")
        driver.execute_script("arguments[0].click();", publish_button)
        print("Publish button clicked!")

        print("   Waiting for '发布成功' (Publish Successful) popup...")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '发布成功')]"))
        )
        print("Post successful confirmation detected!")

        print("   Pausing for 5 seconds to observe the success message...")
        time.sleep(5)

        return True
    except TimeoutException:
        print("Publishing failed. Did not see a '发布成功' (Publish Successful) confirmation.")
        driver.save_screenshot("publish_error_screenshot.png")
        print("   Screenshot of the error page saved as publish_error_screenshot.png")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during publish: {e}")
        driver.save_screenshot("publish_error_screenshot.png")
        print("   Screenshot of the error page saved as publish_error_screenshot.png")
        return False


# ==============================================================================
# ACCOUNT MANAGER CLASS
# ==============================================================================

class XiaohongshuAccountManager:
    def __init__(self):
        self.accounts = settings.xhs_accounts
        self.default_account = settings.xhs_default_account

    def list_accounts(self):
        """List all configured accounts and their status"""
        print("Xiaohongshu Accounts Configuration:")
        print("=" * 60)
        for account_id, account_info in self.accounts.items():
            status = "ENABLED" if account_info.get("enabled", False) else "DISABLED"
            auto_marker = " (AUTO-POSTING)" if account_id == self.default_account else " (MANUAL)"
            print(f"\nAccount: {account_id}{auto_marker}")
            print(f"   Name: {account_info['name']}")
            print(f"   Status: {status}")
            print(f"   Profile: {account_info['chrome_profile']}")
            print(f"   Description: {account_info['description']}")
            profile_path = Path(account_info['chrome_profile']).expanduser()
            if profile_path.exists():
                print(f"   Profile Status: Exists ({profile_path})")
            else:
                print(f"   Profile Status: Not created yet")
        print(f"\nAutomation: Always uses '{self.default_account}' account for auto-posting")

    def get_account_info(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get account information by ID"""
        if account_id not in self.accounts:
            print(f"Account '{account_id}' not found in configuration")
            return None
        account_info = self.accounts[account_id]
        if not account_info.get("enabled", False):
            print(f"Account '{account_id}' is disabled")
            return None
        return account_info

    def setup_account_profile(self, account_id: str) -> bool:
        """Setup Chrome profile directory for an account"""
        account_info = self.get_account_info(account_id)
        if not account_info: return False
        profile_path = Path(account_info['chrome_profile']).expanduser()
        profile_path.mkdir(parents=True, exist_ok=True)
        print(f"Created/verified profile directory: {profile_path}")
        return True

    def login_account(self, account_id: str) -> bool:
        """Login to a specific account"""
        print(f"Logging into account: {account_id}")
        account_info = self.get_account_info(account_id)
        if not account_info or not self.setup_account_profile(account_id):
            return False
        driver = setup_browser(headless=False, user_data_dir=account_info['chrome_profile'])
        try:
            if check_login_and_navigate(driver):
                print(f"Login successful for account: {account_id}")
                return True
            else:
                print(f"Login failed for account: {account_id}")
                return False
        except Exception as e:
            print(f"Error during login: {e}")
            return False
        finally:
            print("Closing browser...")
            driver.quit()

    def post_with_account(self, account_id: str, title: str, description: str, image_paths: list) -> bool:
        """Post content using a specific account"""
        print(f"Posting with account: {account_id}")
        account_info = self.get_account_info(account_id)
        if not account_info or not self.setup_account_profile(account_id):
            return False
        driver = setup_browser(headless=False, user_data_dir=account_info['chrome_profile'])
        try:
            print(f"Starting Xiaohongshu automation with account: {account_info['name']}")
            if not check_login_and_navigate(driver):
                return False
            if not upload_images(driver, image_paths):
                return False
            if not fill_content(driver, title, description):
                return False
            if not publish_post(driver):
                return False

            print(f"Post published successfully with account: {account_id}!")
            return True
        except Exception as e:
            print(f"Error during posting: {e}", file=sys.stderr)
            return False
        finally:
            print("Closing browser...")
            driver.quit()


def main():
    parser = argparse.ArgumentParser(description="Xiaohongshu Account Manager")
    parser.add_argument("--account", help="Account ID to use (auto/manual)")
    parser.add_argument("--action", choices=["login", "post"], help="Action to perform")
    parser.add_argument("--title", help="Post title (for posting)")
    parser.add_argument("--desc", help="Post description (for posting)")
    parser.add_argument("--images", nargs="+", type=Path, help="Image files (for posting)")
    parser.add_argument("--list-accounts", action="store_true", help="List all configured accounts")

    args = parser.parse_args()
    manager = XiaohongshuAccountManager()

    if args.list_accounts:
        manager.list_accounts()
        return
    if not args.account or not args.action:
        print("Please specify an account and an action.", file=sys.stderr)
        return

    if args.action == "login":
        success = manager.login_account(args.account)
        sys.exit(0 if success else 1)
    elif args.action == "post":
        if not all([args.title, args.desc, args.images]):
            print("For posting, please provide --title, --desc, and --images", file=sys.stderr)
            sys.exit(1)

        missing_files = [f for f in args.images if not f.exists()]
        if missing_files:
            print("Missing image files:", file=sys.stderr)
            for f in missing_files: print(f"   {f}", file=sys.stderr)
            sys.exit(1)

        success = manager.post_with_account(args.account, args.title, args.desc, args.images)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        with open("xhs_manager_crash.log", "a", encoding="utf-8") as f:
            f.write(f"--- CRASH at {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            f.write(str(e) + "\n")
            f.write(traceback.format_exc() + "\n")
        sys.exit(1)
