import json
import httpx
import os
import random
import re


headers = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9",
    "authorization": "T1VJH6Le0eIT1dkvie0dGsjFeJCoGGmRKQ3C5aZJzmVZdnrQ4MfGbWOGaOtH1+modZwZ1jZ280VyK+OKY3pWqxFV0NmVCncdsmt43qf4c6syYICxbGUU2oXEHYUgxeLG6U8e+AmCJk7eS02zjegZ",
    "priority": "u=1, i",
    "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"macOS\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "cookie": "_ga=GA1.3.1931977924.1694421581; _ga_QYKCGTHFGK=GS1.3.1702393553.1.0.1702393553.0.0.0; v3hW_2132_smile=10D1; v3hW_2132_home_readfeed=1722356043; v3hW_2132_nofavfid=1; v3hW_2132_lastvisit=1733923290; newbbs_a0th=0_oALTyffUdY7VCdnnOZrN589Z; newbbs_auth=265527__ovgX1z3dY7VCdhoIZt_6hOB; v3hW_2132_saltkey=hQFWZSOs; v3hW_2132_auth=309fHkeu1NOD0%2BlySYMT9xJmrYf6dYtWut%2FwmXMnHKCVTWnkSpE3AvY%2Bj4ZY6zHg%2BWsFLj1IPXjg2QSzo22PKD4LjA4; v3hW_2132_ulastactivity=583fJpWBGmfBThOCW3ECrC8pbRYzwiLnoJQSYBhnDCqpnYI5LCaL; v3hW_2132_sendmail=1; v3hW_2132_viewid=uid_287813; v3hW_2132_home_diymode=1; v3hW_2132_sid=VMtsuw; v3hW_2132_lip=117.173.139.37%2C1735920702; v3hW_2132_lastact=1735920809%09home.php%09space",
    "Referer": "https://bbs.uestc.edu.cn/thread/2235968?page=1",
    "Referrer-Policy": "strict-origin-when-cross-origin"
}

page = 1
url = f"https://bbs.uestc.edu.cn/star/api/v1/post/list?thread_id=2235968&page={page}&thread_details=1&forum_details=1"
response = httpx.get(url, headers=headers)

if response.status_code == 200:
    data = response.json()
    # page更新为data["data"]["total"] / data["data"]["page_size"]
    page = data["data"]["total"] / data["data"]["page_size"]
    # 向上取整
    page = int(page) + 1

typography = {}
typography_list = []

for i in range(1, page + 1):
    url = f"https://bbs.uestc.edu.cn/star/api/v1/post/list?thread_id=2235968&page={i}&thread_details=1&forum_details=1"

    response = httpx.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()


        for item in data["data"]["rows"]:
            if item.get('author_id') == None or item.get('message') == None:
                continue
            if item['author_id'] not in typography:
                    typography[item['author_id']] = []
                    typography[item['author_id']].append(item['author'])
                    typography[item['author_id']].append(item['author_id'])
                    typography[item['author_id']].append(item['message'])
                    continue
            typography[item['author_id']].append(item['message'])

    else:
        print(f"Failed to fetch page {i}, status code: {response.status_code}")



# 把键值对转换为列表
for key, value in typography.items():
        # 如果这个value的list的某个元素包含“不玩原”或“已经买”，continue,
        if any(x for x in value[2:] if "不玩原" in x) or any(x for x in value[2:] if "已经买" in x):
            continue
        # 过滤自己
        if key == 265527:
            continue
        typography_list.append({value[0] : value[1:]})


# 把列表shuffle五次
for i in range(5):
    random.shuffle(typography_list)

for item in typography_list:
    print(item)

# 从列表中随机取出1个元素
print(f"\n\n\t恭喜这位pu：\n\t{random.choice(typography_list)}")
