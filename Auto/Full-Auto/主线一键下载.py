import requests
import json
import re
from datetime import datetime
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# 设置阈值(好评率和浏览量)(不满足条件则降低阈值，但最低不低于50% 0)
download_score_threshold = 80  # 好评率阈值
download_view_threshold = 1000  # 浏览量阈值
# 设置资源关
resource_level = ["wk_toxic_5", "wk_armor_5", "wk_fly_5", "wk_kc_6", "wk_melee_6", "pro_a_1",
                  "pro_a_2", "pro_b_1", "pro_b_2", "pro_c_1", "pro_c_2", "pro_d_1", "pro_d_2"]
# 设置空列表
no_result = []
# 设置日期
date = datetime.now().strftime('%Y-%m-%d')
# 设置缓存路径
cache = os.path.join('Auto/Full-auto', "cache", 'cache.json')


def makedir():
    os.makedirs('Auto/Full-auto/cache', exist_ok=True)
    os.makedirs('往期剿灭', exist_ok=True)
    os.makedirs('资源关', exist_ok=True)
    for _stage, item in all_dict['主题曲'].items():
        i = get_stage_info(item[0]['stage_id'])
        os.makedirs(f'主线/{i} {_stage}', exist_ok=True)


def write_to_file(file_path, content):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(content, file, ensure_ascii=False, indent=4)


def save_data(data):
    with open(cache, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def load_data():
    with open(cache, 'r', encoding='utf-8') as file:
        return json.load(file)


def build_cache(_cache_dict, _id, now_upload_time: str, others: str):
    _cache_dict[f"{_id}-{others}"] = now_upload_time
    return _cache_dict


def compare_cache(_cache_dict, _id, now_upload_time: str, others: str):  # 最新返回True，需更新返回False
    before_upload_time = _cache_dict.get(f"{_id}-{others}", '')
    if before_upload_time == now_upload_time:
        return True
    else:
        return False


def build_dict(data, key: str):  # key为生成的字典的键
    _dict = {}
    for member in data:
        _key = member[key]
        if _key in _dict:
            _dict[_key].append(member)
        else:
            _dict[_key] = [member]
    return _dict


def build_dict2(data, key: str):  # key为生成的字典的键
    _dict = {}
    for member in data:
        content = json.loads(member['content'])
        _key = get_cat_three_info(content[key], "stage_id")
        if _key in _dict:
            _dict[_key].append(member)
        else:
            _dict[_key] = [member]
    return _dict


def build_complex_dict(data):
    complex_dict = {}
    for member in data:
        category = member['cat_one']  # 获取分类
        key = member['cat_two']  # 获取子分类
        # 确保每个主分类下有一个字典，用于存储子分类的列表
        if category not in complex_dict:
            complex_dict[category] = {}
        # 确保子分类下有一个列表，用于存储成员的JSON对象
        if key not in complex_dict[category]:
            complex_dict[category][key] = []
        # 将成员添加到对应的列表中
        complex_dict[category][key].append(member)
    return complex_dict


def get_level_data():
    response = requests.get('https://prts.maa.plus/arknights/level')
    return response.json()['data'] if response.ok else []


def calculate_percent(item):
    like, dislike = item.get('like', 0), item.get('dislike', 0)
    return round(like / (like + dislike) * 100, 2) if like + dislike > 0 else 0


def get_stage_id_info(stage_id, key):  # 通过stage_id获取信息,失败返回stage_id
    return stage_dict.get(stage_id, [{}])[0].get(key, stage_id)


def get_cat_three_info(cat_three, key):  # 通过cat_three获取信息,失败返回cat_three
    return cat_three_dict.get(cat_three, [{}])[0].get(key, cat_three)


def get_stage_info(text):  # 返回第一个-前的整数
    match = re.search(r"(\d+)-", text)
    if match:
        return int(match.group(1))
    else:
        return None


def replace_special_char(text):
    return text.replace('/', '').replace('\\', '')


def generate_filename(stage_id, data, mode, cat_two, stage_name=None):
    if not stage_name:
        stage_name = get_stage_id_info(stage_id, "cat_three")
    _stage = get_stage_info(stage_name)
    opers = data.get('opers', [])
    groups = data.get('groups', [])
    names_parts = ['+'.join(oper.get('name', '') for oper in opers),
                   '+'.join(group.get('name', '') for group in groups)]
    names = '+'.join(part for part in names_parts if part)  # 只连接非空的部分
    names = replace_special_char(names)
    if len(names) > 100:
        names = "文件名过长不予显示"
    if mode == 1:
        file_path = f'主线/{_stage} {cat_two}/{stage_name}_{names}.json'
    elif mode == 2:
        file_path = f'往期剿灭/{stage_name}_{names}.json'
    elif mode == 3:
        file_path = f'资源关/{stage_name}_{names}.json'
    else:
        file_path = f'{stage_name}_{names}.json'
    return file_path


def search(keyword, path_mode=1, filter_mode=0, cat_two=None, cat_three=None):
    if any(substring in keyword for substring in ['#f#', 'easy']):
        return
    url = f"https://prts.maa.plus/copilot/query?page=1&limit=15&levelKeyword={keyword}&desc=true&orderBy=views"
    _headers = {
        "Origin": "https://prts.plus",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
    }
    _response = requests.get(url, headers=_headers)
    if _response.ok:
        filter_data(_response.json(), keyword, path_mode, filter_mode, cat_two, cat_three)
    else:
        print(f"请求 {keyword} 失败")


def less_search(keyword):
    url = f"https://prts.maa.plus/copilot/query?page=1&limit=999&levelKeyword={keyword}&desc=true&orderBy=views"
    _headers = {
        "Origin": "https://prts.plus",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
    }
    _response = requests.get(url, headers=_headers)
    if _response.ok:
        return build_dict2(_response.json()['data']['data'], "stage_name")
    else:
        print(f"请求 {keyword} 失败")


def filter_data(data, keyword, path_mode, filter_mode, cat_two, cat_three):
    global no_result, cache_dict
    total = data['data'].get('total', 0)
    if total > 0:
        download_amount = 0
        if filter_mode == 0:
            score_threshold = download_score_threshold
            view_threshold = download_view_threshold
        else:
            score_threshold = 80
            view_threshold = -1  # 保证只搜索一次
        while not download_amount:
            for item in data['data']['data']:
                percent = calculate_percent(item)
                view = item.get('views', 0)
                if percent >= score_threshold and view >= view_threshold:
                    if compare_cache(cache_dict, item['id'], item['upload_time'], cat_three):
                        # print(f"{item['id']} 未改变数据，无需更新")
                        download_amount += 1
                        continue
                    content = json.loads(item['content'])
                    file_path = generate_filename(keyword, content, path_mode, cat_two, cat_three)
                    content['doc'][
                        'details'] = f"统计日期：{date}\n好评率：{percent}%  浏览量：{view}\n来源：{item['uploader']}  ID：{item['id']}\n" + \
                                     content['doc']['details']
                    print(f"{file_path} {percent}% {view} 成功下载")
                    write_to_file(file_path, content)
                    cache_dict = build_cache(cache_dict, item['id'], item['upload_time'], cat_three)
                    download_amount += 1
            if not download_amount:
                if score_threshold > 50:
                    score_threshold -= 5
                else:
                    view_threshold -= 200
                if view_threshold < 0:
                    print(f"{keyword} 无符合50% 0的数据 不再重试")
                    no_result.append(keyword)
                    break
                print(f"{keyword} 无符合条件的数据，降低阈值为{score_threshold}% {view_threshold}重试")
    else:
        # no_result.append(keyword)
        print(f"{keyword} 无数据")


def less_filter_data(data, stage_id, path_mode=1, filter_mode=0):
    global no_result, cache_dict
    all_data = data.get(stage_id)
    if all_data:
        download_amount = 0
        cat_three = get_stage_id_info(stage_id, "cat_three")
        cat_two = get_stage_id_info(stage_id, "cat_two")
        if filter_mode == 0:
            score_threshold = download_score_threshold
            view_threshold = download_view_threshold
        else:
            score_threshold = 80
            view_threshold = -1  # 保证只搜索一次
        while not download_amount:
            for item in all_data:
                percent = calculate_percent(item)
                view = item.get('views', 0)
                if percent >= score_threshold and view >= view_threshold:
                    if compare_cache(cache_dict, item['id'], item['upload_time'], cat_three):
                        # print(f"{item['id']} 未改变数据，无需更新")
                        download_amount += 1
                        continue
                    content = json.loads(item['content'])
                    file_path = generate_filename(stage_id, content, path_mode, cat_two, cat_three)
                    content['doc'][
                        'details'] = f"统计日期：{date}\n好评率：{percent}%  浏览量：{view}\n来源：{item['uploader']}  ID：{item['id']}\n" + \
                                     content['doc']['details']
                    print(f"{file_path} {percent}% {view} 成功下载")
                    write_to_file(file_path, content)
                    cache_dict = build_cache(cache_dict, item['id'], item['upload_time'], cat_three)
                    download_amount += 1
            if not download_amount:
                if score_threshold > 50:
                    score_threshold -= 5
                else:
                    view_threshold -= 200
                if view_threshold < 0:
                    print(f"{stage_id} 无符合50% 0的数据 不再重试")
                    no_result.append(stage_id)
                    break
                print(f"{stage_id} 无符合条件的数据，降低阈值为{score_threshold}% {view_threshold}重试")
    else:
        # no_result.append(keyword)
        print(f"{stage_id} 无数据")


def less_search_stage(key1):
    less_dict = less_search(key1)
    for key2 in less_dict:
        if any(substring in key2 for substring in ['#f#', 'easy']):
            continue
        less_filter_data(less_dict, key2)


def search_camp(keyword):
    for level in all_dict['剿灭作战'][keyword]:
        search(level['stage_id'], 2, cat_three=level['cat_three'])


def less_search_camp():
    less_dict = less_search('剿灭作战')
    for key2 in less_dict:
        less_filter_data(less_dict, key2, 2)


def resource_stage_search():
    for level in resource_level:
        cat_three = get_stage_id_info(level, "cat_three")
        search(level, 3, 1, cat_three=cat_three)


level_data = get_level_data()
stage_dict = build_dict(level_data, 'stage_id')
cat_three_dict = build_dict(level_data, 'cat_three')
all_dict = build_complex_dict(level_data)
makedir()
if os.path.exists(cache):
    cache_dict = load_data()
else:
    cache_dict = {}
now = datetime.now().timestamp()
# 创建一个线程池
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = []
    # 添加任务到线程池
    for stage in all_dict['主题曲']:
        futures.append(executor.submit(less_search_stage, stage))
    futures.append(executor.submit(less_search_camp))
    futures.append(executor.submit(resource_stage_search))

    # 等待所有任务完成
    for future in as_completed(futures):
        try:
            future.result()
        except Exception as e:
            print(f"Task generated an exception: {e}")
last = datetime.now().timestamp()
save_data(cache_dict)
print(f"搜索完毕，共耗时 {round(last - now, 2)} s.\n")
print('No_result: ', no_result)
