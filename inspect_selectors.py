"""
WhatsApp Web Selector Inspector v2
Outputs results to selectors_output.txt for reliable capture
"""

import os
import time
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

OUTPUT_FILE = "selectors_output.txt"

def log(msg):
    """Print and write to file"""
    print(msg, flush=True)
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def setup_driver():
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    driver.maximize_window()
    return driver

def get_element_info(element):
    if element is None:
        return "NOT FOUND"
    
    info = {}
    for attr in ['aria-label', 'data-testid', 'data-tab', 'data-icon', 'title', 'role', 'aria-placeholder', 'contenteditable', 'accept', 'type']:
        val = element.get_attribute(attr)
        if val:
            info[attr] = val
    info['tag'] = element.tag_name
    cls = element.get_attribute('class')
    if cls:
        info['class'] = cls[:80]
    return info

def find_element_safe(driver, selector):
    try:
        return driver.find_element(By.CSS_SELECTOR, selector)
    except:
        return None

def inspect_elements(driver):
    log("\n" + "="*60)
    log("WHATSAPP WEB SELECTOR INSPECTION RESULTS")
    log("="*60)
    
    # Side Panel
    log("\n--- SIDE PANEL / CHAT LIST ---")
    for sel in ["[data-testid='pane-side']", "[aria-label='Chat list']", "[data-testid='chat-list']"]:
        elem = find_element_safe(driver, sel)
        if elem:
            log(f"FOUND: {sel} => {get_element_info(elem)}")
    
    # Message Input
    log("\n--- MESSAGE INPUT BOX ---")
    for sel in ["[contenteditable='true'][data-tab]", "[aria-placeholder='Type a message']", "div[data-tab='10']", "div[data-tab='6']", "footer [contenteditable='true']", "[role='textbox']"]:
        elem = find_element_safe(driver, sel)
        if elem:
            log(f"FOUND: {sel} => {get_element_info(elem)}")
    
    # Send Button
    log("\n--- SEND BUTTON ---")
    for sel in ["[data-testid='send']", "[data-icon='send']", "[aria-label='Send']", "button[aria-label='Send']", "span[data-testid='send']", "span[data-icon='send']"]:
        elem = find_element_safe(driver, sel)
        if elem:
            log(f"FOUND: {sel} => {get_element_info(elem)}")
    
    # Attach Button
    log("\n--- ATTACH BUTTON ---")
    for sel in ["[data-testid='conversation-clip']", "[data-icon='clip']", "[data-icon='attach-menu-plus']", "[title='Attach']", "span[data-icon='clip']", "[data-icon='plus']", "button[title='Attach']"]:
        elem = find_element_safe(driver, sel)
        if elem:
            log(f"FOUND: {sel} => {get_element_info(elem)}")
    
    # File Inputs
    log("\n--- FILE INPUTS ---")
    try:
        inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
        for i, inp in enumerate(inputs):
            log(f"File Input {i+1}: {get_element_info(inp)}")
    except:
        log("No file inputs found")

def click_attach_and_inspect(driver):
    log("\n--- CLICKING ATTACH BUTTON ---")
    for sel in ["[data-icon='plus']", "[data-icon='clip']", "[data-testid='conversation-clip']", "[title='Attach']"]:
        elem = find_element_safe(driver, sel)
        if elem:
            try:
                elem.click()
                log(f"Clicked: {sel}")
                time.sleep(2)
                break
            except:
                continue
    
    log("\n--- ATTACH MENU OPTIONS ---")
    for sel in ["[data-testid='mi-attach-document']", "[data-testid='mi-attach-media']", "[data-icon='attach-document']", "[data-icon='attach-image']", "li[data-testid*='attach']", "[data-icon='image']", "[data-icon='document']"]:
        elem = find_element_safe(driver, sel)
        if elem:
            log(f"FOUND: {sel} => {get_element_info(elem)}")
    
    log("\n--- FILE INPUTS AFTER ATTACH ---")
    try:
        inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
        for i, inp in enumerate(inputs):
            log(f"File Input {i+1}: {get_element_info(inp)}")
    except:
        log("No file inputs found")

def main():
    # Clear output file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("WhatsApp Web Selector Inspector Results\n")
        f.write(f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    log("="*60)
    log("Starting WhatsApp Web Selector Inspector")
    log("="*60)
    
    driver = setup_driver()
    
    try:
        log("\nOpening WhatsApp Web...")
        driver.get("https://web.whatsapp.com")
        
        log("\n>>> SCAN QR CODE WITH YOUR PHONE <<<")
        log("Waiting up to 120 seconds for login...\n")
        
        try:
            WebDriverWait(driver, 120).until(
                EC.any_of(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='pane-side']")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[aria-label='Chat list']")),
                )
            )
            log("LOGIN SUCCESSFUL!")
            time.sleep(5)
            
            inspect_elements(driver)
            
            log("\n>>> CLICK ON ANY CHAT, then press Enter in terminal <<<")
            input()
            time.sleep(2)
            
            inspect_elements(driver)
            click_attach_and_inspect(driver)
            
        except Exception as e:
            log(f"\nError: {e}")
            inspect_elements(driver)
        
        log("\n" + "="*60)
        log("INSPECTION COMPLETE")
        log(f"Results saved to: {OUTPUT_FILE}")
        log("="*60)
        log("\nPress Enter to close browser...")
        input()
        
    finally:
        driver.quit()
    
    log("\nDone!")

if __name__ == "__main__":
    main()
