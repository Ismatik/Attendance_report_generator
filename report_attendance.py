import pandas
import requests
import openpyxl

overall_data = pandas.DataFrame()
for j in range(1,505):
  url = f"http://192.168.7.39:8098/api/v2/transaction/firstInAndLastOut/{j}?pageNo=1&pageSize=10&access_token=4ECD44C895F358C5DB39BC69C29B1006"
  response = requests.get(url)
  data = response.json()
  info_list = data.get('data', {})
  info_list = info_list.get('data', []) if isinstance(info_list, dict) else []

  # Collect printed info into a list of dicts
  row_list = []
  for i in info_list:
      print(f"PIN #{j}\n: {i['name']} {i['lastName']} {i['firstInTime']} {i['lastOutTime']} DEPARTMENT CODE {i['deptCode']}\n\n")
      row_list.append({
          "PIN": j,
          "Name": i.get('name', ''),
          "LastName": i.get('lastName', ''),
          "FirstInTime": i.get('firstInTime', ''),
          "LastOutTime": i.get('lastOutTime', ''),
          "DeptCode": i.get('deptCode', '')
      })

  # Concatenate to overall_data
  if row_list:
      df = pandas.DataFrame(row_list)
      overall_data = pandas.concat([overall_data, df], ignore_index=True)

if not overall_data.empty:
  overall_data.to_excel("overall_attendance_report.xlsx", index=False)