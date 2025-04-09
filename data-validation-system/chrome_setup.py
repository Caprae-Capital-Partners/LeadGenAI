## chrome_setup.py


"""
Utility script to set up Chrome/Chromium for Selenium WebDriver
"""
import os
import sys
import logging
import subprocess
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_chrome_installation():
    """Check if Chrome/Chromium is installed and accessible"""
    try:
        # Try different commands based on OS
        if sys.platform.startswith('win'):
            # Windows
            commands = [
                r'where chrome',
                r'where chromium',
                r'dir "C:\Program Files\Google\Chrome\Application\chrome.exe"',
                r'dir "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"'
            ]
        elif sys.platform.startswith('darwin'):
            # macOS
            commands = [
                'which google-chrome',
                'which chromium',
                'ls /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome',
                'ls /Applications/Chromium.app/Contents/MacOS/Chromium'
            ]
        else:
            # Linux
            commands = [
                'which google-chrome',
                'which chromium',
                'which chromium-browser'
            ]
            
        for cmd in commands:
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip():
                    logger.info(f"Chrome/Chromium found: {result.stdout.strip()}")
                    return True
            except:
                pass
                
        logger.warning("Chrome/Chromium not found in standard locations")
        return False
        
    except Exception as e:
        logger.error(f"Error checking Chrome installation: {e}")
        return False

def setup_webdriver():
    """Set up and test Chrome WebDriver"""
    try:
        # Check Chrome installation first
        if not check_chrome_installation():
            logger.error("Chrome/Chromium not found. Please install it before continuing.")
            return False
            
        # Install or update ChromeDriver
        logger.info("Setting up ChromeDriver...")
        driver_path = ChromeDriverManager().install()
        logger.info(f"ChromeDriver installed at: {driver_path}")
        
        # Test the WebDriver
        logger.info("Testing WebDriver...")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Try to navigate to a simple page
        driver.get("https://www.google.com")
        title = driver.title
        driver.quit()
        
        logger.info(f"WebDriver test successful. Page title: {title}")
        return True
        
    except Exception as e:
        logger.error(f"Error setting up WebDriver: {e}")
        return False

if __name__ == "__main__":
    logger.info("Checking Chrome/Chromium and WebDriver setup...")
    if setup_webdriver():
        logger.info("Setup completed successfully!")
    else:
        logger.error("Setup failed. Please check the logs for details.")
        sys.exit(1)