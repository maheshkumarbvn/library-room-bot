from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from datetime import datetime
from zoneinfo import ZoneInfo

# ========================
# 🔧 INPUT PARAMETERS
# ========================

# List of dates when bot is allowed to RUN (YYYY-MM-DD)
# RUN_DATES = os.getenv("RUN_DATES", "").split(",")  # e.g. "2026-05-01,2026-05-02"

# List of dates to BOOK rooms for
# BOOKING_DATES = os.getenv("BOOKING_DATES", "").split(",")  # replaces DATE

LOCATION_ID = os.getenv("LOCATION_ID")
GROUP_SIZE = os.getenv("GROUP_SIZE")

MEETING_TITLE = os.getenv("MEETING_TITLE")
USERNAME = os.getenv("USERNAME")
PIN = os.getenv("PIN")

# Default retry = 5 minutes
DEFAULT_RETRY_INTERVAL = int(os.getenv("RETRY_INTERVAL", "600"))

# ========================
# 🪵 LOGGING HELPER
# ========================

def log(msg):
    now = datetime.now(ZoneInfo("America/Edmonton"))
    print(f"[{now.strftime('%Y-%m-%d %H:%M:%S %Z')}] {msg}")

# ========================
# 🧠 TIME-BASED RETRY LOGIC
# ========================

def get_retry_interval():
    now = datetime.now(ZoneInfo("America/Edmonton"))

    # 🚀 Turbo mode between 11:00 PM – 11:50 PM
    if now.hour == 21 and now.minute <= 50:
        log("⚡ Turbo mode active (11:00–11:50 PM Calgary) → retry every 30 sec")
        return 30

    return DEFAULT_RETRY_INTERVAL

# ========================
# 🧠 PREFERRED TIME RANGES
# ========================

PREFERRED_RANGES = [
    ("6:00 pm", "7:30 pm"),
    ("6:00 pm", "7:00 pm"),
    ("6:30 pm", "7:30 pm"),
    ("6:30 pm", "8:00 pm")
]

# ========================
# 🧠 RUN_DATES
# ========================
RUN_DATES: "2026-04-06"

# RUN_DATES = ["2026-04-05,2026-04-06,2026-04-07"]

# ========================
# 🧠 BOOKING_DATES
# ========================
BOOKING_DATES: "2026-05-06"
# BOOKING_DATES = ["2026-05-06,2026-05-07"]

log(f"🎯 RUN_DATES: {RUN_DATES}")
log(f"🎯 BOOKING_DATES: {BOOKING_DATES}")
log(f"🎯 PREFERRED_RANGES: {PREFERRED_RANGES}")

# ========================
# 🚦 CHECK IF TODAY IS RUN DATE
# ========================

today_calgary = datetime.now(ZoneInfo("America/Edmonton")).strftime("%Y-%m-%d")

if RUN_DATES and today_calgary not in RUN_DATES:
    log(f"🛑 Today ({today_calgary}) is NOT in RUN_DATES. Exiting.")
    exit()
else:
    log(f"✅ Today ({today_calgary}) is allowed. Continuing...")

# ========================
# 🚀 START BROWSER
# ========================

options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.binary_location = "/usr/bin/google-chrome"

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 25)

# ========================
# 🔁 MAIN LOOP
# ========================

while True:
    try:
        for DATE in BOOKING_DATES:

            URL = f"https://www.calgarylibrary.ca/events-and-programs/book-a-space/book-a-room?date={DATE}&location={LOCATION_ID}&groupsize={GROUP_SIZE}"

            log(f"🌐 Opening page for booking date: {DATE}")
            log(f"🔗 URL: {URL}")

            driver.get(URL)

            # ========================
            # 🔹 CLICK VIEW AVAILABILITY
            # ========================
            try:
                view_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@data-view-availability]")))
                driver.execute_script("arguments[0].click();", view_btn)
                log("✅ Clicked View Availability")
            except:
                log(f"⏳ Availability not open yet for {DATE}")
                raise Exception("Availability not ready")

            time.sleep(2)

            # ========================
            # 🔹 FETCH SLOTS
            # ========================
            slots = driver.find_elements(By.XPATH, "//ul[@data-times-list]//input[@data-time-slot]")

            available_slots = []

            for slot in slots:
                if slot.is_enabled():
                    slot_id = slot.get_attribute("id")
                    label = driver.find_element(By.XPATH, f"//label[@for='{slot_id}']").text.strip()
                    available_slots.append((label, slot))

            log(f"📡 Slot scan complete for {DATE}")

            if not available_slots:
                log(f"⏳ No slots available yet for {DATE}")
                raise Exception("No slots available")

            log(f"🧮 Available slots for {DATE}: {[s[0] for s in available_slots]}")

            # ========================
            # 🔹 MATCH PREFERRED RANGE
            # ========================
            selected_start = None
            selected_end = None

            slot_labels = [s[0] for s in available_slots]

            for start, end in PREFERRED_RANGES:
                if start in slot_labels and end in slot_labels:
                    log(f"🎯 Found slot for {DATE}: {start} → {end}")
                    selected_start = next(s for s in available_slots if s[0] == start)
                    selected_end = next(s for s in available_slots if s[0] == end)
                    break

            if not selected_start:
                log(f"⏳ Preferred slot not found yet for {DATE}")
                continue  # try next date

            # ========================
            # 🔹 SELECT TIME
            # ========================
            log(f"👉 Selecting time slots for {DATE}...")
            driver.execute_script("arguments[0].click();", selected_start[1])
            time.sleep(2)
            driver.execute_script("arguments[0].click();", selected_end[1])

            # ========================
            # 🔹 CLICK BOOK
            # ========================
            book_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-booking-book-button]")))
            driver.execute_script("arguments[0].click();", book_btn)
            log("📌 Clicked Book")

            # ========================
            # 🔹 FILL FORM
            # ========================
            wait.until(EC.visibility_of_element_located((By.ID, "room-booking-login-form")))

            driver.find_element(By.ID, "room-booking-form-meeting-title").send_keys(MEETING_TITLE)
            driver.find_element(By.ID, "room-booking-form-cardnumber").send_keys(USERNAME)
            driver.find_element(By.ID, "room-booking-form-password").send_keys(PIN)

            log("✍️ Form filled")

            # ========================
            # 🔹 SUBMIT
            # ========================
            submit_btn = driver.find_element(By.XPATH, "//form[@id='room-booking-login-form']//button[@type='submit']")
            driver.execute_script("arguments[0].click();", submit_btn)

            log(f"🎉 Booking SUCCESS for {DATE}!")
            driver.quit()
            exit()  # ✅ ALWAYS EXIT ON SUCCESS

        # If no booking succeeded for any date → retry
        retry_interval = get_retry_interval()
        log(f"🔁 No booking yet. Retrying in {retry_interval} seconds...\n")
        time.sleep(retry_interval)

    except Exception as e:
        retry_interval = get_retry_interval()
        log(f"⚠️ Error: {str(e)}")
        log(f"🔁 Retrying in {retry_interval} seconds...\n")
        time.sleep(retry_interval)

# ========================
# 🏁 CLEANUP (fallback)
# ========================

driver.quit()
