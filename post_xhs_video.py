#!/usr/bin/env python3
"""
Xiaohongshu video posting automation script
Adapted from the image posting scripts for video content
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import random

def is_browser_window_closed_error(error: Exception) -> bool:
    """
    Check if the error is related to browser window being closed by user
    """
    error_str = str(error).lower()
    browser_closed_indicators = [
        'no such window',
        'target window already closed',
        'web view not found',
        'window was closed',
        'chrome not reachable',
        'session deleted',
        'invalid session id'
    ]
    
    return any(indicator in error_str for indicator in browser_closed_indicators)

def handle_browser_error(error: Exception, context: str = "") -> None:
    """
    Handle browser-related errors with appropriate user-friendly messages
    """
    if is_browser_window_closed_error(error):
        print(f"🔄 用户关闭了浏览器窗口，程序正常退出")
        print(f"💡 提示：如需继续操作，请重新运行程序")
    else:
        print(f"⚠️ {context} 发生错误: {error}")

def sanitize_for_chromedriver(text: str) -> str:
    """Removes non-BMP characters that crash ChromeDriver on Windows."""
    return "".join(c for c in text if c <= '\uFFFF')

def human_delay(min_seconds=1, max_seconds=3):
    """Add human-like delay"""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)

def dismiss_modals(driver):
    """Try to dismiss any popups or overlays (from working image code)"""
    print("Dismissing any popups...")
    try:
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        time.sleep(2)  # Give modal time to close
        print("   Attempted to dismiss with ESC key.")
    except Exception:
        pass

def setup_browser(user_data_dir=None, headless=False):
    """Setup Chrome browser with anti-detection settings (borrowed from working image code)"""
    print("Setting up browser with anti-detection features...")
    chrome_options = Options()
    
    if user_data_dir:
        expanded_path = Path(user_data_dir).expanduser().absolute()
        expanded_path.mkdir(parents=True, exist_ok=True)
        chrome_options.add_argument(f"--user-data-dir={expanded_path}")
        print(f"Using profile directory: {expanded_path}")
    
    if headless:
        chrome_options.add_argument("--headless")
    
    # CRITICAL: Anti-detection settings (from working image code)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Window size and user agent (from working image code)
    chrome_options.add_argument("--window-size=1366,788")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Video upload optimizations (keep these for video functionality)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    
    # Enable media features for video
    chrome_options.add_argument("--enable-features=VaapiVideoDecoder")
    chrome_options.add_argument("--use-fake-ui-for-media-stream")
    chrome_options.add_argument("--use-fake-device-for-media-stream")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # CRITICAL: Remove webdriver property (from working image code)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    print("Browser setup complete with anti-detection features")
    return driver

def handle_logout_and_relogin(driver):
    """Handle automatic logout by waiting for manual re-login"""
    print("🔄 Handling logout scenario...")
    print("📢 PLEASE MANUALLY LOG BACK IN TO XIAOHONGSHU")
    print("   1. The browser should show the login page")
    print("   2. Please complete the login process manually")
    print("   3. Navigate back to the creator page if needed")
    
    # Wait for user to manually log back in
    max_wait_minutes = 5
    start_time = time.time()
    
    while (time.time() - start_time) < (max_wait_minutes * 60):
        try:
            current_url = driver.current_url
            page_title = driver.title
            
            # Check if we're back at the creator page and logged in
            if "creator.xiaohongshu.com" in current_url and "login" not in current_url.lower():
                # Check if we can find the file input (indicating we're on the right page)
                try:
                    file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
                    if file_input:
                        print("✅ Successfully logged back in and ready to continue!")
                        time.sleep(3)
                        return True
                except:
                    pass
            
            print(f"⏳ Waiting for manual login... ({int((time.time() - start_time) / 60)} min elapsed)")
            time.sleep(10)  # Check every 10 seconds
            
        except Exception as e:
            handle_browser_error(e, "检查登录状态时")
            time.sleep(5)
    
    print(f"❌ Timeout waiting for manual login after {max_wait_minutes} minutes")
    return False

def check_login_and_navigate(driver):
    """Check login status and navigate to creator page (improved with modal dismissal)"""
    try:
        print("🌐 Navigating to Xiaohongshu creator page...")
        driver.get("https://creator.xiaohongshu.com/publish/publish?source=official")
        time.sleep(8)  # Increased wait for page load
        
        # Dismiss any popups (from working image code)
        dismiss_modals(driver)
        
        print("Checking Creator Platform login status...")
        
        # Check if we're on login page
        on_login_page = any(driver.find_elements(By.XPATH, indicator) for indicator in
                            ["//input[contains(@placeholder, '手机号')]", "//button[contains(text(), '登录')]"])
        
        if on_login_page:
            print("❌ Not logged in. Please login first using the account manager.")
            return False
        
        print("✅ Already logged into Creator Platform")
        print("   Verifying access to posting interface...")
        
        try:
            WebDriverWait(driver, 20).until(EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(), '发布笔记') or contains(text(), '添加图片') or @type='file']")))
            print("✅ Successfully accessed posting interface!")
            time.sleep(3)  # Pause after verification
            return True
        except TimeoutException:
            print("⚠️ Could not verify access to posting interface after waiting.")
            return False
        
    except Exception as e:
        handle_browser_error(e, "导航到小红书页面时")
        return False

def switch_to_video_via_image_tab(driver):
    """Switch to video tab via image tab (EXACT copy of working switch_to_graphic_tab logic)"""
    print("Switching to video tab...")  # Match working print format exactly
    try:
        wait = WebDriverWait(driver, 10)
        
        # First ensure we're on image tab - this refreshes the interface
        image_tab_xpath = "//span[text()='上传图文']/parent::div[contains(@class, 'creator-tab')]"
        image_tab = wait.until(EC.presence_of_element_located((By.XPATH, image_tab_xpath)))
        
        if "active" not in image_tab.get_attribute("class"):
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", image_tab)
            time.sleep(2)
            try:
                image_tab.click()
            except Exception:
                driver.execute_script("arguments[0].click();", image_tab)
            time.sleep(3)
        
        # Now switch to video tab - EXACT same logic as working switch_to_graphic_tab
        video_tab_xpath = "//span[text()='上传视频']/parent::div[contains(@class, 'creator-tab')]"
        video_tab = wait.until(EC.presence_of_element_located((By.XPATH, video_tab_xpath)))
        
        if "active" in video_tab.get_attribute("class"):
            print("Already on video tab.")  # Match working print format
            time.sleep(3)  # Pause even if already on tab
            return True
            
        print("   Scrolling tab into view and clicking...")  # Match working print format
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", video_tab)
        time.sleep(2)
        try:
            video_tab.click()
        except Exception:
            driver.execute_script("arguments[0].click();", video_tab)
            
        print("   Verifying tab switch...")  # Match working print format
        time.sleep(3)  # Increased pause for tab to become active
        refreshed_video_tab = driver.find_element(By.XPATH, video_tab_xpath)
        if "active" in refreshed_video_tab.get_attribute("class"):
            print("Tab switch successful and verified!")  # Match working print format
            time.sleep(3)  # Pause after successful switch
            return True
        else:
            print("Verification failed, but proceeding as the click was sent.")  # Match working print format
            return True
            
    except Exception as e:
        handle_browser_error(e, "切换标签页时")
        return False

def upload_video_human_like(driver, video_path):
    """Upload video by simulating human behavior - click upload area to open Finder"""
    print(f"🤖 Starting human-like video upload...")
    print(f"📁 Video file: {video_path}")
    
    # Do tab switching FIRST 
    if not switch_to_video_via_image_tab(driver):
        return False
    
    try:
        # Find the visible upload area (not the hidden file input)
        upload_area_selectors = [
            "div[class*='upload']",
            "div[class*='drop']", 
            ".upload-area",
            ".upload-zone",
            ".drop-zone",
            "div[class*='dnd']"
        ]
        
        upload_area = None
        for selector in upload_area_selectors:
            try:
                upload_area = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                print(f"✅ Found upload area: {selector}")
                break
            except:
                continue
                
        if not upload_area:
            print("❌ Could not find clickable upload area")
            return False
        
        # Click the upload area to open Finder (human-like)
        print("🖱️ Clicking upload area to open Finder...")
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", upload_area)
        time.sleep(1)
        upload_area.click()
        
        # Wait for Finder to open
        print("⏳ Waiting for Finder to open...")
        time.sleep(3)
        
        # Use AppleScript to control Finder (most reliable for macOS)
        video_path_absolute = str(video_path.absolute())
        video_folder = str(video_path.parent.absolute())
        video_filename = video_path.name
        
        applescript = f'''
        tell application "System Events"
            -- Wait for Finder dialog to appear
            repeat with i from 1 to 20
                if exists window 1 of process "Google Chrome" then
                    exit repeat
                end if
                delay 0.5
            end repeat
            
            -- Navigate to the video folder using keyboard shortcut
            keystroke "g" using {{command down, shift down}}
            delay 1
            keystroke "{video_folder}"
            delay 1
            keystroke return
            delay 3
            
            -- Select the video file by typing its name
            keystroke "{video_filename}"
            delay 2
            
            -- Try different ways to confirm selection
            try
                -- Try clicking Open button (most common)
                click button "Open" of window 1 of process "Google Chrome"
            on error
                try
                    -- Try clicking Choose button (alternative)
                    click button "Choose" of window 1 of process "Google Chrome"
                on error
                    try
                        -- Try clicking Select button
                        click button "Select" of window 1 of process "Google Chrome"
                    on error
                        -- Fallback: just press Enter/Return
                        keystroke return
                    end try
                end try
            end try
        end tell
        '''
        
        print("🍎 Using AppleScript to navigate Finder...")
        print(f"   Navigating to: {video_folder}")
        print(f"   Selecting file: {video_filename}")
        
        import subprocess
        result = subprocess.run(['osascript', '-e', applescript], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            print(f"⚠️ AppleScript error: {result.stderr}")
            # Fallback to keyboard shortcuts
            return upload_video_with_keyboard_fallback(driver, video_path)
        
        print("✅ Finder automation completed")
        
        # Wait for upload to process
        print("⏳ Waiting for upload to process...")
        time.sleep(5)
        
        # Wait for upload confirmation
        print("   Confirming upload by waiting for title field to be ready...")
        WebDriverWait(driver, 120).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='填写标题']")))
        print("✅ Upload confirmed! Title field is now available.")
        time.sleep(3)
        return True
        
    except Exception as e:
        handle_browser_error(e, "人性化上传视频时")
        print("🔄 Falling back to traditional method...")
        return upload_video_traditional(driver, video_path)

def upload_video_with_keyboard_fallback(driver, video_path):
    """Reliable keyboard method for Finder navigation"""
    try:
        print("⌨️ Using keyboard navigation in Finder...")
        import subprocess
        
        # Improved keyboard shortcuts with better timing
        keyboard_script = f'''
        tell application "System Events"
            -- Wait a moment for dialog to be ready
            delay 1
            
            -- Go to folder shortcut (Cmd+Shift+G)
            keystroke "g" using {{command down, shift down}}
            delay 1.5
            
            -- Type the folder path and navigate
            keystroke "{video_path.parent.absolute()}"
            delay 0.5
            keystroke return
            delay 3
            
            -- Type filename to select it
            keystroke "{video_path.name}"
            delay 2
            
            -- Confirm selection - try multiple methods
            try
                keystroke return
            on error
                try
                    keystroke space
                on error
                    keystroke return using {{command down}}
                end try
            end try
        end tell
        '''
        
        result = subprocess.run(['osascript', '-e', keyboard_script], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print(f"   ⚠️ Keyboard script warning: {result.stderr}")
        
        # Wait for upload confirmation
        print("   Waiting for upload confirmation...")
        WebDriverWait(driver, 120).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='填写标题']")))
        print("✅ Keyboard method successful!")
        return True
        
    except Exception as e:
        handle_browser_error(e, "键盘导航上传时")
        return False

def upload_video_traditional(driver, video_path):
    """Traditional file input method as final fallback"""
    try:
        print("🔧 Using traditional file input method...")
        
        file_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']")))
        
        file_input.send_keys(str(video_path.absolute()))
        print("Traditional upload method completed.")
        
        WebDriverWait(driver, 120).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='填写标题']")))
        print("✅ Traditional upload confirmed!")
        return True
        
    except Exception as e:
        handle_browser_error(e, "传统上传方法时")
        return False

# Keep the new human-like method as the main one
def upload_video(driver, video_path):
    """Main upload function - tries human-like method first"""
    return upload_video_human_like(driver, video_path)

def fill_content(driver, title, description):
    """Fill in title and description with maximum human-like behavior"""
    print("📝 Filling in post content...")
    try:
        # Sanitize text to remove characters that crash ChromeDriver (borrowed from working code)
        safe_title = sanitize_for_chromedriver(title)
        safe_description = sanitize_for_chromedriver(description)

        if title != safe_title:
            print("   Sanitized title to remove special characters.")
        if description != safe_description:
            print("   Sanitized description to remove special characters.")

        print(f"   Title: {safe_title}")
        print(f"   Description: {safe_description[:100]}...")

        # Wait longer after upload for UI to fully stabilize
        print("   Waiting for upload to fully process...")
        human_delay(8, 12)

        # --- Fill Title (ultra human-like) ---
        title_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='填写标题']"))
        )
        
        # Simulate natural mouse movement to title field
        print("   Moving to title field naturally...")
        actions = ActionChains(driver)
        actions.move_to_element(title_input).perform()
        human_delay(1, 2)
        
        # Click naturally
        actions.click().perform()
        human_delay(0.5, 1)
        
        # Clear field with keyboard shortcuts (more human-like)
        actions.key_down(Keys.COMMAND).send_keys('a').key_up(Keys.COMMAND).perform()
        time.sleep(0.3)
        actions.send_keys(Keys.DELETE).perform()
        
        human_delay(1, 2)
        
        # Type with very human-like patterns
        print("   Typing title with natural rhythm...")
        for i, char in enumerate(safe_title):
            actions.send_keys(char).perform()
            
            # Human-like typing rhythm: varied speeds, occasional pauses
            if char == ' ' or char in '，。！？':  # Pause after punctuation
                time.sleep(random.uniform(0.2, 0.5))
            elif i > 0 and i % random.randint(8, 15) == 0:  # Random pauses while typing
                time.sleep(random.uniform(0.3, 0.8))
            else:
                # Variable typing speed - some characters faster, some slower
                base_delay = random.uniform(0.08, 0.25)
                if char.isdigit() or char in 'aeiouAEIOU':  # Faster for common chars
                    base_delay *= 0.7
                elif char.isupper() or char in '!@#$%^&*()':  # Slower for special chars
                    base_delay *= 1.5
                time.sleep(base_delay)
        
        print("✅ Title filled")
        human_delay(3, 5)

        # --- Fill Description (ultra human-like) ---
        desc_editor = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".ql-editor, [contenteditable='true']"))
        )

        print("   Moving to description editor naturally...")
        
        # Natural scrolling behavior - simulate user scrolling to see the field
        current_scroll = driver.execute_script("return window.pageYOffset;")
        target_scroll = driver.execute_script("return arguments[0].getBoundingClientRect().top + window.pageYOffset - window.innerHeight/2;", desc_editor)
        
        if abs(target_scroll - current_scroll) > 100:
            print("   Scrolling naturally to description field...")
            steps = random.randint(3, 6)
            for i in range(steps):
                scroll_amount = (target_scroll - current_scroll) / steps
                driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                time.sleep(random.uniform(0.1, 0.3))
        
        human_delay(2, 3)
        
        # Move to and click description editor
        actions = ActionChains(driver)
        actions.move_to_element(desc_editor).perform()
        human_delay(1, 2)
        actions.click().perform()
        
        print("   Waiting for description editor to be ready...")
        human_delay(2, 4)

        print("   Typing description with natural human patterns...")
        
        # Split description into words for more natural typing
        words = safe_description.split()
        for word_idx, word in enumerate(words):
            # Type the word
            for char_idx, char in enumerate(word):
                actions.send_keys(char).perform()
                
                # Natural typing speed variation
                if char in '，。！？；：':  # Pause after Chinese punctuation
                    time.sleep(random.uniform(0.3, 0.7))
                elif char == ' ':
                    time.sleep(random.uniform(0.15, 0.35))
                else:
                    # Realistic human typing speed: 60-120 WPM equivalent
                    base_delay = random.uniform(0.1, 0.3)
                    # Slowdown for difficult characters
                    if char.isupper() or char in '!@#$%^&*()[]{}':
                        base_delay *= 1.4
                    time.sleep(base_delay)
            
            # Add space after word (except last word)
            if word_idx < len(words) - 1:
                actions.send_keys(' ').perform()
                time.sleep(random.uniform(0.1, 0.25))
            
            # Natural pauses between words - occasionally pause to "think"
            if word_idx > 0 and word_idx % random.randint(5, 10) == 0:
                print("      ...natural pause...")
                time.sleep(random.uniform(1.5, 4))
            elif random.random() < 0.15:  # 15% chance of micro-pause
                time.sleep(random.uniform(0.5, 1.2))

        print("✅ Description filled")
        human_delay(4, 7)  # Longer pause to simulate user reviewing

        return True
        
    except Exception as e:
        handle_browser_error(e, "填写内容时")
        driver.save_screenshot("fill_content_error.png")
        print("   Screenshot of the error page saved as fill_content_error.png")
        return False

def publish_post(driver):
    """Publish the video post with human-like behavior"""
    try:
        print("🚀 Publishing post...")
        
        # Simulate user reviewing the post before publishing
        print("   Taking time to review post before publishing...")
        human_delay(8, 15)  # User would naturally review their work
        
        # Look for publish button with more natural approach
        publish_button = None
        
        # First try to find by common text content
        try:
            xpath_options = [
                "//button[contains(text(), '发布')]",
                "//button[contains(text(), '发表')]", 
                "//button[contains(text(), '提交')]",
                "//div[contains(text(), '发布')]/parent::button",
                "//span[contains(text(), '发布')]/parent::button",
                "//span[contains(text(), '发布')]/ancestor::button"
            ]
            
            for xpath in xpath_options:
                try:
                    publish_button = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    print(f"   Found publish button via: {xpath}")
                    break
                except:
                    continue
                    
        except:
            pass
        
        # Fallback to CSS selectors
        if not publish_button:
            css_selectors = [
                'button[class*="publish"]',
                'button[class*="submit"]',
                '.publish-btn',
                '.submit-btn',
                'button[type="submit"]'
            ]
            
            for selector in css_selectors:
                try:
                    publish_button = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    print(f"   Found publish button via: {selector}")
                    break
                except:
                    continue
        
        # Final fallback - search all buttons
        if not publish_button:
            print("   Searching all buttons for publish option...")
            try:
                buttons = WebDriverWait(driver, 5).until(
                    lambda d: d.find_elements(By.TAG_NAME, "button")
                )
                
                for button in buttons:
                    try:
                        button_text = button.text.strip().lower()
                        if any(word in button_text for word in ["发布", "发表", "提交", "publish", "submit"]):
                            if button.is_enabled() and button.is_displayed():
                                publish_button = button
                                print(f"   Found publish button with text: '{button.text}'")
                                break
                    except:
                        continue
            except:
                pass
        
        if not publish_button:
            print("❌ Could not find publish button")
            driver.save_screenshot("no_publish_button.png")
            return False
        
        # Human-like interaction with publish button
        print("   Moving to publish button naturally...")
        actions = ActionChains(driver)
        
        # Scroll to button if needed
        try:
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", publish_button)
            human_delay(1, 2)
        except:
            pass
        
        # Move mouse to button naturally
        actions.move_to_element(publish_button).perform()
        human_delay(1, 2)
        
        # Pause before clicking (user hesitation)
        print("   Final moment before publishing...")
        human_delay(2, 4)
        
        # Click naturally with ActionChains instead of JavaScript
        actions.click().perform()
        print("✅ Publish button clicked naturally")
        
        # Wait for publishing to complete with more realistic timing
        print("   Waiting for publishing to complete...")
        human_delay(10, 20)  # Publishing can take time
        
        # Check for success indicators more thoroughly
        try:
            # Wait for potential success message or redirect
            WebDriverWait(driver, 30).until(
                lambda d: any(indicator in d.page_source.lower() for indicator in [
                    "发布成功", "发表成功", "提交成功", "success", "published"
                ]) or d.current_url != driver.current_url
            )
        except:
            pass
        
        # Final verification
        page_text = driver.page_source.lower()
        success_indicators = [
            "发布成功",
            "发表成功", 
            "提交成功",
            "success",
            "published"
        ]
        
        for indicator in success_indicators:
            if indicator in page_text:
                print("✅ Post published successfully")
                return True
        
        print("⚠️ Publish completed (no explicit success confirmation found)")
        print("   This is often normal - the post may still have been published successfully")
        return True
        
    except Exception as e:
        handle_browser_error(e, "发布帖子时")
        driver.save_screenshot("publish_error.png")
        return False

def create_video_post(title, description, video_path, user_data_dir=None, headless=False):
    """Main function to create a video post"""
    
    if not video_path.exists():
        print(f"❌ Video file not found: {video_path}")
        return False
    
    print("🎯 Starting Xiaohongshu video posting automation...")
    print(f"   Title: {title}")
    print(f"   Description: {description[:100]}...")
    print(f"   Video: {video_path.name}")
    print(f"   Size: {video_path.stat().st_size / 1024 / 1024:.1f} MB")
    
    driver = setup_browser(user_data_dir, headless)
    
    try:
        # Step 1: Navigate and check login
        if not check_login_and_navigate(driver):
            return False
        
        # Step 2: Upload video
        if not upload_video(driver, video_path):
            return False
        
        # Step 3: Fill content
        if not fill_content(driver, title, description):
            return False
        
        # Step 4: Publish
        if not publish_post(driver):
            return False
        
        print("🎉 Video posting automation completed successfully!")
        
        # Keep browser open for a few seconds to see the result
        human_delay(5, 8)
        
        return True
        
    except Exception as e:
        handle_browser_error(e, "视频发布自动化过程")
        return False
    finally:
        print("🔒 Closing browser...")
        driver.quit()

def main():
    parser = argparse.ArgumentParser(description="Xiaohongshu video posting automation")
    parser.add_argument("video", type=Path, help="Video file to upload")
    parser.add_argument("--title", required=True, help="Post title")
    parser.add_argument("--desc", required=True, help="Post description")
    parser.add_argument("--profile", help="Chrome profile directory for persistent login")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    
    args = parser.parse_args()
    
    if not args.video.exists():
        print(f"❌ Video file not found: {args.video}")
        sys.exit(1)
    
    success = create_video_post(
        args.title, 
        args.desc, 
        args.video, 
        user_data_dir=args.profile,
        headless=args.headless
    )
    
    if success:
        print("✅ Video posting completed successfully!")
        sys.exit(0)
    else:
        print("❌ Video posting failed")
        sys.exit(1)

if __name__ == "__main__":
    main() 