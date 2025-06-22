import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from telegram import Bot
from telegram.error import TelegramError

logging.basicConfig(level=logging.INFO)

def send_telegram_message(bot_token, chat_id, message):
    bot = Bot(token=bot_token)
    try:
        bot.send_message(chat_id=chat_id, text=message)
    except TelegramError as e:
        logging.error(f"Telegram error: {e}")

def setup_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--user-data-dir=/tmp/chrome-user-data")
    service = Service('/usr/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def check_appointments(driver, user_email, schedule_id, embassy_country_code):
    url = f"https://ais.usvisa-info.com/{embassy_country_code}/niv/schedule/{schedule_id}/appointment"
    driver.get(url)
    time.sleep(3)  # wait for page load

    try:
        # Example: check if text 'No appointments available' is on page
        driver.find_element(By.XPATH, "//*[contains(text(),'No appointments available')]")
        return False
    except:
        return True

def main():
    # Read config from environment variables
    user_email = os.getenv("USER_EMAIL")
    user_password = os.getenv("USER_PASSWORD")  # Not used in this minimal example, but you can add login logic
    schedule_id = os.getenv("USER_SCHEDULE_ID")
    group_id = os.getenv("USER_GROUP_ID")       # Not used here, add if needed
    embassy_country_code = os.getenv("EMBASSY_COUNTRY_CODE")
    embassy_facility_id = os.getenv("EMBASSY_FACILITY_ID")  # Not used here, add if needed

    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not all([user_email, user_password, schedule_id, group_id, embassy_country_code, embassy_facility_id, telegram_bot_token, telegram_chat_id]):
        logging.error("Missing one or more required environment variables.")
        return

    driver = setup_driver()

    available = check_appointments(driver, user_email, schedule_id, embassy_country_code)
    if available:
        message = f"Visa appointment available for {user_email}! Check immediately!"
        send_telegram_message(telegram_bot_token, telegram_chat_id, message)
        logging.info(message)
    else:
        logging.info("No appointments available.")

    driver.quit()

if __name__ == "__main__":
    main()
