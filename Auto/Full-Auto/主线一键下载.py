import requests
import json
import re
from datetime import datetime
import os

# 设置阈值
download_score_threshold = 80  # 好评率阈值
download_view_threshold = 1000  # 浏览量阈值
# 设置stage_name
tough = [10, 11, 12, 13, 14]
main = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
sub = [2, 3, 4, 5, 6, 7, 9]  # TODO: 增加sub适配
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
max_hard_level = {
    5: 4,
    6: 4,
    7: 4,
    8: 4,
    9: 6,
    10: 3,
    11: 4,
    12: 4,
    13: 4,
    14: 4
}


def get_current_date():
    return datetime.now().strftime('%Y-%m-%d')


date = get_current_date()


def write_to_file(file_path, content):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(content, file, ensure_ascii=False, indent=4)


def pad_zero(i):
    return str(i).zfill(2)


def build_dict(data, key: str):  # key为生成的字典的键
    _dict = {}
    for member in data:
        _key = member[key]
        if _key in _dict:
            _dict[_key].append(member)
        else:
            _dict[_key] = [member]
    return _dict


def get_level_data():
    url = 'https://prts.maa.plus/arknights/level'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()['data']
    else:
        return []


def calculate_percent(item):
    like = item.get('like', 0)
    dislike = item.get('dislike', 0)
    total = like + dislike
    if total == 0:
        return 0
    else:
        return round(like / total * 100, 2)


def get_level_name(stage_id):
    return stage_dict.get(stage_id, [{}])[0].get('cat_three', '')


def extract_info(text):  # TODO: 增加sub适配
    match = re.search(r"(\d+)-", text)
    if match:
        return int(match.group(1))
    else:
        return None


def generate_filename_mode3(data):
    stage_name = get_level_name(data.get('stage_name', ''))
    _stage = extract_info(stage_name)
    opers = data.get('opers', [])
    groups = data.get('groups', [])
    names_parts = ['+'.join(oper.get('name', '') for oper in opers),
                   '+'.join(group.get('name', '') for group in groups)]
    names = '+'.join(part for part in names_parts if part)  # 只连接非空的部分
    return f'./download/主线/第{_stage}章/{stage_name}_{names.replace("/", "")}.json'


def search(keyword):
    url = f"https://prts.maa.plus/copilot/query?page=1&limit=15&levelKeyword={keyword}&desc=true&orderBy=views"
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
            while not download_amount:
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
                if not download_amount:
                    if score_threshold > 50:
                        score_threshold -= 5
                    else:
                        view_threshold -= 200
                    print(f"{keyword} 无符合条件的数据，降低阈值为{score_threshold}% {view_threshold}重试")
        else:
            print(f"{keyword} 无数据")
    else:
        print(f"请求 {keyword} 失败")


def tough_stage_search(_stage):
    for level in range(1, max_level.get(_stage, 0) + 1):
        search(f"tough_{pad_zero(_stage)}-{pad_zero(level)}")


def main_stage_search(_stage):
    for level in range(1, max_level.get(_stage, 0) + 1):
        search(f"main_{pad_zero(_stage)}-{pad_zero(level)}")


def hard_stage_search(_stage):
    for level in range(1, max_hard_level.get(_stage, 0) + 1):
        search(f"hard_{pad_zero(_stage)}-{pad_zero(level)}")


def bat_search():
    for _stage in tough:
        tough_stage_search(_stage)
    for _stage in main:
        main_stage_search(_stage)
    for _stage in max_hard_level:
        hard_stage_search(_stage)


if not os.path.exists(f'./download/主线'):
    os.makedirs(f'./download/主线')
for stage in max_level:
    if not os.path.exists(f'./download/主线/第{stage}章'):
        os.makedirs(f'./download/主线/第{stage}章')
stage_dict = build_dict(get_level_data(), 'stage_id')
bat_search()
