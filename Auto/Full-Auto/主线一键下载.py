import requests
import json
import re
from datetime import datetime
import os

# 设置阈值
download_score_threshold = 80  # 好评率阈值
download_view_threshold = 1000  # 浏览量阈值
# 设置stage_name
all_stage = range(15)
tough = [10, 11, 12, 13, 14]
main = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
sub = [2, 3, 4, 5, 6, 7, 9]  # TODO: 增加sub适配
# 设置剧情关 第二个数据为实际-1
plot = {
    6: [6, 12],
    7: [1, 6],
    9: [1, 7],
    10: [1, 12],
    11: [4, 9],
    12: [1, 10],
    13: [1, 8],
    14: [1, 12]
}
# 设置最大关卡数
max_level = {
    0: 11,
    1: 12,
    2: 10,
    3: 8,
    4: 10,
    5: 10,
    6: 14,
    7: 16,
    8: 17,
    9: 17,
    10: 15,
    11: 18,
    12: 18,
    13: 19,
    14: 19
}


def get_current_date():
    return datetime.now().strftime('%Y-%m-%d')


date = get_current_date()


def write_to_file(file_path, content):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(content, file, ensure_ascii=False, indent=4)


def pad_zero(i):
    return str(i).zfill(2)


def calculate_percent(item):
    like = item.get('like', 0)
    dislike = item.get('dislike', 0)
    total = like + dislike
    if total == 0:
        return 0
    else:
        return round(like / total * 100, 2)


def find_position(lst, level):
    for i, num in enumerate(lst):
        if level < num:
            return level + i
    return level + len(lst)


def extract_info(text):  # TODO: 增加sub适配
    pattern = r"(main|tough)_([0-9]+)-([0-9]+)"
    match = re.match(pattern, text)
    if match:
        name = match.group(1)
        _stage = int(match.group(2))
        level = int(match.group(3))
        return name, _stage, level
    else:
        return None


def generate_stage_name(stage_name):
    name, _stage, level = extract_info(stage_name)
    if _stage in tough:
        if name == 'main':
            prefix = "标准"
        elif name == 'tough':
            prefix = "磨难"
        else:
            prefix = "剧情"
    else:
        prefix = ""
    return f"{prefix}{_stage}-{find_position(plot.get(_stage, []), level)}", _stage


def generate_filename_mode3(data):
    stage_name, _stage = generate_stage_name(data.get('stage_name', ''))
    opers = data.get('opers', [])
    groups = data.get('groups', [])
    names_parts = ['+'.join(oper.get('name', '') for oper in opers),
                   '+'.join(group.get('name', '') for group in groups)]
    names = '+'.join(part for part in names_parts if part)  # 只连接非空的部分
    return f'./download/主线/第{_stage}章/{stage_name}_{names.replace("/", "")}.json'


def search(keyword):
    url = f"https://prts.maa.plus/copilot/query?page=1&limit=15&levelKeyword={keyword}&desc=true&orderBy=hot"
    _headers = {
        "Origin": "https://prts.plus",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
    }

    _response = requests.get(url, headers=_headers)
    if _response.status_code == 200:
        data = _response.json()
        total = data['data'].get('total', 0)
        if total > 0:
            download_amount = 0
            score_threshold = download_score_threshold
            view_threshold = download_view_threshold
            while True:
                for item in data['data']['data']:
                    percent = calculate_percent(item)
                    view = item.get('views', 0)
                    if percent >= score_threshold and view >= view_threshold:
                        content = json.loads(item['content'])
                        file_path = generate_filename_mode3(content)
                        content['doc']['details'] = f"统计日期：{date}\n好评率：{percent}%  浏览量：{view}\n来源：{item['uploader']}  ID：{item['id']}\n" + content['doc']['details']
                        print(f"{file_path} {percent}% {view} 成功下载")
                        write_to_file(file_path, content)
                        download_amount += 1
                if download_amount == 0:
                    score_threshold -= 5
                    view_threshold -= 200
                    print(f"{keyword} 无符合条件的数据，降低阈值为{score_threshold}% {view_threshold}重试")
                else:
                    break


def bat_search():
    for _stage in tough:
        for level in range(1, max_level.get(_stage, 0) + 1):
            search(f"tough_{pad_zero(_stage)}-{pad_zero(level)}")
    for _stage in main:
        for level in range(1, max_level.get(_stage, 0) + 1):
            search(f"main_{pad_zero(_stage)}-{pad_zero(level)}")


if not os.path.exists(f'./download/主线'):
    os.makedirs(f'./download/主线')
for stage in all_stage:
    if not os.path.exists(f'./download/主线/第{stage}章'):
        os.makedirs(f'./download/主线/第{stage}章')
# search("main_14-01")
bat_search()
