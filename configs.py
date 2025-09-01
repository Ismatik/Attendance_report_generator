from datetime import time

# Main configuration file for attendance reporting script.
BASE_URL = "http://192.168.7.39:8098"
ACCESS_TOKEN = "4ECD44C895F358C5DB39BC69C29B1006"
NUMBER_OF_DAYS = 30 # How many recent days of data to fetch per worker
MAX_WORKERS = 505   # The script will check for workers from PIN 1 up to this number

# --- Schedule Configuration ---
# Define the planned start and end times for a standard workday.
PLANNED_START_TIME = time(8, 30)
PLANNED_END_TIME = time(18, 30)

# Assuming a 10-hour schedule with a 1-hour lunch break = 9 hours of work.
PLANNED_WORK_DURATION_MINUTES = 540
LUNCH_BREAK_MINUTES = 60
