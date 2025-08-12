from pathlib import Path
import time
import json
import random
import subprocess
import uuid
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from config import settings

def sanitize_for_chromedriver(text: str) -> str:
    """Removes non-BMP characters that crash ChromeDriver on Windows."""
    return "".join(c for c in text if c <= '\uFFFF')

class XiaohongshuSelenium:
    def __init__(self):
        self.driver = None
        self.automation_profile = None
        
    def cleanup_existing_chrome_processes(self):
        """Kill any existing Chrome processes using the automation profile"""
        try:
            print("🧹 Cleaning up existing Chrome processes...")
            # Kill processes using the automation profile
            subprocess.run(['pkill', '-f', 'chrome_profiles/auto'], 
                         capture_output=True, text=True)
            time.sleep(2)  # Give processes time to terminate
            print("✅ Existing Chrome processes cleaned up")
        except Exception as e:
            print(f"⚠️ Warning: Could not cleanup Chrome processes: {e}")
    
    # TODO: not working: extension not loaded. Have to manually load the extension.
    def setup_driver_with_extension(self, headless=False):
        """Setup Chrome driver with dedicated automation profile and extension"""
        print("Setting up browser...")
        
        # Clean up any existing Chrome processes first
        self.cleanup_existing_chrome_processes()
        
        options = Options()
        
        # Setup Chrome profiles using config
        if not settings.setup_chrome_profiles():
            print("❌ Failed to setup Chrome profiles")
            return False
        
        # Get the auto profile path from config
        base_profile = Path(settings.auto_chrome_profile_path).absolute()
        
        # If the profile directory is locked, try with a unique suffix
        try:
            self.automation_profile = base_profile
        except Exception as e:
            print(f"⚠️ Base profile directory issue: {e}")
            # Create a unique profile directory as fallback
            unique_suffix = str(uuid.uuid4())[:8]
            self.automation_profile = Path(f"chrome_profiles/auto_{unique_suffix}").absolute()
            self.automation_profile.mkdir(parents=True, exist_ok=True)
            print(f"📁 Using unique profile directory: {self.automation_profile}")
        
        print(f"📁 Using automation profile directory: {self.automation_profile}")
        options.add_argument(f"--user-data-dir={self.automation_profile}")
        
        # Load extension for form filling: Mannully add the extension to chrome before everything.
        #extension_path = Path("~/mydrive/code/maker/monitor_x_bookmark/xiaohongshu_extension").absolute()
        #if extension_path.exists():
        #    print(f"🔌 Loading extension: {extension_path}")
        #    options.add_argument(f"--load-extension={extension_path}")
        #else:
        #    print("⚠️ Extension not found - form filling will be done manually")
        
        # Stealth options (following xhs_account_manager.py exactly)
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--window-size=1366,788")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Additional options to prevent conflicts
        options.add_argument("--no-first-run")
        options.add_argument("--disable-default-apps")
        
        # 根据参数决定是否使用headless模式
        if headless:
            options.add_argument("--headless")  # Run invisibly
            print("🌐 Running in headless mode (no browser window)")
        else:
            print("🌐 Running in visible mode (browser window will be shown)")
        
        # Try multiple methods to get ChromeDriver working
        driver_started = False
        
        # Method 1: webdriver-manager
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service
            import os
            import stat
            
            print("🔄 Attempting webdriver-manager...")
            driver_path = ChromeDriverManager().install()
            print(f"📍 ChromeDriver path: {driver_path}")
            
            # Ensure ChromeDriver has executable permissions
            os.chmod(driver_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
            
            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
            print("✅ webdriver-manager ChromeDriver started successfully")
            driver_started = True
            
        except Exception as e:
            print(f"⚠️ webdriver-manager failed: {e}")
        
        # Method 2: Manual ChromeDriver download and setup
        if not driver_started:
            try:
                import zipfile
                import os
                import stat
                
                print("🔄 Attempting manual ChromeDriver download...")
                
                # Create local chromedriver directory
                local_driver_dir = Path.home() / ".local_chromedriver"
                local_driver_dir.mkdir(exist_ok=True)
                driver_path = local_driver_dir / "chromedriver"
                
                if not driver_path.exists():
                    print("📥 Downloading ChromeDriver manually...")
                    
                    # Get Chrome version
                    chrome_version_cmd = '/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --version'
                    import subprocess
                    try:
                        result = subprocess.run(['bash', '-c', chrome_version_cmd], 
                                              capture_output=True, text=True)
                        chrome_version = result.stdout.split()[-1].split('.')[0]  # Major version
                        print(f"🔍 Chrome version: {chrome_version}")
                    except:
                        chrome_version = "138"  # Fallback
                    
                    # Download URL for Mac ARM
                    download_url = f"https://storage.googleapis.com/chrome-for-testing-public/{chrome_version}.0.7204.168/mac-arm64/chromedriver-mac-arm64.zip"
                    
                    try:
                        response = requests.get(download_url, timeout=30)
                        response.raise_for_status()
                        
                        zip_path = local_driver_dir / "chromedriver.zip"
                        with open(zip_path, 'wb') as f:
                            f.write(response.content)
                        
                        # Extract
                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            zip_ref.extractall(local_driver_dir)
                        
                        # Move chromedriver from nested folder
                        nested_driver = local_driver_dir / "chromedriver-mac-arm64" / "chromedriver"
                        if nested_driver.exists():
                            nested_driver.rename(driver_path)
                        
                        # Cleanup
                        zip_path.unlink()
                        import shutil
                        shutil.rmtree(local_driver_dir / "chromedriver-mac-arm64", ignore_errors=True)
                        
                        print("✅ ChromeDriver downloaded successfully")
                    except Exception as download_error:
                        print(f"❌ Manual download failed: {download_error}")
                        raise
                
                # Set executable permissions
                os.chmod(driver_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
                
                # Start Chrome with manual ChromeDriver
                from selenium.webdriver.chrome.service import Service
                service = Service(str(driver_path))
                self.driver = webdriver.Chrome(service=service, options=options)
                print("✅ Manual ChromeDriver started successfully")
                driver_started = True
                
            except Exception as e:
                print(f"❌ Manual ChromeDriver setup failed: {e}")
        
        # Method 3: System ChromeDriver (last resort)
        if not driver_started:
            try:
                print("🔄 Trying system ChromeDriver as last resort...")
                self.driver = webdriver.Chrome(options=options)
                print("✅ System ChromeDriver started successfully")
                driver_started = True
            except Exception as e:
                print(f"❌ System ChromeDriver failed: {e}")
        
        if not driver_started:
            raise Exception("All ChromeDriver methods failed. Please install ChromeDriver manually.")
        
        # Remove webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("✅ Browser setup complete")
        return self.driver
    
    def dismiss_modals(self):
        """Try to dismiss any popups or overlays."""
        print("🔄 Dismissing any popups...")
        try:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(2)  # Give modal time to close
            print("   ✅ Attempted to dismiss with ESC key.")
        except Exception:
            pass

    def login_to_xiaohongshu(self):
        """Navigate to Xiaohongshu and handle login with robust verification"""
        try:
            print("🔐 Navigating directly to creator page...")
            target_url = "https://creator.xiaohongshu.com/publish/publish?source=official"
            print(f"📍 Target URL: {target_url}")
            self.driver.get(target_url)
            print(f"📍 Current URL after navigation: {self.driver.current_url}")
            time.sleep(8)  # Increased wait for page load
            
            self.dismiss_modals()
            
            print("🔍 Checking Creator Platform login status...")
            
            # Check if we're on a login page by looking for login indicators
            login_indicators = [
                "//input[contains(@placeholder, '手机号')]",
                "//button[contains(text(), '登录')]",
                "//input[contains(@placeholder, '密码')]",
                "//div[contains(text(), '登录')]"
            ]
            
            on_login_page = any(self.driver.find_elements(By.XPATH, indicator) for indicator in login_indicators)
            
            if on_login_page:
                print("⏳ Please complete the Creator Platform login in the browser.")
                print("📌 Look for login form with phone number or email input")
                input("✅ Press Enter after you are logged in and see the publishing interface...")
                time.sleep(3)
            else:
                print("✅ Already logged into Creator Platform.")
            
            print("🔍 Verifying access to posting interface...")
            try:
                # Wait for posting interface elements to be present
                posting_indicators = [
                    "//*[contains(text(), '发布笔记')]",
                    "//*[contains(text(), '添加图片')]",
                    "//input[@type='file']",
                    "//*[contains(text(), '上传图文')]",
                    "//*[contains(text(), '上传视频')]"
                ]
                
                # Try to find any of these indicators
                for indicator in posting_indicators:
                    try:
                        WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, indicator))
                        )
                        print(f"✅ Found posting interface element: {indicator}")
                        break
                    except:
                        continue
                else:
                    # If none found, wait a bit longer for the main interface
                    WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '发布笔记') or contains(text(), '上传')]"))
                    )
                
                print("✅ Successfully accessed posting interface!")
                time.sleep(3)  # Pause after verification
                return True
                
            except TimeoutException:
                print("❌ Could not verify access to posting interface after waiting.")
                print("💡 Make sure you're logged in and can see the upload buttons")
                return False
            
        except Exception as e:
            print(f"❌ Error during login process: {e}")
            return False
    
    def switch_to_video_tab(self):
        """Switch to the video upload tab"""
        print("📹 Switching to video upload tab...")
        try:
            wait = WebDriverWait(self.driver, 10)
            # Look for video upload tab
            video_tab_selectors = [
                "//span[text()='上传视频']/parent::div",
                "//div[contains(text(), '上传视频')]",
                "//button[contains(text(), '上传视频')]"
            ]
            
            for selector in video_tab_selectors:
                try:
                    tab_element = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                    # Check if already active
                    if "active" in tab_element.get_attribute("class"):
                        print("✅ Already on video upload tab.")
                        time.sleep(2)
                        return True
                    
                    print("   🎯 Clicking video upload tab...")
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", tab_element)
                    time.sleep(1)
                    tab_element.click()
                    time.sleep(3)
                    print("✅ Switched to video upload tab!")
                    return True
                except:
                    continue
            
            print("⚠️ Video tab not found, assuming we're on correct tab")
            return True
            
        except Exception as e:
            print(f"❌ Error switching to video tab: {e}")
            return False

    def upload_video_file(self, video_path):
        """Upload video file directly using Selenium"""
        print(f"📁 Uploading video file: {video_path}")
        try:
            # Make sure we're on video tab
            if not self.switch_to_video_tab():
                return False
            
            # Find file input element
            file_input = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
            )
            
            # Send video file path to input
            abs_path = str(Path(video_path).absolute())
            print(f"   📎 Sending file path: {abs_path}")
            file_input.send_keys(abs_path)
            
            print("   ⏳ Confirming upload by waiting for form fields...")
            # Wait for upload to complete and form fields to appear
            WebDriverWait(self.driver, 120).until(  # Increased timeout for video processing
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='标题'], input[placeholder*='填写标题']"))
            )
            
            print("✅ Video upload confirmed! Form fields are now available.")
            time.sleep(5)  # Extra pause for video processing to stabilize
            return True
            
        except TimeoutException:
            print("❌ Video upload timed out. Form fields did not become available.")
            return False
        except Exception as e:
            print(f"❌ Video upload failed: {e}")
            return False

    def handle_hashtag_suggestions(self, desc_element, hashtag_text):
        """Handle hashtag suggestions by clicking the first option"""
        try:
            # Wait for suggestions to appear
            time.sleep(2)
            
            # Based on the real HTML structure provided by user
            suggestion_selectors = [
                # Primary selectors based on actual HTML structure
                ".ql-mention-list-item",  # Main selector for mention items
                ".ql-mention-list .ql-mention-list-item",  # More specific
                "li.ql-mention-list-item",  # Even more specific
                
                # Select the first (selected) item specifically
                ".ql-mention-list-item.selected",
                ".ql-mention-list-item[data-index='0']",
                
                # Alternative selectors for different page structures
                ".ant-dropdown-menu-item",
                ".ant-select-dropdown-menu-item",
                "div[class*='dropdown'] div[class*='item']",
                "div[class*='suggestion'] div",
                "li[class*='suggestion']",
                "div[class*='tag'] div",
                
                # Data testid selectors
                "[data-testid*='suggestion']",
                "[data-testid*='tag']",
                "[data-testid*='dropdown']",
                
                # Role-based selectors
                "div[role='option']",
                "div[role='menuitem']",
                "li[role='option']",
                
                # Generic selectors as fallback
                "div[class*='menu'] div",
                "div[class*='list'] div",
                "div[class*='item']",
                
                # XPath alternatives for more specific targeting
                "//li[@class='ql-mention-list-item']",
                "//li[@class='ql-mention-list-item' and @data-index='0']",
                "//li[contains(@class, 'ql-mention-list-item') and contains(@class, 'selected')]",
                "//div[contains(@class, 'dropdown')]//div[contains(@class, 'item')]",
                "//div[contains(@class, 'suggestion')]//div",
                "//li[contains(@class, 'suggestion')]",
                "//div[contains(@class, 'tag')]//div"
            ]
            
            # Try CSS selectors first (prioritize the real HTML structure)
            for i, selector in enumerate(suggestion_selectors[:15]):  # CSS selectors only
                try:
                    # Wait for suggestions to appear
                    suggestions = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                    )
                    
                    if suggestions:
                        # For the real HTML structure, prefer the selected item or first item
                        if "ql-mention-list-item" in selector:
                            # Try to find the selected item first
                            selected_items = [s for s in suggestions if "selected" in s.get_attribute("class")]
                            if selected_items:
                                selected_items[0].click()
                                print(f"   ✅ Clicked selected hashtag suggestion for #{hashtag_text} (CSS: {selector})")
                                time.sleep(0.5)
                                return True
                            else:
                                # If no selected item, click the first one
                                suggestions[0].click()
                                print(f"   ✅ Clicked first hashtag suggestion for #{hashtag_text} (CSS: {selector})")
                                time.sleep(0.5)
                                return True
                        else:
                            # For other selectors, just click the first one
                            suggestions[0].click()
                            print(f"   ✅ Clicked hashtag suggestion for #{hashtag_text} (CSS: {selector})")
                            time.sleep(0.5)
                            return True
                        
                except Exception as e:
                    continue
            
            # Try XPath selectors if CSS failed
            for selector in suggestion_selectors[15:]:  # XPath selectors
                try:
                    suggestions = WebDriverWait(self.driver, 2).until(
                        EC.presence_of_all_elements_located((By.XPATH, selector))
                    )
                    
                    if suggestions:
                        suggestions[0].click()
                        print(f"   ✅ Clicked hashtag suggestion for #{hashtag_text} (XPath: {selector})")
                        time.sleep(0.5)
                        return True
                        
                except Exception as e:
                    continue
            
            # If no suggestions found, try pressing Enter to select first option
            try:
                from selenium.webdriver.common.keys import Keys
                desc_element.send_keys(Keys.ENTER)
                print(f"   ✅ Pressed Enter for hashtag #{hashtag_text}")
                time.sleep(0.5)
                return True
            except:
                pass
            
            # Try pressing Tab as another fallback
            try:
                from selenium.webdriver.common.keys import Keys
                desc_element.send_keys(Keys.TAB)
                print(f"   ✅ Pressed Tab for hashtag #{hashtag_text}")
                time.sleep(0.5)
                return True
            except:
                pass
            
            # Try pressing Arrow Down + Enter as final fallback
            try:
                from selenium.webdriver.common.keys import Keys
                desc_element.send_keys(Keys.ARROW_DOWN)
                time.sleep(0.2)
                desc_element.send_keys(Keys.ENTER)
                print(f"   ✅ Pressed Arrow Down + Enter for hashtag #{hashtag_text}")
                time.sleep(0.5)
                return True
            except:
                pass
            
            print(f"   ⚠️ No suggestion found for #{hashtag_text}")
            return False
            
        except Exception as e:
            print(f"   ⚠️ Error handling hashtag #{hashtag_text}: {e}")
            return False

    def fill_form_manually(self, title, description):
        """Fill form manually using Selenium (no extension needed)"""
        try:
            print("📝 Filling form manually with Selenium...")
            
            # Sanitize text to avoid ChromeDriver BMP character issues
            safe_title = sanitize_for_chromedriver(title)
            safe_description = sanitize_for_chromedriver(description)
            
            if title != safe_title:
                print("   🧹 Sanitized title to remove special characters")
            if description != safe_description:
                print("   🧹 Sanitized description to remove special characters")
            
            # Wait for form fields to be available
            print("   ⏳ Waiting for form fields...")
            time.sleep(5)
            
            # Fill title
            try:
                title_input = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='标题'], input[placeholder*='填写标题']"))
                )
                
                print("   📝 Filling title...")
                title_input.clear()
                title_input.send_keys(safe_title)
                print(f"   ✅ Title filled: {safe_title}")
                
            except Exception as e:
                print(f"   ❌ Error filling title: {e}")
                return False
            
            # Fill description with hashtag handling
            try:
                desc_selectors = [
                    "textarea[placeholder*='描述']",
                    "div[contenteditable='true']",
                    ".ql-editor",
                    "[data-placeholder*='描述']"
                ]
                
                desc_element = None
                for selector in desc_selectors:
                    try:
                        desc_element = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        print(f"   📄 Found description field with selector: {selector}")
                        break
                    except:
                        continue
                
                if not desc_element:
                    print("   ❌ Could not find description field")
                    return False
                
                print("   📄 Filling description with hashtag handling...")
                desc_element.clear()
                
                # Split description by hashtags and handle them separately
                parts = safe_description.split('#')
                if len(parts) == 1:
                    # No hashtags, just fill normally
                    desc_element.send_keys(safe_description)
                else:
                    # Has hashtags, handle them one by one
                    desc_element.send_keys(parts[0])  # First part without hashtag
                    
                    for i, part in enumerate(parts[1:], 1):
                        if part.strip():  # Skip empty parts
                            # Extract the hashtag text (before any space or punctuation)
                            hashtag_text = part.split()[0] if part.split() else part
                            
                            # Type the hashtag
                            desc_element.send_keys(f"#{hashtag_text}")
                            
                            # Handle the suggestion
                            suggestion_handled = self.handle_hashtag_suggestions(desc_element, hashtag_text)
                            
                            # Add the rest of the part (after hashtag)
                            remaining_text = part[len(hashtag_text):]
                            if remaining_text:
                                desc_element.send_keys(remaining_text)
                
                print(f"   ✅ Description filled with hashtag handling ({len(safe_description)} characters)")
                
            except Exception as e:
                print(f"   ❌ Error filling description: {e}")
                return False
            
            print("✅ Form filled successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error filling form manually: {e}")
            return False

    def monitor_upload_and_publish(self, max_wait_minutes=120):
        """Monitor upload progress and publish when ready"""
        try:
            print(f"👀 Monitoring upload progress (max {max_wait_minutes} minutes)...")
            print("📋 Process: Upload Processing → Publish Button Available → Publishing")
            
            max_iterations = max_wait_minutes  # 1-minute intervals
            
            for i in range(max_iterations):
                try:
                    # Check if still uploading by looking for "取消上传" button
                    cancel_buttons = self.driver.find_elements(By.XPATH, "//span[contains(text(), '取消上传')]")
                    
                    if cancel_buttons:
                        minutes_elapsed = i + 1
                        print(f"⏳ Video still uploading... ({minutes_elapsed}/{max_wait_minutes} min)")
                        time.sleep(60)  # Wait 1 minute
                        continue
                    
                    # Upload completed, check if publish button is clickable
                    print("✅ Upload completed! Checking publish button...")
                    
                    publish_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), '发布') or contains(@class, 'publish')]")
                    
                    for button in publish_buttons:
                        if button.is_enabled():
                            print("🚀 Publish button is clickable! Publishing...")
                            button.click()
                            time.sleep(3)
                            print("✅ Video published successfully!")
                            return True
                    
                    print("⚠️ Publish button found but not clickable yet, waiting...")
                    time.sleep(60)
                    
                except Exception as e:
                    print(f"⚠️ Error checking upload status: {e}")
                    time.sleep(60)
            
            print(f"⚠️ Upload monitoring timeout after {max_wait_minutes} minutes")
            return False
            
        except Exception as e:
            print(f"❌ Error monitoring upload: {e}")
            return False

    def monitor_form_completion(self, max_wait_minutes=10):
        """Monitor the form filling and submission progress"""
        try:
            print(f"👀 Monitoring hybrid form completion (max {max_wait_minutes} minutes)...")
            print("📋 Process: Form Filling → Upload Processing → Publish Button Activation → Publishing")
            
            max_iterations = max_wait_minutes * 12  # 5-second intervals
            
            for i in range(max_iterations):
                try:
                    # Check for completion
                    completion_check = self.driver.execute_script("""
                        return {
                            formResult: window.formResult,
                            complete: window.formResult !== undefined
                        };
                    """)
                    
                    if completion_check['complete']:
                        result = completion_check['formResult']
                        if result.get('success'):
                            print(f"🎉 Hybrid form completion successful!")
                            print(f"📝 Title: {result.get('title', 'N/A')}")
                            print(f"📄 Description: {result.get('description', 'N/A')[:50]}...")
                            print("✅ Video has been published successfully!")
                        else:
                            error_msg = result.get('error', 'Unknown error')
                            print(f"❌ Hybrid form completion failed: {error_msg}")
                            
                            # Handle publish button timeout by using direct upload monitoring
                            if 'Publish button' in error_msg:
                                print("🔄 Switching to direct upload monitoring...")
                                return self.monitor_upload_and_publish()
                        
                        return result.get('success', False)
                    
                    # Progress updates with context
                    if i % 12 == 0:  # Every minute
                        minutes_elapsed = i // 12
                        if minutes_elapsed == 0:
                            print(f"⏳ Extension working... (form filling & upload processing)")
                        elif minutes_elapsed < 3:
                            print(f"⏳ Extension processing... ({minutes_elapsed}/{max_wait_minutes} min) - waiting for publish button")
                        else:
                            print(f"⏳ Still processing... ({minutes_elapsed}/{max_wait_minutes} min) - may need more time for video processing")
                    
                    time.sleep(5)
                    
                except Exception as e:
                    print(f"⚠️ Error checking form completion: {e}")
                    time.sleep(5)
            
            print(f"⚠️ Form completion monitoring timeout after {max_wait_minutes} minutes")
            print("🔄 Switching to direct upload monitoring...")
            return self.monitor_upload_and_publish()
            
        except Exception as e:
            print(f"❌ Error monitoring form completion: {e}")
            return False
    
    def run_hybrid_upload(self, video_path, title, description):
        """Run the hybrid upload process: Selenium upload + Manual form filling"""
        try:
            print("🚀 Starting Selenium video upload process...")
            
            # Step 1: Upload video file with Selenium
            if not self.upload_video_file(video_path):
                return False
            
            # Step 2: Fill form manually with Selenium (no extension needed)
            print("📝 Filling form manually with Selenium...")
            if not self.fill_form_manually(title, description):
                return False
            
            # Step 3: Monitor and publish
            print("⏳ Monitoring for publish button...")
            if not self.monitor_upload_and_publish():
                return False
            
            print("🎉 Upload completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Upload failed: {e}")
            return False
    
    def run_upload_process(self, video_path, title, description, headless=False):
        """Run the complete Selenium upload process"""
        print("🚀 Starting Xiaohongshu Selenium Upload Process")
        print("Selenium (Login + Video Upload + Form Filling + Publishing)")
        print("=" * 70)
        
        try:
            # Setup browser with extension
            self.setup_driver_with_extension(headless=headless)
            print("✅ Browser and extension loaded")
            
            time.sleep(2)
            
            # Login process
            if not self.login_to_xiaohongshu():
                return False
            
            # break here and open the chrome to upload the chrome extension
            time.sleep(2)
            
            # Run hybrid upload
            success = self.run_hybrid_upload(video_path, title, description)
            
            if success:
                print("✅ Hybrid upload process completed successfully!")
                print("🎉 Your video has been published to Xiaohongshu!")
            else:
                print("❌ Upload process failed - check browser for details")
            
            return success
            
        except Exception as e:
            print(f"❌ Upload process failed: {e}")
            return False
        
        finally:
            print("\n🌐 Keeping browser open for 10 seconds for verification...")
            time.sleep(10)
            # Use the new cleanup method instead of just driver.quit()
            self.cleanup_resources()

    def cleanup_resources(self):
        """Clean up browser and profile resources"""
        try:
            if self.driver:
                print("🔄 Closing browser...")
                self.driver.quit()
                time.sleep(2)  # Give Chrome time to fully close
            
            # Clean up temporary profile directories
            if self.automation_profile and "auto_" in str(self.automation_profile):
                # Only clean up uniquely named profiles, not the main one
                main_profile = Path(settings.auto_chrome_profile_path).absolute()
                if self.automation_profile != main_profile:
                    try:
                        import shutil
                        shutil.rmtree(self.automation_profile, ignore_errors=True)
                        print(f"🧹 Cleaned up temporary profile: {self.automation_profile}")
                    except Exception as e:
                        print(f"⚠️ Could not clean up profile directory: {e}")
            
            # Clean up any other temporary profiles
            self.cleanup_temp_profiles()
        except Exception as e:
            print(f"⚠️ Error during cleanup: {e}")
    
    def cleanup_temp_profiles(self):
        """Clean up temporary profile directories"""
        try:
            # Find all temporary directories starting with auto_
            temp_dirs = list(Path("chrome_profiles").glob("auto_*"))
            cleaned_count = 0
            
            for temp_dir in temp_dirs:
                if temp_dir.is_dir():
                    import shutil
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    cleaned_count += 1
                    print(f"🧹 Cleaned up temporary profile: {temp_dir}")
            
            if cleaned_count > 0:
                print(f"✅ Cleaned up {cleaned_count} temporary profiles")
            else:
                print("ℹ️ No temporary profiles found to clean")
                
        except Exception as e:
            print(f"⚠️ Error cleaning up temporary profiles: {e}")

def main():
    """Main execution function"""
    print("📱 XIAOHONGSHU HYBRID UPLOADER")
    print("Selenium (Login + Upload) + Extension (Form Filling)")
    print("=" * 65)
    
    # Configuration
    video_path = settings.test_video_path
    title = "Amazing Video Content 🎬"
    description = "This is an awesome video shared from social media! Check it out and let me know what you think! 🔥✨ #video #content #awesome"
    
    print("📋 Upload Configuration:")
    print(f"   📁 Profile: chrome_profiles/auto/")
    print(f"   🔌 Extension: xiaohongshu_extension/")
    print(f"   🎬 Video: {video_path}")
    print(f"   📝 Title: {title}")
    print(f"   📄 Description: {description[:80]}...")
    
    # Check if video file exists
    if not Path(video_path).exists():
        print(f"\n❌ Video file not found: {video_path}")
        print("Please ensure the video file exists at the specified path.")
        return
    
    # Check if extension exists
    extension_path = Path(settings.xiaohongshu_extension_path)
    if not extension_path.exists():
        print(f"\n❌ Extension folder not found: {extension_path}")
        print("Please ensure the extension folder exists with manifest.json, content.js, and background.js")
        return
    
    print("\n⚠️ Hybrid Process Overview:")
    print("   🔄 Creates dedicated automation browser profile")
    print("   🔌 Loads extension for stealth form filling")
    print("   🔐 Opens Xiaohongshu (login if needed)")
    print("   📁 Selenium uploads video file directly")
    print("   🤝 Extension fills title/description (avoids BMP character errors)")
    print("   🚀 Extension publishes the video")
    print("   ✅ Best of both worlds: Selenium reliability + Extension stealth!")

    
    # Run hybrid upload process
    uploader = XiaohongshuSelenium()
    success = uploader.run_upload_process(video_path, title, description)
    
    if success:
        print("\n🎉 Video uploaded and published successfully!")
        print("💡 Check your Xiaohongshu account to see the published video")
    else:
        print("\n❌ Upload process failed")
        print("💡 Check the browser output above for error details")

# if __name__ == "__main__":
#     main() 