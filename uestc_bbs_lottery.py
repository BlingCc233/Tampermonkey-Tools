import json
import os
import random
import re

pattern = re.compile(r'^uestc-\d{4}-\d{2}-\d{2}\.json$')

dir = "/Users/ccbling/tmp"

for filename in os.listdir(dir):
    if pattern.match(filename):
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)


typography = {}


for item in data:
    if item.get('MuiTypography-root') == None or item.get('rich-text-content') == None:
        continue
    if item['MuiTypography-root'] not in typography:
            typography[item['MuiTypography-root']] = []
            typography[item['MuiTypography-root']].append(item['rich-text-content'])
            continue
    typography[item['MuiTypography-root']].append(item['rich-text-content'])

typography_list = []

# 把键值对转换为列表
for key, value in typography.items():
        # 如果这个value的list的某个元素包含“不玩原”，continue,
        if any(x for x in value if "不玩原" in x):
            continue
        # 过滤自己
        if key == "BlingCc":
             continue
        typography_list.append({key : value})

# 把列表shuffle五次
for i in range(5):
    random.shuffle(typography_list)

for item in typography_list:
    print(item)

# 从列表中随机取出1个元素
print(f"\n\n\t恭喜这位pu：\n", random.choice(typography_list))
