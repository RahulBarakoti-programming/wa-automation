import os
import time
import shutil
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from .exceptions import WhatsAppAuthenticationError, WhatsAppLoadError, MessageSendError

class WhatsAppAutomation:
    """
    A class to automate WhatsApp Web operations using Selenium.
    
    Args:
        user_data_dir (str, optional): Path to store user data. Defaults to './User_Data'.
    """
    
    def __init__(self, user_data_dir=None):
        self.user_data_dir = os.path.abspath(user_data_dir or "./User_Data")
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
                
                options = Options()
                options.add_argument(f"user-data-dir={self.user_data_dir}")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-gpu")
                options.add_argument("--disable-extensions")
                options.add_argument("--disable-notifications")
                options.add_argument("--disable-web-security")
                options.add_argument("--allow-running-insecure-content")
                options.add_argument("--window-size=1920,1080")

                self.driver = webdriver.Chrome(
                    service=Service(ChromeDriverManager().install()),
                    options=options
                )
                self.driver.maximize_window()
                self.driver.get("https://web.whatsapp.com")
                
                if self.wait_for_initial_load():
                    logging.info("Chrome WebDriver initialized successfully")
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
            whatsapp_url = f'https://web.whatsapp.com/send?phone={number}&text&app_absent=0'
            self.driver.get(whatsapp_url)
            
            if not self._wait_for_chat_load():
                raise WhatsAppLoadError(f"Failed to load chat for number {number}")

            message_box = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@contenteditable='true'][@data-tab='10']"))
            )
            
            self.driver.execute_script(
                "arguments[0].focus(); "
                "arguments[0].innerHTML = ''; "
                "arguments[0].innerHTML = arguments[1]; "
                "arguments[0].dispatchEvent(new InputEvent('input', "
                "{ bubbles: true, cancelable: true, inputType: 'insertText', data: arguments[1] }));",
                message_box, message
            )
            
            time.sleep(wait_before_send)
            
            send_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Send']"))
            )
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
            whatsapp_url = f'https://web.whatsapp.com/send?phone={number}&text&app_absent=0'
            self.driver.get(whatsapp_url)
            
            if not self._wait_for_chat_load():
                raise WhatsAppLoadError(f"Failed to load chat for number {number}")

            attach_button = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[title='Attach']"))
            )
            attach_button.click()
            time.sleep(1)

            image_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file'][accept='image/*,video/mp4,video/3gpp,video/quicktime']"))
            )
            image_input.send_keys(os.path.abspath(image_path))
            time.sleep(2)

            if caption:
                caption_box = WebDriverWait(self.driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[@contenteditable='true'][@data-tab='undefined']"))
                )
                
                self.driver.execute_script(
                    "arguments[0].focus(); "
                    "arguments[0].innerHTML = ''; "
                    "arguments[0].innerHTML = arguments[1]; "
                    "arguments[0].dispatchEvent(new InputEvent('input', "
                    "{ bubbles: true, cancelable: true, inputType: 'insertText', data: arguments[1] }));",
                    caption_box, caption
                )
                time.sleep(wait_before_send)  

            send_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Send']"))
            )
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
            whatsapp_url = f'https://web.whatsapp.com/send?phone={number}&text&app_absent=0'
            self.driver.get(whatsapp_url)
            
            if not self._wait_for_chat_load():
                raise WhatsAppLoadError(f"Failed to load chat for number {number}")

            attach_button = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[title='Attach']"))
            )
            attach_button.click()
            time.sleep(1)

            file_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file'][accept='*']"))
            )
            file_input.send_keys(os.path.abspath(file_path))
            time.sleep(2)

            if caption:
                caption_box = WebDriverWait(self.driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[@contenteditable='true'][@data-tab='undefined']"))
                )
                
                self.driver.execute_script(
                    "arguments[0].focus(); "
                    "arguments[0].innerHTML = ''; "
                    "arguments[0].innerHTML = arguments[1]; "
                    "arguments[0].dispatchEvent(new InputEvent('input', "
                    "{ bubbles: true, cancelable: true, inputType: 'insertText', data: arguments[1] }));",
                    caption_box, caption
                )
                time.sleep(wait_before_send) 

            send_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Send']"))
            )
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

    def _wait_for_chat_load(self, timeout=60):
        """Internal method to wait for chat to load"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.any_of(
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
        """Close the browser and clean up resources"""
        if self.driver:
            self.driver.quit()
        if os.path.exists(self.user_data_dir):
            shutil.rmtree(self.user_data_dir)