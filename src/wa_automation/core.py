import os
import re
import time
import random
import shutil
import logging
import subprocess
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .exceptions import WhatsAppAuthenticationError, WhatsAppLoadError, MessageSendError


def _detect_chrome_version():
    """Auto-detect the installed Chrome major version from the OS."""
    try:
        if os.name == 'nt':  # Windows
            import winreg
            for key_path in [
                r"SOFTWARE\Google\Chrome\BLBeacon",
                r"SOFTWARE\Wow6432Node\Google\Chrome\BLBeacon",
            ]:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                    version, _ = winreg.QueryValueEx(key, "version")
                    winreg.CloseKey(key)
                    major = int(version.split(".")[0])
                    logging.info(f"Detected Chrome version: {major} (from registry)")
                    return major
                except Exception:
                    continue
        else:  # Linux / macOS
            for cmd in ["google-chrome", "google-chrome-stable", "chromium-browser", "chromium"]:
                try:
                    out = subprocess.check_output([cmd, "--version"], stderr=subprocess.DEVNULL).decode()
                    match = re.search(r"(\d+)\.\d+\.\d+\.\d+", out)
                    if match:
                        major = int(match.group(1))
                        logging.info(f"Detected Chrome version: {major}")
                        return major
                except Exception:
                    continue
    except Exception as e:
        logging.warning(f"Could not auto-detect Chrome version: {e}")
    return None

# Selector configurations with fallbacks (primary first)
SEND_BUTTON_SELECTORS = [
    (By.CSS_SELECTOR, "span[data-icon='send']"),
    (By.CSS_SELECTOR, "button[aria-label='Send']"),
    (By.CSS_SELECTOR, "[data-testid='send']"),
    (By.CSS_SELECTOR, "span[data-testid='send']"),
    (By.XPATH, "//span[@data-icon='send']"),
    (By.XPATH, "//button[@aria-label='Send']"),
]

ATTACH_BUTTON_SELECTORS = [
    (By.CSS_SELECTOR, "div[data-tab='6']"),  # Confirmed from inspection
    (By.CSS_SELECTOR, "span[data-icon='plus']"),
    (By.CSS_SELECTOR, "span[data-icon='clip']"),
    (By.CSS_SELECTOR, "[data-testid='conversation-clip']"),
    (By.CSS_SELECTOR, "button[title='Attach']"),
    (By.XPATH, "//span[@data-icon='plus']"),
    (By.XPATH, "//span[@data-icon='clip']"),
]

MESSAGE_INPUT_SELECTORS = [
    (By.CSS_SELECTOR, "div[data-tab='10'][contenteditable='true']"),
    (By.CSS_SELECTOR, "div[aria-placeholder='Type a message']"),
    (By.CSS_SELECTOR, "footer div[contenteditable='true']"),
    (By.XPATH, "//div[@contenteditable='true'][@data-tab='10']"),
    (By.XPATH, "//div[@aria-placeholder='Type a message']"),
]

CAPTION_INPUT_SELECTORS = [
    (By.CSS_SELECTOR, "div[data-tab='10'][contenteditable='true']"),
    (By.CSS_SELECTOR, "div[aria-placeholder='Add a caption']"),
    (By.XPATH, "//div[@contenteditable='true'][@data-tab='undefined']"),
    (By.XPATH, "//div[@aria-placeholder='Add a caption']"),
]

IMAGE_INPUT_SELECTORS = [
    (By.CSS_SELECTOR, "input[type='file'][accept='image/*']"),
    (By.CSS_SELECTOR, "input[type='file'][accept*='image']"),
    (By.CSS_SELECTOR, "input[type='file'][accept='image/*,video/mp4,video/3gpp,video/quicktime']"),
]

FILE_INPUT_SELECTORS = [
    (By.CSS_SELECTOR, "input[type='file'][accept='*']"),
    (By.CSS_SELECTOR, "input[type='file']:not([accept='image/*'])"),
]

class WhatsAppAutomation:
    """
    A class to automate WhatsApp Web operations using undetected-chromedriver.
    
    Args:
        user_data_dir (str, optional): Path to store user data. Defaults to './User_Data'.
        chrome_version (int, optional): Chrome major version to use. Auto-detected if not provided.
    """
    
    def __init__(self, user_data_dir=None, chrome_version=None):
        self.user_data_dir = os.path.abspath(user_data_dir or "./User_Data")
        self.chrome_version = chrome_version or _detect_chrome_version()
        self.driver = None
        self.is_authenticated = False
        try:
            self.init_driver()
        except Exception as e:
            logging.error(f"Failed to initialize Chrome driver: {str(e)}")
            raise WhatsAppAuthenticationError(f"Driver initialization failed: {str(e)}")

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
                options.add_argument("--window-size=1920,1080")
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
                self.driver.get("https://web.whatsapp.com")
                
                if self.wait_for_initial_load():
                    logging.info("Chrome WebDriver initialized successfully")
                    self._warm_up_session()
                    return True
                    
            except Exception as e:
                logging.error(f"Driver initialization attempt {attempt + 1} failed: {str(e)}")
                if self.driver:
                    self.driver.quit()
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise WhatsAppAuthenticationError(f"Failed to initialize driver after {max_retries} attempts")

    def wait_for_initial_load(self, timeout=300):
        """Wait for initial WhatsApp Web load and handle authentication"""
        try:
            logging.info("Waiting for WhatsApp Web to load...")
            
            WebDriverWait(self.driver, timeout).until(
                EC.any_of(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "canvas[aria-label='Scan this QR code to link a device!']")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='pane-side']")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[aria-label='Chat list']"))
                )
            )
            
            time.sleep(5)
            
            try:
                qr_code = self.driver.find_element(By.CSS_SELECTOR, "canvas[aria-label='Scan this QR code to link a device!']")
                print("\n=== Please scan the QR code with your WhatsApp phone app ===")
                
                WebDriverWait(self.driver, 60).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[aria-label='Chat list']"))
                )
                time.sleep(5)
                self.is_authenticated = True
                return True
                
            except NoSuchElementException:
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div[aria-label='Chat list']"))
                    )
                    self.is_authenticated = True
                    return True
                except TimeoutException:
                    raise WhatsAppLoadError("Neither QR code nor chat list found")
                    
        except Exception as e:
            raise WhatsAppLoadError(f"Error during initial WhatsApp Web load: {str(e)}")
    
    def _warm_up_session(self):
        """Simulate natural browsing before sending messages to avoid detection."""
        try:
            logging.info("Warming up session — browsing chats...")
            print("\n🔄 Warming up session (browsing chats)...")
            
            # Wait a bit like a real user would
            time.sleep(random.uniform(3, 6))
            
            # Scroll through the chat list a few times
            try:
                chat_pane = self.driver.find_element(By.CSS_SELECTOR, "div[data-testid='pane-side']")
                for _ in range(random.randint(2, 4)):
                    scroll_amount = random.randint(200, 500)
                    self.driver.execute_script(
                        "arguments[0].scrollTop += arguments[1]",
                        chat_pane, scroll_amount
                    )
                    time.sleep(random.uniform(1, 3))
                
                # Scroll back to top
                self.driver.execute_script("arguments[0].scrollTop = 0", chat_pane)
                time.sleep(random.uniform(1, 2))
            except Exception:
                pass  # If chat pane not found, skip scrolling
            
            print("✅ Warm-up complete.\n")
        except Exception as e:
            logging.warning(f"Warm-up phase failed (non-critical): {e}")

    def _find_element_with_fallback(self, selectors, timeout=10, clickable=True):
        """
        Find an element using multiple fallback selectors.
        
        Args:
            selectors: List of (By, selector) tuples to try
            timeout: Timeout for each selector attempt
            clickable: If True, wait for element to be clickable; if False, just presence
            
        Returns:
            WebElement if found, raises TimeoutException if none found
        """
        last_exception = None
        for by, selector in selectors:
            try:
                if clickable:
                    element = WebDriverWait(self.driver, timeout // len(selectors) + 1).until(
                        EC.element_to_be_clickable((by, selector))
                    )
                else:
                    element = WebDriverWait(self.driver, timeout // len(selectors) + 1).until(
                        EC.presence_of_element_located((by, selector))
                    )
                logging.debug(f"Found element with selector: {selector}")
                return element
            except TimeoutException as e:
                last_exception = e
                continue
        raise TimeoutException(f"Could not find element with any of the provided selectors: {[s[1] for s in selectors]}")

    def _insert_text(self, element, text):
        """
        Insert text into an element using a synthetic paste event.
        This properly triggers WhatsApp's Lexical editor to parse formatting and newlines
        without touching the user's actual system clipboard.
        """
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
          
    def send_message(self, number, message, wait_before_send=1, wait_after_send=5):
        """
        Send a text message to a WhatsApp number
        
        Args:
            number (str): The phone number to send the message to
            message (str): The message text
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            whatsapp_url = f'https://web.whatsapp.com/send?phone={number}'
            self.driver.get(whatsapp_url)
            
            if not self._wait_for_chat_load():
                raise WhatsAppLoadError(f"Failed to load chat for number {number}")

            # Find message input with fallback selectors
            message_box = self._find_element_with_fallback(MESSAGE_INPUT_SELECTORS, timeout=10)
            
            # Use execCommand instead of innerHTML to avoid detection
            self._insert_text(message_box, message)
            
            time.sleep(wait_before_send)
            
            # Find send button with fallback selectors
            send_button = self._find_element_with_fallback(SEND_BUTTON_SELECTORS, timeout=10)
            send_button.click()
            time.sleep(wait_after_send)
            
            return True
            
        except Exception as e:
            raise MessageSendError(f"Failed to send message: {str(e)}")

    def send_image(self, number, image_path, caption=None,wait_before_send=1, wait_after_send=5):
        """
        Send an image with optional caption
        
        Args:
            number (str): The phone number to send the image to
            image_path (str): Path to the image file
            caption (str, optional): Caption for the image
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            whatsapp_url = f'https://web.whatsapp.com/send?phone={number}'
            self.driver.get(whatsapp_url)
            
            if not self._wait_for_chat_load():
                raise WhatsAppLoadError(f"Failed to load chat for number {number}")

            attach_button = self._find_element_with_fallback(ATTACH_BUTTON_SELECTORS, timeout=20)
            attach_button.click()
            time.sleep(1)

            # Find image input with fallback selectors
            image_input = self._find_element_with_fallback(IMAGE_INPUT_SELECTORS, timeout=10, clickable=False)
            image_input.send_keys(os.path.abspath(image_path))
            time.sleep(2)

            if caption:
                caption_box = WebDriverWait(self.driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[@contenteditable='true'][@data-tab='undefined']"))
                )
                
                # Use execCommand instead of innerHTML
                self._insert_text(caption_box, caption)
                time.sleep(wait_before_send)  

            send_button = self._find_element_with_fallback(SEND_BUTTON_SELECTORS, timeout=10)
            send_button.click()
            time.sleep(wait_after_send)
            
            return True
            
        except Exception as e:
            raise MessageSendError(f"Failed to send image: {str(e)}")

    def send_file(self, number, file_path, caption=None, wait_before_send=1, wait_after_send=5):
        """
        Send a file with optional caption
        
        Args:
            number (str): The phone number to send the file to
            file_path (str): Path to the file
            caption (str, optional): Caption for the file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            whatsapp_url = f'https://web.whatsapp.com/send?phone={number}'
            self.driver.get(whatsapp_url)
            
            if not self._wait_for_chat_load():
                raise WhatsAppLoadError(f"Failed to load chat for number {number}")

            attach_button = self._find_element_with_fallback(ATTACH_BUTTON_SELECTORS, timeout=20)
            attach_button.click()
            time.sleep(1)

            # Find file input with fallback selectors
            file_input = self._find_element_with_fallback(FILE_INPUT_SELECTORS, timeout=10, clickable=False)
            file_input.send_keys(os.path.abspath(file_path))
            time.sleep(2)

            if caption:
                caption_box = WebDriverWait(self.driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[@contenteditable='true'][@data-tab='undefined']"))
                )
                
                # Use execCommand instead of innerHTML
                self._insert_text(caption_box, caption)
                time.sleep(wait_before_send) 

            send_button = self._find_element_with_fallback(SEND_BUTTON_SELECTORS, timeout=10)
            send_button.click()
            
            # Wait for upload to complete
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "svg.x9tu13d.x1bndym7"))
            )
            WebDriverWait(self.driver, 120).until_not(
                EC.presence_of_element_located((By.CSS_SELECTOR, "svg.x9tu13d.x1bndym7"))
            )
            
            time.sleep(wait_after_send)
            return True
            
        except Exception as e:
            raise MessageSendError(f"Failed to send file: {str(e)}")

    def _wait_for_chat_load(self, timeout=10):
        """Internal method to wait for chat to load"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.any_of(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-tab='10'][contenteditable='true']")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[aria-placeholder='Type a message']")),
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Phone number shared via url is invalid')]")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='chat']"))
                )
            )
            time.sleep(3)
            # Check for invalid number message
            if self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Phone number shared via url is invalid')]"):
                logging.error("Invalid phone number detected")
                raise MessageSendError("Invalid phone number detected")
            return True
        except:
            return False

    def cleanup(self):
        """Close the browser and clean up Chrome processes. Does NOT delete user data (preserves WhatsApp session)."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None

    # Alias for convenience
    close = cleanup