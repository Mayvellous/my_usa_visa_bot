import os
import time
import logging
import threading
from datetime import datetime
from flask import Flask
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from telegram import Bot
from telegram.error import TelegramError

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

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

def check_appointments(driver, schedule_id, embassy_country_code):
    url = f"https://ais.usvisa-info.com/{embassy_country_code}/niv/schedule/{schedule_id}/appointment"
    driver.get(url)
    time.sleep(3)  # wait for page load

    cutoff_date = datetime(2025, 11, 17)  # November 17, 2025

    try:
        no_appointments_text = driver.find_elements(By.XPATH, "//*[contains(text(),'No appointments available')]")
        if no_appointments_text:
            return False

        date_elements = driver.find_elements(By.CSS_SELECTOR, ".ui-datepicker-calendar td.available a")

        for elem in date_elements:
            date_str = elem.get_attribute("aria-label")  # Example: "Tuesday, November 14, 2025"
            if not date_str:
                continue

            try:
                appointment_date = datetime.strptime(date_str, "%A, %B %d, %Y")
            except ValueError:
                logging.warning(f"Date parsing failed for: {date_str}")
                continue

            if appointment_date < cutoff_date:
                return True

        return False

    except Exception as e:
        logging.error(f"Error checking appointments: {e}")
        return False

def bot_loop():
    user_email = os.getenv("USER_EMAIL")
    user_password = os.getenv("USER_PASSWORD")
    schedule_id = os.getenv("USER_SCHEDULE_ID")
    group_id = os.getenv("USER_GROUP_ID")  # Keep for completeness
    embassy_country_code = os.getenv("EMBASSY_COUNTRY_CODE")
    embassy_facility_id = os.getenv("EMBASSY_FACILITY_ID")

    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not all([user_email, user_password, schedule_id, group_id, embassy_country_code, embassy_facility_id, telegram_bot_token, telegram_chat_id]):
        logging.error("Missing one or more required environment variables.")
        return

    driver = setup_driver()

    while True:
        logging.info("Checking appointments...")
        available = check_appointments(driver, schedule_id, embassy_country_code)

        if available:
            message = f"Visa appointment available BEFORE Nov 17, 2025 for {user_email}! Check immediately!"
            send_telegram_message(telegram_bot_token, telegram_chat_id, message)
            logging.info(message)
        else:
            logging.info("No appointments available before cutoff date.")

        time.sleep(60 * 15)  # Wait 15 minutes

@app.route("/")
def index():
    return "Bot is running!"

if __name__ == "__main__":
    threading.Thread(target=bot_loop, daemon=True).start()
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
