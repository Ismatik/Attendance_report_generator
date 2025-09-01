import requests
import pandas
from datetime import datetime, timedelta
from configs import BASE_URL, ACCESS_TOKEN, MAX_WORKERS, NUMBER_OF_DAYS
from configs import PLANNED_START_TIME, PLANNED_END_TIME, PLANNED_WORK_DURATION_MINUTES

all_records = []

for pin_id in range(1, MAX_WORKERS):
    user_info = {}
    # 1. First, get the employee's basic information
    try:
        user_info_url = f"{BASE_URL}/api/person/get/{pin_id}?access_token={ACCESS_TOKEN}"
        response = requests.get(user_info_url, timeout=10)
        if response.status_code == 200:
            user_data = response.json().get('data', {})
            if user_data: # Check if data is not None or empty
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

    # 2. Now, get the attendance records for this employee
    first_last_url = (
        f"{BASE_URL}/api/v2/transaction/firstInAndLastOut/{pin_id}?"
        f"pageNo=1&pageSize={NUMBER_OF_DAYS}&access_token={ACCESS_TOKEN}"
    )
    try:
        response = requests.get(first_last_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        daily_records = data.get('data', {}).get('data', [])

        # 3. Handle case where the employee has NO attendance records at all
        if not daily_records:
            print(f"No attendance records found for PIN #{pin_id}.")
            all_records.append({
                "ID": pin_id,
                "FIO": f"{user_info.get('name', '')} {user_info.get('lastName', '')}".strip(),
                "Department": user_info.get('deptName', 'N/A'),
                "Date": "N/A",
                "Day of the week": "N/A",
                "Schedule": "N/A",
                "Planned time": "N/A",
                "Actual attendance": "No records found",
                "Actual Time": "No records found",
                "Transaction count": 0,
                "Late": "N/A",
                "Overwork": "N/A",
                "difference": "N/A"
            })
            continue

        print(f"Processing PIN #{pin_id}. Found {len(daily_records)} daily records.")
        
        # 4. Process each daily record found
        for record in daily_records:
            first_in_str = record.get('firstInTime')
            last_out_str = record.get('lastOutTime')

            # 5. Handle case where a specific day has INCOMPLETE data
            if not first_in_str or not last_out_str:
                # Try to get the date from whichever timestamp is available
                date_source_str = first_in_str or last_out_str
                attendance_date_str = date_source_str.split(' ')[0]
                day_of_week = datetime.strptime(attendance_date_str, '%Y-%m-%d').strftime('%A')
                
                all_records.append({
                    "ID": pin_id,
                    "FIO": f"{user_info.get('name', '')} {user_info.get('lastName', '')}".strip(),
                    "Department": user_info.get('deptName', 'N/A'),
                    "Date": attendance_date_str,
                    "Day of the week": day_of_week,
                    "Schedule": f"{PLANNED_START_TIME.strftime('%H:%M')} - {PLANNED_END_TIME.strftime('%H:%M')}",
                    "Planned time": PLANNED_WORK_DURATION_MINUTES,
                    "Actual attendance": "Incomplete Data",
                    "Actual Time": "Incomplete Data",
                    "Transaction count": "N/A",
                    "Late": "Incomplete Data",
                    "Overwork": "Incomplete Data",
                    "difference": "Incomplete Data"
                })
                continue # Move to the next day's record

            # 6. Process a normal, complete daily record
            first_in_dt = datetime.strptime(first_in_str, '%Y-%m-%d %H:%M:%S')
            last_out_dt = datetime.strptime(last_out_str, '%Y-%m-%d %H:%M:%S')
            
            attendance_date = first_in_dt.date()
            planned_start_dt = datetime.combine(attendance_date, PLANNED_START_TIME)
            planned_end_dt = datetime.combine(attendance_date, PLANNED_END_TIME)

            actual_duration = last_out_dt - first_in_dt
            actual_duration_minutes = actual_duration.total_seconds() / 60
            
            lateness = max(first_in_dt - planned_start_dt, timedelta(0))
            overwork = max(last_out_dt - planned_end_dt, timedelta(0))
            difference_minutes = actual_duration_minutes - PLANNED_WORK_DURATION_MINUTES
            
            date_str = attendance_date.strftime('%Y-%m-%d')
            day_of_week = first_in_dt.strftime('%A')
            
            transaction_count = 0
            trans_url = (
                f"{BASE_URL}/api/v2/transaction/person/{pin_id}?"
                f"startDate={date_str}&endDate={date_str}&access_token={ACCESS_TOKEN}"
            )
            try:
                trans_response = requests.get(trans_url, timeout=10)
                trans_response.raise_for_status()
                trans_data = trans_response.json()
                data_dict = trans_data.get('data')
                if isinstance(data_dict, dict):
                    transaction_count = data_dict.get('total', 0)
            except requests.RequestException as e:
                print(f"Could not fetch transaction count for PIN #{pin_id} on {date_str}. Error: {e}")

            all_records.append({
                "ID": pin_id,
                "FIO": f"{user_info.get('name', '')} {user_info.get('lastName', '')}".strip(),
                "Department": user_info.get('deptName', 'N/A'),
                "Date": date_str,
                "Day of the week": day_of_week,
                "Schedule": f"{PLANNED_START_TIME.strftime('%H:%M')} - {PLANNED_END_TIME.strftime('%H:%M')}",
                "Planned time": PLANNED_WORK_DURATION_MINUTES,
                "Actual attendance": f"{first_in_dt.strftime('%H:%M:%S')} - {last_out_dt.strftime('%H:%M:%S')}",
                "Actual Time": str(actual_duration),
                "Transaction count": transaction_count,
                "Late": str(lateness),
                "Overwork": str(overwork),
                "difference": f"{difference_minutes:.0f} min"
            })

    except requests.RequestException as e:
        print(f"An error occurred while processing attendance for PIN #{pin_id}: {e}")
    except (ValueError, KeyError):
        print(f"Could not parse attendance data for PIN #{pin_id}. Skipping.")

# --- Save to Excel ---
if all_records:
    print(f"\nProcessed all workers. Total records created: {len(all_records)}.")
    report_df = pandas.DataFrame(all_records)
    output_filename = "monthly_attendance_report_with_calculations.xlsx"
    report_df.to_excel(output_filename, index=False)
    print(f"Report successfully saved as {output_filename}")
else:
    print("No data was collected. The report was not generated.")