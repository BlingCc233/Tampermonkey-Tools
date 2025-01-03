import json
import httpx
import os
import random
import re


headers = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9",
    "authorization": 你的认证信息,
    "priority": "u=1, i",
    "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"macOS\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "cookie": 你的认证信息,
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
        # 如果这个value的list的某个元素包含“不玩原”，continue,
        if any(x for x in value[2:] if "不玩原" in x):
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
