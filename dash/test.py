from datetime import datetime, timedelta
import requests

# url = "https://portal-api.emcs.cucloud.net/query"
# data = {
#     "range": {
#         "from": str(datetime.now() - timedelta(days=30)),
#         "to": str(datetime.now())
#     },
#     "targets": [
#         {
#             "payload": {
#                 "additional": [
#                     "noagg",
#                 ]
#             },
#             "target": "GameFarmRoadWeatherStation.TAVG_H_F",
#         }
#     ]
# }

url = "https://portal-api.emcs.cucloud.net/query"
data = {
    "range": {
        "from": str(datetime.now() - timedelta(days=30)),
        "to": str(datetime.now())
    },
    "targets": [
        {
            "target": "GameFarmRoadWeatherStation.TAVG_H_F",
        }
    ]
}
request = requests.post(url, json=data)
print(request)
request = requests.post(url, json=data)
print(request.json())