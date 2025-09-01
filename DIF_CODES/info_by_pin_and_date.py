# get_single_report_detailed.py
import requests
import pandas
from datetime import datetime, time, timedelta
from configs import BASE_URL, ACCESS_TOKEN
from configs import PLANNED_START_TIME, PLANNED_END_TIME, PLANNED_WORK_DURATION_MINUTES, LUNCH_BREAK_MINUTES

def get_user_input():
    """Gets and validates user input for PIN, start date, and end date."""
    while True:
        try:
            # pin_id = int(input("Enter the worker's PIN: "))
            pin_id = 392
            break
        except ValueError:
            print("Invalid input. Please enter a number for the PIN.")

    while True:
        try:
            # start_date_str = input("Enter the start date (YYYY-MM-DD): ")
            start_date_str = '2025-08-01'
            datetime.strptime(start_date_str, '%Y-%m-%d')
            break
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")

    while True:
        try:
            # end_date_str = input("Enter the end date (YYYY-MM-DD): ")
            end_date_str = '2025-08-28'
            datetime.strptime(end_date_str, '%Y-%m-%d')
            break
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")
            
    return pin_id, start_date_str, end_date_str

def generate_report(pin_id, start_date_str, end_date_str):
    """Fetches data day-by-day and generates the attendance report."""
    report_data = []
    user_info = {}

    # 1. Get User's Name and Department
    try:
        user_info_url = f"{BASE_URL}/api/person/get/{pin_id}?access_token={ACCESS_TOKEN}"
        response = requests.get(user_info_url, timeout=10)
        response.raise_for_status()
        user_data = response.json().get('data')
        if user_data:
            user_info['name'] = user_data.get('name', '')
            user_info['lastName'] = user_data.get('lastName', '')
            user_info['deptName'] = user_data.get('deptName', 'N/A')
        else:
            print(f"Could not find user with PIN #{pin_id}. Exiting.")
            return None, None
    except requests.RequestException as e:
        print(f"Error fetching user info for PIN #{pin_id}: {e}")
        return None, None

    print(f"Fetching data for: {user_info.get('name')} {user_info.get('lastName')}")

    # 2. Create a date range to iterate through each day
    date_range = pandas.date_range(start=start_date_str, end=end_date_str)

    for day in date_range:
        current_day_str = day.strftime('%Y-%m-%d')
        next_day_str = (day + timedelta(days=1)).strftime('%Y-%m-%d')
        print(f"Processing {current_day_str}...")

        try:
            # 3. For each day, fetch ALL transactions using the corrected date logic
            trans_url = (
                f"{BASE_URL}/api/v2/transaction/person/{pin_id}?"
                f"startDate={current_day_str}&endDate={next_day_str}&pageNo=1&pageSize=100&access_token={ACCESS_TOKEN}"
            )
            response = requests.get(trans_url, timeout=10)
            response.raise_for_status()
            
            trans_data = response.json().get('data', {})
            if trans_data not in [None, {}, []]:
                all_day_trans = trans_data.get('data', [])
                transaction_count = trans_data.get('total', 0)
                
                # --- Calculate EntryIN and EntryOut ---
                entry_in_count = 0
                entry_out_count = 0
                for trans in all_day_trans:
                    # Using .get() is safer in case the 'devName' key is missing
                    device_name = trans.get('devName', '')
                    print(device_name)
                    if "Турникет-Вход" in device_name or "Enter tur" in device_name:
                        entry_in_count += 1
                    elif "Турникет-Выход" in device_name or "Exit tur" in device_name:
                        entry_out_count += 1
                
                event_times = [t['eventTime'] for t in all_day_trans]
                
                first_in_str = min(event_times)
                last_out_str = max(event_times)
                
                first_in_dt = datetime.strptime(first_in_str, '%Y-%m-%d %H:%M:%S')
                last_out_dt = datetime.strptime(last_out_str, '%Y-%m-%d %H:%M:%S')
                
                planned_start_dt = datetime.combine(day.date(), PLANNED_START_TIME)
                planned_end_dt = datetime.combine(day.date(), PLANNED_END_TIME)
                
                lateness_delta = max(first_in_dt - planned_start_dt, timedelta(0))
                lateness_minutes = int(lateness_delta.total_seconds() / 60)
                
                overwork_delta = max(last_out_dt - planned_end_dt, timedelta(0))
                overwork_minutes = int(overwork_delta.total_seconds() / 60)

                report_data.append({
                    "Date": current_day_str,
                    "First_in": first_in_dt.strftime('%H:%M:%S'),
                    "Last_out": last_out_dt.strftime('%H:%M:%S'),
                    "EntryIN": entry_in_count,
                    "EntryOut": entry_out_count,
                    "otdel": user_info.get('deptName', 'N/A'),
                    "day_of_the_week": day.strftime('%A'),
                    "supposed_time(min)": PLANNED_WORK_DURATION_MINUTES,
                    "late_for_work(min)": lateness_minutes,
                    "overwork(min)": overwork_minutes
                })
            else:
                print(f"  -> No records found (Absent).")

        except requests.RequestException as e:
            print(f"  -> An error occurred while fetching data for this day: {e}")
        except (ValueError, KeyError) as e:
            print(f"  -> Could not parse data for this day. Error: {e}")

    return report_data, user_info


def main():
    pin_id, start_date, end_date = get_user_input()
    
    report_data, user_info = generate_report(pin_id, start_date, end_date)

    if report_data:
        print(f"\nSuccessfully generated {len(report_data)} records.")
        report_df = pandas.DataFrame(report_data)
        
        user_name = f"{user_info.get('name', 'user')}_{user_info.get('lastName', pin_id)}".strip('_')
        output_filename = f"Report_{user_name}_{start_date}_to_{end_date}.xlsx"
        
        report_df.to_excel(output_filename, index=False)
        print(f"Report successfully saved as: {output_filename}")
    else:
        print("No data was generated for the report.")

if __name__ == "__main__":
    main()