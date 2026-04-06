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


DATE = os.getenv("DATE")    # "2026-05-06"
LOCATION_ID = os.getenv("LOCATION_ID")  # Seton Library
GROUP_SIZE = os.getenv("GROUP_SIZE") # 14

MEETING_TITLE = os.getenv("MEETING_TITLE")
NAME = os.getenv("NAME")
EMAIL = os.getenv("EMAIL")
PHONE = os.getenv("PHONE")
PIN = os.getenv("PIN")

PREFERRED_TIME = os.getenv("PREFERRED_TIME")    # PREFERRED_TIME = "5:59 AM,6:05 AM,6:15 AM"
# GitHub uses UTC, not Calgary time.
# Calgary Time	UTC
# 11:59 PM	    5:59

# ========================
# 🌐 URL BUILDER
# ========================
URL = f"https://www.calgarylibrary.ca/events-and-programs/book-a-space/book-a-room?date={DATE}&location={LOCATION_ID}&groupsize={GROUP_SIZE}"

# ========================
# 🚀 START BROWSER
# ========================
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.binary_location = "/usr/bin/google-chrome"

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 20)

driver.get(URL)

print("Page opened... waiting for slots")

# ========================
# ⏳ WAIT FOR SLOTS
# ========================
time.sleep(5)  # allow JS load

# ========================
# 🎯 FIND TIME SLOT
# ========================
slots = driver.find_elements(By.XPATH, "//button[contains(@class,'fc-timegrid-slot')]")

found = False
for slot in slots:
    if PREFERRED_TIME in slot.text:
        print(f"Found slot: {slot.text}")
        slot.click()
        found = True
        break

if not found:
    print("Preferred slot not found. Exiting.")
    driver.quit()
    exit()

# ========================
# 📝 WAIT FOR FORM
# ========================
print("Waiting for booking form...")
wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))

# ========================
# ✍️ FILL FORM
# ========================
def fill_field(label_text, value):
    field = driver.find_element(By.XPATH, f"//label[contains(text(),'{label_text}')]/following::input[1]")
    field.send_keys(value)

fill_field("Name", NAME)
fill_field("Email", EMAIL)
fill_field("Phone", PHONE)

# Meeting title
driver.find_element(By.XPATH, "//input[contains(@name,'title')]").send_keys(MEETING_TITLE)

# PIN (if exists)
try:
    driver.find_element(By.XPATH, "//input[contains(@type,'password')]").send_keys(PIN)
except:
    pass

# ========================
# ✅ SUBMIT
# ========================
submit_btn = driver.find_element(By.XPATH, "//button[contains(text(),'Book')]")
submit_btn.click()

print("Booking attempted 🚀")

time.sleep(5)
driver.quit()
