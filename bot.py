from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

# ========================
# 🔧 INPUT PARAMETERS
# ========================

DATE = os.getenv("DATE")
LOCATION_ID = os.getenv("LOCATION_ID")
GROUP_SIZE = os.getenv("GROUP_SIZE")

MEETING_TITLE = os.getenv("MEETING_TITLE")
USERNAME = os.getenv("NAME")   # ✅ replaced PHONE with USERNAME
PIN = os.getenv("PIN")

RETRY_INTERVAL = int(os.getenv("RETRY_INTERVAL", "10"))  # seconds

# ========================
# 🌐 URL
# ========================

URL = f"https://www.calgarylibrary.ca/events-and-programs/book-a-space/book-a-room?date={DATE}&location={LOCATION_ID}&groupsize={GROUP_SIZE}"

# ========================
# 🧠 PREFERRED TIME RANGES
# ========================

PREFERRED_RANGES = [
    ("6:00 pm", "7:30 pm"),
    ("6:30 pm", "8:00 pm"),
    ("6:00 pm", "7:00 pm"),
    ("6:30 pm", "7:30 pm")
]

# ========================
# 🪵 LOGGING HELPER
# ========================

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

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
# 🔁 RETRY LOOP
# ========================

while True:
    try:
        log("🌐 Opening page...")
        driver.get(URL)

        # ========================
        # 🔹 CLICK VIEW AVAILABILITY
        # ========================
        try:
            view_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@data-view-availability]")))
            driver.execute_script("arguments[0].click();", view_btn)
            log("✅ Clicked View Availability")
        except:
            log("⏳ Availability not open yet...")
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

        if not available_slots:
            log("⏳ No available slots yet...")
            raise Exception("No slots")

        log(f"🧮 Available slots: {[s[0] for s in available_slots]}")

        # ========================
        # 🔹 MATCH PREFERRED RANGE
        # ========================
        selected_start = None
        selected_end = None

        slot_labels = [s[0] for s in available_slots]

        for start, end in PREFERRED_RANGES:
            if start in slot_labels and end in slot_labels:
                log(f"🎯 Found slot: {start} → {end}")
                selected_start = next(s for s in available_slots if s[0] == start)
                selected_end = next(s for s in available_slots if s[0] == end)
                break

        if not selected_start:
            log("⏳ Preferred time not available yet...")
            raise Exception("Preferred slot not found")

        # ========================
        # 🔹 SELECT TIME
        # ========================
        log("👉 Selecting time slots...")
        driver.execute_script("arguments[0].click();", selected_start[1])
        time.sleep(1)
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

        log("🎉 Booking submitted successfully!")
        break

    except Exception as e:
        log(f"⚠️ Retry triggered: {str(e)}")
        log(f"🔁 Retrying in {RETRY_INTERVAL} seconds...\n")
        time.sleep(RETRY_INTERVAL)

# ========================
# 🏁 CLEANUP
# ========================

time.sleep(5)
driver.quit()
