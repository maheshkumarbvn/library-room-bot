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
NAME = os.getenv("NAME")
EMAIL = os.getenv("EMAIL")
PHONE = os.getenv("PHONE")
PIN = os.getenv("PIN")

PREFERRED_TIME = os.getenv("PREFERRED_TIME")  # e.g. "5:59 AM,6:05 AM"

# ========================
# 🌐 URL
# ========================
URL = f"https://www.calgarylibrary.ca/events-and-programs/book-a-space/book-a-room?date={DATE}&location={LOCATION_ID}&groupsize={GROUP_SIZE}"

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

print("🚀 Opening page...")
driver.get(URL)

time.sleep(5)

print(f"📍 URL Loaded: {driver.current_url}")
print("📄 Page title:", driver.title)

# ========================
# 🎯 FIND SLOTS
# ========================
print("🔍 Locating available time slots...")

slots = driver.find_elements(By.XPATH, "//button[contains(@class,'fc-timegrid-slot')]")

print(f"🧮 Total slots found: {len(slots)}")

if len(slots) == 0:
    print("❌ No slots detected. Page may not have loaded correctly.")
    driver.quit()
    exit()

print("📝 Available slots:")
for s in slots:
    try:
        print("-", s.text.strip())
    except:
        pass

preferred_times = [t.strip() for t in PREFERRED_TIME.split(",")]

found_start = None

# ========================
# 🎯 SELECT START TIME
# ========================
for slot in slots:
    slot_text = slot.text.strip()
    for pref in preferred_times:
        if pref in slot_text:
            print(f"✅ Matching start slot found: {slot_text}")
            found_start = slot
            break
    if found_start:
        break

if not found_start:
    print("❌ Preferred start time not found. Exiting.")
    driver.quit()
    exit()

# Click start slot
print("👉 Clicking start time...")
driver.execute_script("arguments[0].click();", found_start)

time.sleep(2)

# ========================
# 🎯 HANDLE END TIME (GENERIC ATTEMPT)
# ========================
print("⏳ Attempting to select end time...")

try:
    # Try to find next clickable time slots (common UI pattern)
    selectable_slots = driver.find_elements(By.XPATH, "//button[contains(@class,'fc-timegrid-slot')]")

    if len(selectable_slots) > 1:
        # Pick the next slot after the selected one
        print("📌 Selecting next available slot as end time...")
        driver.execute_script("arguments[0].click();", selectable_slots[1])
    else:
        print("⚠️ Could not determine end time automatically.")

except Exception as e:
    print("⚠️ End time selection failed:", str(e))

# ========================
# 📝 WAIT FOR FORM
# ========================
print("🧾 Waiting for booking form...")

try:
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
    print("✅ Form loaded.")
except:
    print("❌ Form did not load.")
    driver.quit()
    exit()

# ========================
# ✍️ FILL FORM
# ========================
def fill_field(label_text, value):
    try:
        field = driver.find_element(By.XPATH, f"//label[contains(text(),'{label_text}')]/following::input[1]")
        field.send_keys(value)
        print(f"✍️ Filled {label_text}")
    except Exception as e:
        print(f"⚠️ Could not fill {label_text}: {e}")

fill_field("Name", NAME)
fill_field("Email", EMAIL)
fill_field("Phone", PHONE)

# Meeting title
try:
    driver.find_element(By.XPATH, "//input[contains(@name,'title')]").send_keys(MEETING_TITLE)
    print("✍️ Meeting title filled")
except:
    print("⚠️ Meeting title field not found")

# PIN
try:
    driver.find_element(By.XPATH, "//input[contains(@type,'password')]").send_keys(PIN)
    print("🔐 PIN entered")
except:
    print("ℹ️ No PIN field present")

# ========================
# ✅ SUBMIT
# ========================
try:
    submit_btn = driver.find_element(By.XPATH, "//button[contains(text(),'Book')]")
    print("🚀 Clicking Book button...")
    submit_btn.click()
except Exception as e:
    print("❌ Submit button not found or clickable:", e)

time.sleep(5)

print("🏁 Booking flow completed (check result above).")

driver.quit()
