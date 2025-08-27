import pandas
import requests
import openpyxl

# url = "http://192.168.7.39:8098/api/v2/transaction/firstInAndLastOut/166?pageNo=1&pageSize=200&access_token=4ECD44C895F358C5DB39BC69C29B1006"# url = "http://192.168.7.39:8098/api/v2/transaction/firstInAndLastOut/166?pageNo=1&pageSize=200&access_token=4ECD44C895F358C5DB39BC69C29B1006"# url = "http://192.168.7.39:8098/api/v2/transaction/firstInAndLastOut/166?pageNo=1&pageSize=200&access_token=4ECD44C895F358C5DB39BC69C29B1006"


# payload = ""
# headers = {
#   'Cookie': 'SESSION=N2RlMDA5MzQtMGIyYy00MTQ5LWE3NmQtM2Q5Y2ViZjdjN2Jk'
# }

# response = requests.request("GET", url, headers=headers, data=payload)

# data = response.json()
# # If the response is like {"data": [...]}, extract the list
# if isinstance(data, dict) and "data" in data:
#     records = data["data"]
# else:
#     records = data

# df = pandas.DataFrame(records)
# df.to_excel("attendance_report.xlsx", index=False)
# for i in df["data"]:
#   print(i)
