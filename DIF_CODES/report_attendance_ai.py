import requests
import pandas
from datetime import datetime, time, timedelta

# --- Configuration ---
BASE_URL = "http://192.168.7.39:8098"
ACCESS_TOKEN = "4ECD44C895F358C5DB39BC69C29B1006"
NUMBER_OF_DAYS = 30  # How many recent days of data to fetch per worker
MAX_WORKERS = 505    # The script will check for workers from PIN 1 up to this number

# --- Schedule Configuration ---
PLANNED_START_TIME = time(8, 30)
PLANNED_END_TIME = time(18, 30)
PLANNED_WORK_DURATION_MINUTES = 540

# --- Main Script ---
all_records = []

print("Starting to fetch attendance data...")

for pin_id in range(1, MAX_WORKERS):
    user_info = {}
    # 1. Get the employee's basic information
    try:
        user_info_url = f"{BASE_URL}/api/person/get/{pin_id}?access_token={ACCESS_TOKEN}"
        response = requests.get(user_info_url, timeout=10)
        if response.status_code == 200:
            user_data = response.json().get('data', {})
            if user_data:
                user_info['name'] = user_data.get('name', '')
                user_info['lastName'] = user_data.get('lastName', '')
                user_info['deptName'] = user_data.get('deptName', 'N/A')
            else:
                print(f"PIN #{pin_id} exists but returned no data. Skipping.")
                continue
        else:
            print(f"Could not find user with PIN #{pin_id}. Skipping.")
            continue
    except requests.RequestException as e:
        print(f"Error fetching user info for PIN #{pin_id}: {e}. Skipping.")
        continue

    # 2. Get the list of days the employee was active
    first_last_url = (
        f"{BASE_URL}/api/v2/transaction/firstInAndLastOut/{pin_id}?"
        f"pageNo=1&pageSize={NUMBER_OF_DAYS}&access_token={ACCESS_TOKEN}"
    )
    try:
        response = requests.get(first_last_url, timeout=10)
        response.raise_for_status()
        data = response.json()
    
        if data.get('data' , {}) is None:
            continue
        
        active_days_records = data.get('data', {}).get('data', [])

        try:
            if not active_days_records:
                print(f"No attendance records found for PIN #{pin_id}.")
                all_records.append({
                    "ID": pin_id, "FIO": f"{user_info.get('name', '')} {user_info.get('lastName', '')}".strip(),
                    "Department": user_info.get('deptName', 'N/A'), "Date": "N/A", "Day of the week": "N/A",
                    "Actual attendance": "No records found", "Actual Time (minutes)": 0, "Transaction count": 0,
                    "Late": "N/A", "Overwork": "N/A"
                })
                continue
        except AttributeError:
            print(f"Unexpected data format for PIN #{pin_id}. Skipping.")
            continue

        print(f"Processing PIN #{pin_id}. Found {len(active_days_records)} active days.")
        
        # 3. For each active day, get all transactions and build the timeline
        for day_record in active_days_records:
            attendance_date_str = day_record.get('firstInTime', '').split(' ')[0]
            if not attendance_date_str:
                continue

            # Fetch all transactions for this specific day
            trans_url = (
                f"{BASE_URL}/api/v2/transaction/person/{pin_id}?"
                f"startDate={attendance_date_str}&endDate={attendance_date_str}&pageSize=100&access_token={ACCESS_TOKEN}"
            )
            
            timeline_parts = []
            total_duration = timedelta(0)
            transaction_count = 0
            
            try:
                trans_response = requests.get(trans_url, timeout=10)
                trans_response.raise_for_status()
                trans_data = trans_response.json()
                
                transactions = trans_data.get('data', {}).get('data', [])
                transaction_count = trans_data.get('data', {}).get('total', 0)

                if transactions:
                    # Sort transactions by time to ensure correct order
                    transactions.sort(key=lambda x: x['eventTime'])
                    
                    # Pair up transactions (IN/OUT, IN/OUT, ...)
                    for i in range(0, len(transactions) - 1, 2):
                        start_trans = transactions[i]
                        end_trans = transactions[i+1]
                        
                        start_dt = datetime.strptime(start_trans['eventTime'], '%Y-%m-%d %H:%M:%S')
                        end_dt = datetime.strptime(end_trans['eventTime'], '%Y-%m-%d %H:%M:%S')
                        
                        # Add the formatted time pair to our list
                        timeline_parts.append(f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}")
                        # Add the duration of this pair to the total
                        total_duration += (end_dt - start_dt)
            
            except requests.RequestException as e:
                print(f"Could not fetch transaction details for PIN #{pin_id} on {attendance_date_str}. Error: {e}")

            # --- Final Calculations for the day ---
            timeline_str = " -> ".join(timeline_parts) if timeline_parts else "Incomplete Data"
            
            first_in_dt = datetime.strptime(transactions[0]['eventTime'], '%Y-%m-%d %H:%M:%S') if transactions else None
            last_out_dt = datetime.strptime(transactions[-1]['eventTime'], '%Y-%m-%d %H:%M:%S') if len(transactions) > 1 else None

            attendance_date = first_in_dt.date()
            planned_start_dt = datetime.combine(attendance_date, PLANNED_START_TIME)
            planned_end_dt = datetime.combine(attendance_date, PLANNED_END_TIME)
            
            lateness = max(first_in_dt - planned_start_dt, timedelta(0)) if first_in_dt else "N/A"
            overwork = max(last_out_dt - planned_end_dt, timedelta(0)) if last_out_dt else "N/A"

            all_records.append({
                "ID": pin_id,
                "FIO": f"{user_info.get('name', '')} {user_info.get('lastName', '')}".strip(),
                "Department": user_info.get('deptName', 'N/A'),
                "Date": attendance_date_str,
                "Day of the week": datetime.strptime(attendance_date_str, '%Y-%m-%d').strftime('%A'),
                "Actual attendance": timeline_str,
                "Actual Time (minutes)": int(total_duration.total_seconds() / 60),
                "Transaction count": transaction_count,
                "Late": str(lateness),
                "Overwork": str(overwork)
            })

    except requests.RequestException as e:
        print(f"An error occurred while processing attendance for PIN #{pin_id}: {e}")
    except (ValueError, KeyError, IndexError):
        print(f"Could not parse attendance data for PIN #{pin_id}. Skipping.")

# --- Save to Excel ---
if all_records:
    print(f"\nProcessed all workers. Total records created: {len(all_records)}.")
    report_df = pandas.DataFrame(all_records)
    output_filename = "daily_timeline_attendance_report_with_ai.xlsx"
    report_df.to_excel(output_filename, index=False)
    print(f"Report successfully saved as {output_filename}")
else:
    print("No data was collected. The report was not generated.")