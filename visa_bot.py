import yaml
import argparse
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from telegram import Bot
from telegram.error import TelegramError

def load_config(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

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

def check_appointments(driver, config):
    url = f"https://ais.usvisa-info.com/{config['embassies'][0]['country_code']}/niv/schedule/{config['users'][0]['schedule_id']}/appointment"
    driver.get(url)
    time.sleep(3)  # wait for page load

    try:
        no_appointments_text = driver.find_element(By.XPATH, "//*[contains(text(),'No appointments available')]")
        return False
    except:
        return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    config = load_config(args.config)

    driver = setup_driver()

    available = check_appointments(driver, config)
    if available:
        message = "Visa appointment available! Check immediately!"
        send_telegram_message(config["telegram"]["bot_token"], config["telegram"]["chat_id"], message)
        logging.info(message)
    else:
        logging.info("No appointments available.")

    driver.quit()

if __name__ == "__main__":
    main()
