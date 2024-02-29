__author__ = 'BlingCc'

# FUCK 乐健

import requests
import json
from datetime import datetime
from Config import username,password

main_url = "https://cpes.legym.cn/"

#登陆
###
login_url = main_url + "authorization/user/manage/login"
headers = {
    'Content-Type': 'application/json',
    'Accept': '*/*',
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Html5Plus/1.0 (Immersed/20) uni-app',
    'Content-Length': '120',
    'Accept-Language': 'en-US,en;q=0.9'
}
data = {
    'entrance': '1',
    'password': password,
    'userName': username
}
response = requests.post(login_url, headers=headers, data=json.dumps(data))
organizationId = None
accessToken = None
response_data = response.json()

if response_data['code'] == 0:
    organizationId = response_data['data']['organizationId']
    accessToken = response_data['data']['accessToken']
    print("Organization ID:", organizationId)
    print("Access Token:", accessToken)
else:
    print("请求未成功，响应信息：", response_data['message'])
###

#重新包装请求头
###
headers = {
    "Content-Type": "application/json",
    "Accept-Encoding": "gzip, deflate, br",
    "Organization": organizationId,
    "Connection": "keep-alive",
    "Accept": "*/*",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Html5Plus/1.0 (Immersed/20) uni-app",
    "Authorization": "Bearer " + accessToken,
    "Accept-Language": "en-US,en;q=0.9"
}
###

#获取userID
###
uid = None
info_url = main_url + "authorization/user/getBasicInfo"
response = requests.post(info_url, headers=headers)
response_json = response.json()

uid = response_json.get('data').get('id')

print("UID: " + uid)
###

#报名活动
###
list_url = main_url + "education/app/activity/getActivityList"

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

dayOfWeek = datetime.now().isoweekday()
# judge week System
if (dayOfWeek == 1):
    dayOfWeek_CN = "一"
elif (dayOfWeek == 2):
    dayOfWeek_CN = "二"
elif (dayOfWeek == 3):
    dayOfWeek_CN = "三"
elif (dayOfWeek == 4):
    dayOfWeek_CN = "四"
elif (dayOfWeek == 5):
    dayOfWeek_CN = "五"
elif (dayOfWeek == 6):
    dayOfWeek_CN = "六"
else:
    dayOfWeek_CN = "天"
for item in items:
    if item["stateName"] == "活动进行中" and item["name"] == "第三空间周"+dayOfWeek_CN+"格拉斯哥清水河校区" and item["address"] == "综训馆及周围体育场":
        desired_item = item
        break

item_id = None

if desired_item:
    item_id = desired_item["id"]
    print("Activity ID:", item_id)
else:
    print("活动 not found in the response.")
###

#签到
###
signup_url = main_url + "education/app/activity/signUp"


data = {
    "activityId": item_id
}

response = requests.post(signup_url, headers=headers, data=json.dumps(data))
response_json = response.json()

if response_json.get('data', {}).get('success'):
    print('报名成功')
else:
    print(response_json.get('data').get('reason'))

interval_url = main_url + "education/app/activity/checkSignInterval?activityId=" + item_id
response = requests.get(interval_url, headers=headers)
response_json = response.json()
try:
    time_interval = int(response_json.get('data').get('timeInterval')) / 60000
except (TypeError, ValueError):
    time_interval = 0


if time_interval > 0:
    print("距离下次签到：" + str(time_interval) + " 分钟")
else:
    print("签到开始")

sha1 = "f2cec9bdb92c6427ef82a8728c4ca62bca2e94fb"
import hashlib
import random
import string
random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
sha1_hash = hashlib.sha1(item_id.encode()).hexdigest()
print("SHA-1哈希值:", sha1_hash)
# sha1 = sha1_hash

data = {
    "pageType": "activity",
    "activityId": item_id,
    "times": "1",
    "userId": uid,
    "activityType": 0,
    "attainabilityType": 1,
    "signDigital": sha1
}

sign_url = main_url + "education/activity/app/attainability/sign"

response = requests.put(sign_url, json=data, headers=headers)
response_json = response.json()
message = response_json.get("message")
print(message)

#    schedule.every().day.at("08:00").do(sign)# 报名活动
# while (True):
#     # 启动服务
#     schedule.run_pending()
#     time.sleep(1)
