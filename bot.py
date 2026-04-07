import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ========================
# 🔧 ENV CONFIG
# ========================

RUN_DATES = os.getenv("RUN_DATES", "").split(",")
BOOKING_DATES = os.getenv("BOOKING_DATES", "").split(",")

LOCATION_ID = os.getenv("LOCATION_ID")
GROUP_SIZE = os.getenv("GROUP_SIZE")

MEETING_TITLE = os.getenv("MEETING_TITLE")
USERNAME = os.getenv("USERNAME")
PIN = os.getenv("PIN")

DEFAULT_RETRY = 600  # 10 mins

# ========================
# 🪵 LOGGING
# ========================

def log(msg):
    now_mdt = datetime.now(ZoneInfo("America/Edmonton"))
    now_utc = datetime.utcnow()
    print(f"[UTC {now_utc.strftime('%H:%M:%S')} | MDT {now_mdt.strftime('%H:%M:%S')}] {msg}")

log("⏱️ Printing time... ⏱️ ")

# ========================
# ⏱️ TIME-GATE LOGIC
# ========================

def should_run_now():
    now = datetime.now(ZoneInfo("America/Edmonton"))

    # Example: only act between 8:55–9:05 AM
    if now.hour >= 15 and now.minute >= 01:
        return True
    if now.hour == 14 and now.minute <= 55:
        return True

    return False


if not should_run_now():
    log("⏳ Outside execution window. Exiting.")
    log("⏱️ Printing time... ⏱️ ")
    exit()

# ========================
# ⏱️ RETRY LOGIC
# ========================

def get_retry_interval():
    now = datetime.now(ZoneInfo("America/Edmonton"))

    # ✅ 11 PM → 1 AM window
    if now.hour == 23 or now.hour == 0:
        log("⚡ Turbo Mode ACTIVE (11PM–1AM MDT) → retry every 60 sec")
        return 60

    return DEFAULT_RETRY

# ========================
# 🎯 TIME PREFERENCES
# ========================

PREFERRED_RANGES = [
    ("6:00 pm", "7:30 pm"),
    ("6:30 pm", "8:00 pm"),
    ("6:00 pm", "7:00 pm"),
    ("6:30 pm", "7:30 pm"),
]

# ========================
# 🚦 RUN DATE CHECK
# ========================

today = datetime.now(ZoneInfo("America/Edmonton")).strftime("%Y-%m-%d")

log(f"🎯 RUN_DATES: {RUN_DATES}")
log(f"🎯 BOOKING_DATES: {BOOKING_DATES}")

if RUN_DATES and today not in RUN_DATES:
    log(f"🛑 Today {today} not in RUN_DATES. Exiting.")
    exit()

log(f"✅ Today {today} allowed. Starting bot...")

# ========================
# 🚀 BROWSER
# ========================

options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")
options.binary_location = "/usr/bin/google-chrome"

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 20)

# ========================
# 🔁 MAIN LOOP
# ========================

while True:
    try:
        for DATE in BOOKING_DATES:

            DATE = DATE.strip()  # ✅ FIXED BUG HERE

            URL = f"https://www.calgarylibrary.ca/events-and-programs/book-a-space/book-a-room?date={DATE}&location={LOCATION_ID}&groupsize={GROUP_SIZE}"

            log(f"🌐 Opening page for booking date: {DATE}")
            driver.get(URL)

            # Click View Availability
            try:
                btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@data-view-availability]")))
                driver.execute_script("arguments[0].click();", btn)
                log("✅ Clicked View Availability")
            except:
                log(f"⏳ Not open yet for {DATE}")
                raise Exception("Not open")

            time.sleep(2)

            # Get slots
            slots = driver.find_elements(By.XPATH, "//ul[@data-times-list]//input[@data-time-slot]")

            available = []
            for s in slots:
                if s.is_enabled():
                    sid = s.get_attribute("id")
                    label = driver.find_element(By.XPATH, f"//label[@for='{sid}']").text.strip()
                    available.append((label, s))

            if not available:
                log(f"⏳ No slots yet for {DATE}")
                continue

            labels = [x[0] for x in available]
            log(f"🧮 Slots for {DATE}: {labels}")

            # Match preferred range
            start_slot = end_slot = None
            for start, end in PREFERRED_RANGES:
                if start in labels and end in labels:
                    start_slot = next(x for x in available if x[0] == start)
                    end_slot = next(x for x in available if x[0] == end)
                    log(f"🎯 Found {start} → {end}")
                    break

            if not start_slot:
                log("⏳ Preferred not found")
                continue

            # Select
            driver.execute_script("arguments[0].click();", start_slot[1])
            driver.execute_script("arguments[0].click();", end_slot[1])

            # Book
            book_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-booking-book-button]")))
            driver.execute_script("arguments[0].click();", book_btn)

            # Fill form
            wait.until(EC.visibility_of_element_located((By.ID, "room-booking-login-form")))

            driver.find_element(By.ID, "room-booking-form-meeting-title").send_keys(MEETING_TITLE)
            driver.find_element(By.ID, "room-booking-form-cardnumber").send_keys(USERNAME)
            driver.find_element(By.ID, "room-booking-form-password").send_keys(PIN)

            # Submit
            driver.find_element(By.XPATH, "//form[@id='room-booking-login-form']//button[@type='submit']").click()

            log(f"🎉 SUCCESS for {DATE}")
            driver.quit()
            exit()

        retry = get_retry_interval()
        log(f"🔁 Retry in {retry} sec\n")
        time.sleep(retry)

    except Exception as e:
        retry = get_retry_interval()
        log(f"⚠️ Error: {e}")
        log(f"🔁 Retry in {retry} sec\n")
        time.sleep(retry)
