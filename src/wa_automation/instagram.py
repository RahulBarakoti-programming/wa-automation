import os
import time
import random
import logging
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .core import _detect_chrome_version # Reuse version detection
from .exceptions import (
    InstagramAuthenticationError,
    InstagramLoadError,
    InstagramActionError,
    InstagramPostError,
    InstagramDMError
)

class InstagramAutomation:
    """
    A class to automate Instagram operations using undetected-chromedriver.
    
    Args:
        user_data_dir (str, optional): Path to store user data. Defaults to './User_Data/Instagram'.
        chrome_version (int, optional): Chrome major version to use. Auto-detected if not provided.
    """
    
    def __init__(self, user_data_dir=None, chrome_version=None):
        self.user_data_dir = os.path.abspath(user_data_dir or "./User_Data/Instagram")
        self.chrome_version = chrome_version or _detect_chrome_version()
        self.driver = None
        self.is_authenticated = False
        try:
            self.init_driver()
        except Exception as e:
            logging.error(f"Failed to initialize Chrome driver: {str(e)}")
            raise InstagramAuthenticationError(f"Driver initialization failed: {str(e)}")

    def init_driver(self, retry_delay=5, max_retries=3):
        """Initialize Chrome WebDriver with retry mechanism"""
        for attempt in range(max_retries):
            try:
                os.makedirs(self.user_data_dir, exist_ok=True)
                
                options = uc.ChromeOptions()
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-gpu")
                options.add_argument("--disable-notifications")
                options.add_argument("--window-size=1440,900")
                options.add_argument("--disable-session-crashed-bubble")
                options.add_argument("--no-first-run")
                options.add_argument("--no-default-browser-check")

                self.driver = uc.Chrome(
                    options=options,
                    user_data_dir=self.user_data_dir,
                    use_subprocess=True,
                    version_main=self.chrome_version,
                )
                self.driver.maximize_window()
                time.sleep(2)  # Let browser fully start before navigating
                
                # Check for existing session
                self.driver.get("https://www.instagram.com/")
                if self._check_if_logged_in():
                    self.is_authenticated = True
                    logging.info("Already logged in to Instagram via session cookies.")
                else:
                    logging.info("No active Instagram session. Ready for login.")
                return True
                    
            except Exception as e:
                logging.error(f"Driver initialization attempt {attempt + 1} failed: {str(e)}")
                if self.driver:
                    self.driver.quit()
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise InstagramAuthenticationError(f"Failed to initialize driver after {max_retries} attempts")

    def _check_if_logged_in(self, timeout=10):
        """Check if we are logged in by looking for Home feed elements"""
        try:
            # Home icon or Navigation sidebar
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "svg[aria-label='Home'], svg[aria-label='Messenger'], svg[aria-label='New post']"))
            )
            return True
        except TimeoutException:
            return False

    def _find_element_with_fallback(self, selectors, timeout=15, clickable=False):
        """Find an element using multiple fallback selectors."""
        for by, selector in selectors:
            print(f"  [🔍] Trying selector: {selector} (By: {by})")
            try:
                if clickable:
                    element = WebDriverWait(self.driver, timeout // len(selectors) + 1).until(
                        EC.element_to_be_clickable((by, selector))
                    )
                else:
                    element = WebDriverWait(self.driver, timeout // len(selectors) + 1).until(
                        EC.presence_of_element_located((by, selector))
                    )
                print(f"  [✅] SUCCESS! Worked with selector: '{selector}'")
                return element
            except TimeoutException:
                print(f"  [✖] Failed: {selector}")
                continue
        raise TimeoutException(f"Could not find element with any of the provided selectors: {[s[1] for s in selectors]}")

    def login(self, username, password):
        """
        Log into Instagram with username and password.
        Will pause and ask for 2FA code in console if required.
        """
        if self.is_authenticated:
            logging.info("Already authenticated, skipping login.")
            return True

        self.driver.get("https://www.instagram.com/accounts/login/")
        
        try:
            # Username input
            username_input = self._find_element_with_fallback([
                (By.CSS_SELECTOR, "input[name='username']"),
                (By.CSS_SELECTOR, "input[name='email']"),
                (By.CSS_SELECTOR, "input[type='text']")
            ], timeout=20)
            username_input.clear()
            self._type_like_human(username_input, username)
            time.sleep(random.uniform(1, 2))

            # Password input
            password_input = self._find_element_with_fallback([
                (By.CSS_SELECTOR, "input[name='password']"),
                (By.CSS_SELECTOR, "input[name='pass']"),
                (By.CSS_SELECTOR, "input[type='password']")
            ], timeout=10)
            password_input.clear()
            self._type_like_human(password_input, password)
            time.sleep(random.uniform(1, 2))

            # Login Button
            login_btn = self._find_element_with_fallback([
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.XPATH, "//button[descendant::div[text()='Log in']]"),
                (By.XPATH, "//div[@role='button' or @role='none'][.//div[text()='Log in' or text()='Log In']]"),
                (By.CSS_SELECTOR, "div[aria-label='Log in'], div[aria-label='Log In']"),
                (By.XPATH, "//*[@id='login_form']//div[text()='Log in' or text()='Log In']")
            ], timeout=10, clickable=True)
            login_btn.click()

            logging.info("Login credentials submitted.")
            time.sleep(5)

            # Check what screen we are on
            try:
                # Did we get an error?
                error_msg = self.driver.find_element(By.CSS_SELECTOR, "div[role='alert'], p[data-testid='login-error-message'], #slfErrorAlert")
                if error_msg:
                    raise InstagramAuthenticationError(f"Login failed: {error_msg.text}")
            except NoSuchElementException:
                pass # No error message

            # Wait for either Home Screen, 2FA, or Save Info Screen
            print("\\n[Wait] Checking what screen loaded after clicking Log in...")
            detected_screen = "unknown"
            
            # We wait infinitely if needed by doing a loop
            while True:
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.any_of(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "svg[aria-label='Home']")),
                            EC.presence_of_element_located((By.CSS_SELECTOR, "input[aria-label*='code'], input[type='text'], input[name='email'][id]")),
                            EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Save Info')]")),
                            EC.presence_of_element_located((By.XPATH, "//button[text()='Not Now']"))
                        )
                    )
                    break
                except TimeoutException:
                    print("... Still waiting for page to load or challenge to appear ...")
                    error_msg = None
                    try:
                        error_msg = self.driver.find_element(By.CSS_SELECTOR, "div[role='alert'], p[data-testid='login-error-message'], #slfErrorAlert")
                        if error_msg: raise InstagramAuthenticationError(f"Login failed: {error_msg.text}")
                    except NoSuchElementException: pass

            # Handle "Save Your Login Info?" if it appears
            try:
                 not_now_btn = self.driver.find_element(By.XPATH, "//button[text()='Not Now']")
                 not_now_btn.click()
                 time.sleep(3)
            except NoSuchElementException:
                 pass

             # Handle 2FA or Email/SMS verification
            try:
                # Based on tracing, Instagram often hides the code input as type='text' with a random ID or even name='email'
                code_input = self.driver.find_element(By.CSS_SELECTOR, "input[aria-label*='code'], input[type='text'], input[name='email'][id]")
                
                print("\\n=======================================================")
                print("🔒 INSTAGRAM 2FA / SECURITY CHALLENGE DETECTED")
                print(">> Please check the browser window and read the prompt.")
                print("=======================================================\n")
                
                auth_code = input(">> Type the security code here and press Enter: ").strip()
                
                self._type_like_human(code_input, auth_code)
                time.sleep(2)
                
                # Submit code
                submit_code_btn = self._find_element_with_fallback([
                    (By.XPATH, "//div[@role='button'][contains(., 'Continue') or contains(., 'Confirm') or contains(., 'Submit')]"),
                    (By.XPATH, "//button[contains(., 'Continue') or contains(., 'Confirm') or contains(., 'Submit')]"),
                    (By.XPATH, "//*[@role='button' or @role='none'][contains(text(), 'Continue') or contains(text(), 'Confirm')]"),
                    (By.CSS_SELECTOR, "button[type='button'], button[type='submit']"),
                    (By.XPATH, "//div[text()='Continue' or text()='Confirm']")
                ], timeout=15, clickable=True)
                submit_code_btn.click()
                print("Code submitted. Waiting for approval...")
                time.sleep(8)
                
                 # Handle "Save Your Login Info?" again if it appears after 2FA
                try:
                     not_now_btn = self.driver.find_element(By.XPATH, "//button[text()='Not Now']")
                     not_now_btn.click()
                     time.sleep(3)
                except NoSuchElementException:
                     pass

            except NoSuchElementException:
                pass # No verification needed

            if self._check_if_logged_in(timeout=15):
                self.is_authenticated = True
                print("✅ Successfully logged in to Instagram!")
                return True
            else:
                 print("\\n⚠️ WARNING: Auto-login couldn't confirm the Home screen.")
                 input(">> If there's another challenge in the browser, fix it, then press ENTER to continue:")
                 if self._check_if_logged_in(timeout=5):
                     self.is_authenticated = True
                     return True
                 raise InstagramAuthenticationError("Failed to verify successful login (Home screen not found).")

        except Exception as e:
            raise InstagramAuthenticationError(f"Login process failed: {str(e)}")

    def _type_like_human(self, element, text):
        """Type text slowly to simulate human interaction."""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.2))

    def _insert_text(self, element, text):
        """Insert text using synthetic paste event, similar to WhatsApp."""
        self.driver.execute_script("""
            var el = arguments[0];
            var text = arguments[1];
            el.focus();
            document.execCommand('selectAll', false, null);
            document.execCommand('delete', false, null);
            var dataTransfer = new DataTransfer();
            dataTransfer.setData('text/plain', text);
            var event = new ClipboardEvent('paste', {
                clipboardData: dataTransfer,
                bubbles: true,
                cancelable: true
            });
            el.dispatchEvent(event);
        """, element, text)

    def send_dm(self, username, message):
        """Send a Direct Message to a user by navigating to their profile directly."""
        if not self.is_authenticated:
            raise InstagramAuthenticationError("Not logged in.")

        try:
            # 1. Go directly to user's profile
            self.driver.get(f"https://www.instagram.com/{username}/")
            time.sleep(3)
            
            # 2. Click "Message" button on their profile
            message_btn = self._find_element_with_fallback([
                (By.XPATH, "//div[@role='button'][text()='Message']"),
                (By.XPATH, "//div[text()='Message']"),
                (By.XPATH, "//button[descendant::div[text()='Message']]")
            ], timeout=15, clickable=True)
            message_btn.click()
            time.sleep(4) # Wait for DM interface to open
            
            # 3. Handle potential popups like "Turn on Notifications" in DMs
            try:
                not_now_btn = self.driver.find_element(By.XPATH, "//button[text()='Not Now']")
                not_now_btn.click()
                time.sleep(1)
            except NoSuchElementException:
                pass

            # 4. Type the message
            # The input area usually has aria-label="Message"
            msg_box = self._find_element_with_fallback([
                (By.CSS_SELECTOR, "div[aria-label='Message']"),
                (By.CSS_SELECTOR, "div[contenteditable='true'][role='textbox']"),
                (By.CSS_SELECTOR, "textarea[placeholder='Message...']")
            ], timeout=15)
            self._insert_text(msg_box, message)
            time.sleep(1)

            # 5. Click Send
            send_btn = self._find_element_with_fallback([
                (By.CSS_SELECTOR, "div[aria-label='Send'][role='button']"),
                (By.XPATH, "//div[@role='button'][text()='Send']"),
                (By.XPATH, "//button[text()='Send']")
            ], timeout=10, clickable=True)
            send_btn.click()
            time.sleep(2)
            
            return True

        except Exception as e:
            raise InstagramDMError(f"Failed to send DM to {username}: {str(e)}")

    def like_post(self, post_url):
        """Like an Instagram post by URL."""
        if not self.is_authenticated:
            raise InstagramAuthenticationError("Not logged in.")

        try:
            self.driver.get(post_url)
            time.sleep(3)

            # Check if already liked
            try:
                self.driver.find_element(By.CSS_SELECTOR, "svg[aria-label='Unlike']")
                logging.info(f"Post {post_url} is already liked.")
                return True
            except NoSuchElementException:
                pass

            # Click Like button
            like_btn = self._find_element_with_fallback([
                (By.CSS_SELECTOR, "svg[aria-label='Like']"),
                (By.XPATH, "//*[@aria-label='Like']")
            ], timeout=10, clickable=True)
            
            # Click the parent button/div of the SVG
            like_btn.find_element(By.XPATH, "./ancestor::div[@role='button']").click()
            time.sleep(random.uniform(1, 2))
            return True

        except Exception as e:
            raise InstagramActionError(f"Failed to like post {post_url}: {str(e)}")
            
    def follow_user(self, username):
        """Follow a user by their username."""
        if not self.is_authenticated:
            raise InstagramAuthenticationError("Not logged in.")

        try:
            self.driver.get(f"https://www.instagram.com/{username}/")
            time.sleep(3)
            
            # Click Follow button
            follow_btn = self._find_element_with_fallback([
                (By.XPATH, "//button[descendant::div[text()='Follow']]"),
                (By.XPATH, "//div[text()='Follow']")
            ], timeout=10, clickable=True)
            
            follow_btn.click()
            time.sleep(random.uniform(1, 2))
            return True
            
        except TimeoutException:
            # Check if we are already following
            try:
                self.driver.find_element(By.XPATH, "//button[descendant::div[text()='Following']]")
                logging.info(f"Already following {username}.")
                return True
            except NoSuchElementException:
                raise InstagramActionError(f"Failed to follow user {username}. Button not found.")
        except Exception as e:
            raise InstagramActionError(f"Failed to follow user {username}: {str(e)}")

    def post_photo(self, photo_path, caption=""):
        """Post a photo to the Instagram feed."""
        if not self.is_authenticated:
            raise InstagramAuthenticationError("Not logged in.")

        if not os.path.exists(photo_path):
             raise InstagramPostError(f"Photo file not found: {photo_path}")

        try:
            self.driver.get("https://www.instagram.com/")
            time.sleep(3)
            
            # Click "Create" in sidebar
            create_btn = self._find_element_with_fallback([
                (By.CSS_SELECTOR, "svg[aria-label='New post']"),
                (By.XPATH, "//span[text()='Create']")
            ], timeout=15, clickable=True)
            
            # Click the parent button/link
            create_btn.find_element(By.XPATH, "./ancestor::a | ./ancestor::div[@role='button']").click()
            time.sleep(2)
            
            # Upload photo
            # The file input is usually hidden
            file_input = self._find_element_with_fallback([
                (By.CSS_SELECTOR, "input[type='file'][accept*='image']"),
                (By.CSS_SELECTOR, "input[type='file']")
            ], timeout=10)
            file_input.send_keys(os.path.abspath(photo_path))
            time.sleep(3)

            # Click Next twice (Crop -> Filters -> Caption)
            for _ in range(2):
                next_btn = self._find_element_with_fallback([
                    (By.XPATH, "//button[contains(text(), 'Next')]"),
                    (By.XPATH, "//div[contains(text(), 'Next')]")
                ], timeout=10, clickable=True)
                next_btn.click()
                time.sleep(2)

            # Type Caption
            if caption:
                caption_box = self._find_element_with_fallback([
                    (By.CSS_SELECTOR, "div[contenteditable='true'][role='textbox']"),
                    (By.CSS_SELECTOR, "div[aria-label='Write a caption...']")
                ], timeout=10)
                self._insert_text(caption_box, caption)
                time.sleep(1)

            # Click Share
            share_btn = self._find_element_with_fallback([
                 (By.XPATH, "//button[contains(text(), 'Share')]"),
                 (By.XPATH, "//div[contains(text(), 'Share')]")
            ], timeout=10, clickable=True)
            share_btn.click()
            
            # Wait for upload to complete
            WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Your post has been shared')]"))
            )
            time.sleep(2)
            
            # Close dialog
            close_btn = self._find_element_with_fallback([
                (By.CSS_SELECTOR, "svg[aria-label='Close']"),
                (By.XPATH, "//*[@aria-label='Close']")
            ], timeout=5, clickable=True)
            close_btn.find_element(By.XPATH, "./ancestor::div[@role='button'] | ./ancestor::button").click()
            
            return True

        except Exception as e:
            raise InstagramPostError(f"Failed to post photo: {str(e)}")

    def get_profile_info(self, username):
        """Scrape basic profile info like Bio and Post URLs."""
        if not self.is_authenticated:
            raise InstagramAuthenticationError("Not logged in.")

        try:
            self.driver.get(f"https://www.instagram.com/{username}/")
            time.sleep(3)
            
            # Wait for header to load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "header"))
            )
            
            data = {
                "username": username, 
                "bio": "", 
                "recent_posts": [],
                "followers": "0",
                "following": "0",
                "posts_count": "0"
            }
            
            # Extract metrics securely using specific DOM nodes
            try:
                # 1. Use JavaScript to forcefully extract text regardless of CSS visibility/truncation
                data["followers"] = self.driver.execute_script("""
                    let el = document.querySelector('a[href*="/followers/"] span[title], a[href*="/followers/"]');
                    return el ? (el.title || el.textContent || '').replace(/[^0-9.,kKmM]/g, '') : "0";
                """) or "0"
                
                data["following"] = self.driver.execute_script("""
                    let el = document.querySelector('a[href*="/following/"] span[title], a[href*="/following/"]');
                    return el ? (el.title || el.textContent || '').replace(/[^0-9.,kKmM]/g, '') : "0";
                """) or "0"
                
                data["posts_count"] = self.driver.execute_script("""
                    let els = Array.from(document.querySelectorAll('header span, header li, header div'));
                    let match = els.find(e => e.textContent.toLowerCase().includes('post') && e.textContent.length < 20);
                    return match ? match.textContent.replace(/[^0-9.,kKmM]/g, '') : "0";
                """) or "0"
            except Exception as e:
                logging.debug(f"Metrics JS extraction failed: {e}")

            # Extract Bio using the header context
            try:
                # Bio is usually the last major text block. Execute JS to filter out numbers and standard labels
                bio_text = self.driver.execute_script("""
                    return Array.from(document.querySelectorAll('header section span'))
                        .filter(e => !e.closest('a') && !e.closest('h1') && e.textContent.length > 5)
                        .map(e => e.textContent)
                        .join('\\n');
                """)
                data["bio"] = bio_text.strip()
            except Exception as e:
                logging.debug(f"Bio extraction failed: {e}")
                
            # Extract recent post URLs
            try:
                post_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/p/') or contains(@href, '/reel/')]")
                urls = []
                for link in post_links:
                    href = link.get_attribute("href")
                    if href and href not in urls:
                        urls.append(href)
                data["recent_posts"] = urls[:12] # Top 12
            except:
                pass
                
            return data

        except Exception as e:
            raise InstagramActionError(f"Failed to get profile info for {username}: {str(e)}")

    def get_post_details(self, post_url):
        """Scrape a post's caption and its comments."""
        if not self.is_authenticated:
            raise InstagramAuthenticationError("Not logged in.")

        try:
            self.driver.get(post_url)
            time.sleep(6) # Increase base sleep to let comments properly fetch
            
            data = {"post_url": post_url, "caption": "", "comments": []}
            
            # 1. Extract Post Caption
            try:
                # Try multiple vectors: desktop standard, mobile fallback, and generic list index
                caption_el = self._find_element_with_fallback([
                    (By.XPATH, "//h1[contains(@class, '_ap3a')]"),
                    (By.XPATH, "//h1"),
                    (By.XPATH, "//ul//li[1]//span[contains(@class, '_ap3a')]"),
                    (By.XPATH, "//div[contains(@class, 'x1lliihq')]//span[contains(@class, '_ap3a')]")
                ], timeout=10)
                data["caption"] = caption_el.text
            except TimeoutException:
                print("  [✖] Timed out waiting for caption. Dom might be complex, attempting JS extraction...")
                data["caption"] = self.driver.execute_script("""
                    let h1 = document.querySelector('h1');
                    if (h1) return h1.textContent;
                    let span = document.querySelector('ul > div > li:first-child span');
                    return span ? span.textContent : "";
                """)
                pass

            # 2. Extract Comments and Commenter Profiles
            # Based on inspector: commenters have <a role="link" href="/username/"> inside an <h3>
            # The comment text is usually in a span near the <h3>
            try:
                comment_blocks = self.driver.find_elements(By.XPATH, "//ul/div/li/div/div")
                for block in comment_blocks:
                    comment_data = {"username": "", "profile_url": "", "text": ""}
                    try:
                        # Find commenter
                        user_link = block.find_element(By.XPATH, ".//h3//a[@role='link']")
                        comment_data["username"] = user_link.text
                        comment_data["profile_url"] = user_link.get_attribute("href")
                        
                        # Find comment text (span usually after the h3)
                        # The text class based on inspector: _ap3a _aaco _aacu _aacx _aad7 _aade
                        try:
                            # Try to find exactly the comment span and not the trailing time/reply buttons
                            text_span = block.find_element(By.XPATH, ".//div[contains(@class, 'x1lliihq')]//span[contains(@class, '_ap3a')] | .//div[2]/div[1]/span[1]")
                            comment_data["text"] = text_span.text
                        except NoSuchElementException:
                             # Fallback, just dump block text
                             comment_data["text"] = block.text.replace(comment_data["username"], "").strip()
                             
                        if comment_data["username"]:
                            data["comments"].append(comment_data)
                    except NoSuchElementException:
                        continue
            except Exception as e:
                logging.debug(f"Comment extraction failed: {e}")
                
            return data

        except Exception as e:
            raise InstagramActionError(f"Failed to extract post details for {post_url}: {str(e)}")

    def cleanup(self):
        """Close browser. Does NOT delete User_Data."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None

    close = cleanup
