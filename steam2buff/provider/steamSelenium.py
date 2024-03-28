from steam2buff import logger

from datetime import datetime

import asyncpg
from psycopg2 import sql

import json

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException

import time

import json

class SteamSelenium:

    def __init__(self, sessionid=None, steamLoginSecure=None):
        logger.info('SteamSelenium', sessionid, steamLoginSecure)
        self.sessionid = sessionid
        self.steamLoginSecure = steamLoginSecure

    async def __aenter__(self):
        try:
            options = ChromeOptions()
            # Path to the Brave browser binary
            options.binary_location = 'C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe'
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-infobars")
            options.add_argument("--disable-notifications")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-web-security")
            options.add_argument("--disable-xss-auditor")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--ignore-certificate-errors")
            options.add_argument("--ignore-ssl-errors")
            options.add_argument("--blink-settings=imagesEnabled=false")
            # Disable loading stylesheets
            options.add_argument("--blink-settings=cssImagesEnabled=false")
            ## Disable loading images
            # Disable loading images
            options.add_argument("--disable-images")
            # disable stylesheets
            options.add_argument("--disable-stylesheets")
            
            options.add_argument("--enable-javascript")
            options.add_argument("--allow-running-insecure-content")
            options.add_argument("--disable-web-security")
            # options.add_argument("--incognito")
            options.add_argument("--disable-cache")

            # Disable images
            prefs = {"profile.managed_default_content_settings.images": 2, "profile.default_content_setting_values.notifications": 2, "profile.managed_default_content_settings.stylesheets": 2}
            options.add_experimental_option("prefs", prefs)

            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)")

            # options.set_preference("profile.default_content_setting_values.notifications", 2)

            driver = webdriver.Chrome(options=options)

            driver.get('https://steamcommunity.com/market/listings/730/AWP%20%7C%20Neo-Noir%20%28Field-Tested%29') 
            
            driver.delete_all_cookies()
            driver.execute_script('localStorage.clear();')
            
            driver.add_cookie({'name': 'sessionid', 'value': self.sessionid})
            driver.add_cookie({'name': 'steamLoginSecure', 'value': self.steamLoginSecure})

            driver.refresh()
            time.sleep(0.5)
            
            self.driver = driver
            return self
        except Exception as e:
            logger.error(f'Failed to open Steam: {e}')
            exit(1)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.driver.quit()

    async def open_url(self, url, listing_id):
        logger.info(f'Opening URL: {url}')
        self.driver.get(url)

        try:
            WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.ID, 'largeiteminfo_item_name')))
            logger.info(f'Page Loaded')
        except TimeoutException:
            self.driver.refresh()
            try:
                WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.ID, 'largeiteminfo_item_name')))
                logger.info(f'Page Loaded')
            except TimeoutException:
                logger.error(f'Failed to open URL: Timeout')
                return False
            
            
        try:
            element = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.ID, 'listing_{}'.format(listing_id))))
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        except TimeoutException:
            logger.error(f'Failed to locate Listing')
            return False
        
        try:
            button_to_click = element.find_element(By.XPATH, './div[2]/div[1]/div[1]/a')
            button_to_click.click() 
        except NoSuchElementException as e:
            logger.error(f'Failed to Click on First button')
            return False
            
        try:
            confirm_ssa = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, 'market_buynow_dialog_accept_ssa_container')))
            confirm_ssa_button = confirm_ssa.find_element(By.XPATH, './input')
            
            is_clicked = confirm_ssa_button.get_attribute('aria-pressed') == "true"
            
            if not is_clicked:
                confirm_ssa_button.click()
        except TimeoutException:
            logger.error(f'Failed to locate SSA Button')
            return False
            
        try:
            confirm_buy = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, 'market_buynow_dialog_paymentinfo_bottomactions')))
            confirm_buy_button = confirm_buy.find_element(By.XPATH, './a')
            confirm_buy_button.click()
        except TimeoutException:
            logger.error(f'Failed to locate Buy Button')
            return False
            
        return True
