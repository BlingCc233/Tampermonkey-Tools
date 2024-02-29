__author__ = 'BlingCc'

# FUCK 乐健

import requests
import json
from Config import headers

main_url = "https://cpes.legym.cn/education/app/activity/"
list_url = main_url + "getActivityList"

data = {
    "name": "",
    "campus": "",
    "page": 1,
    "size": 20,
    "state": 1,
    "topicId": "",
    "week": ""
}

response = requests.post(list_url, json=data, headers=headers)
response_json = response.json()
desired_item = None
items = response_json.get('data').get('items')

for item in items:
    if item["stateName"] == "活动进行中" and item["name"] == "第三空间周四格拉斯哥清水河校区" and item["address"] == "综训馆及周围体育场":
        desired_item = item
        break

item_id = None

if desired_item:
    item_id = desired_item["id"]
    print("item ID:", item_id)
else:
    print("item not found in the response.")


sign_url = main_url + "signUp"


data = {
    "activityId": item_id
}

response = requests.post(sign_url, headers=headers, data=json.dumps(data))
response_json = response.json()

if response_json.get('data', {}).get('success'):
    print('报名成功')
else:
    print(response_json.get('data').get('reason'))
