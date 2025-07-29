import requests
import json
import re
from datetime import datetime
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import math

base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
print(base_path)
os.chdir(base_path)
# 设置阈值(好评率和浏览量)(不满足条件则降低阈值，但最低不低于50% 0)
download_score_threshold = 80  # 好评率阈值
download_view_threshold = 1000  # 浏览量阈值
# 设置空列表
no_result = []
# 设置日期
date = datetime.now().strftime('%Y-%m-%d')
# 设置缓存路径
# cache = 'Auto/Full-Auto/cache/cache.json'
cache = 'Auto/Full-Auto/cache/new_main_cache.json'
id_cache = 'Auto/Full-Auto/cache/id_cache.json'


def wilson_lower_bound(like, dislike, confidence=0.95):
    n = like + dislike
    if n == 0:
        return 0
    # 根据置信度选择z值
    if confidence == 0.90:
        z = 1.645
    elif confidence == 0.95:
        z = 1.96
    elif confidence == 0.99:
        z = 2.576
    else:
        z = 1.96  # 默认95%
    phat = like / n
    denominator = 1 + z*z/n
    numerator = phat + z*z/(2*n) - z * math.sqrt((phat*(1-phat) + z*z/(4*n)) / n)
    return round(numerator / denominator, 2)


def makedir():
    os.makedirs('Auto/Full-Auto/cache', exist_ok=True)
    os.makedirs('往期剿灭', exist_ok=True)
    os.makedirs('资源关', exist_ok=True)
    for _stage, item in all_dict['主题曲'].items():
        i = get_stage_info(item[0]['stage_id'])
        os.makedirs(f'主线/{i} {_stage}', exist_ok=True)


def write_to_file(file_path, content):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(content, file, ensure_ascii=False, indent=4)


def load_data(path):
    if os.path.exists(cache):
        with open(path, 'r', encoding='utf-8') as file:
            return json.load(file)
    else:
        return {}


def build_main_new_cache(_cache_dict, cat_three, _id: str, now_upload_time: str):
    chapter = get_cat_three_info(cat_three_dict, cat_three, "cat_two")
    _id = str(_id)
    if chapter not in _cache_dict:
        _cache_dict[chapter] = {}
    if cat_three not in _cache_dict[chapter]:
        _cache_dict[chapter][cat_three] = {}
    _cache_dict[chapter][cat_three][_id] = now_upload_time
    return _cache_dict


def build_id_cache(_cache_dict, _id, file_path: str):
    _id = str(_id)
    if _id not in _cache_dict:
        _cache_dict[_id] = [file_path]
    elif file_path not in _cache_dict[_id]:
        for file in _cache_dict[_id]:
            directory, filename = os.path.split(file)
            if directory == os.path.dirname(file_path):
                _cache_dict[_id].remove(file)
        _cache_dict[_id].append(file_path)
    return _cache_dict


def compare_main_new_cache(new_cache_dict, cat_three, _id, now_upload_time):
    chapter = get_cat_three_info(cat_three_dict, cat_three, "cat_two")
    before_upload_time = new_cache_dict.get(chapter, {}).get(cat_three, {}).get(str(_id), '')
    return before_upload_time == now_upload_time


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
        _key = get_cat_three_info(cat_three_dict, content[key], "stage_id")
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
    return add_level_data(response.json()['data']) if response.ok else []


def add_level_data(ld):
    """
    添加关卡数据
    :param ld: 关卡数据
    :return: 无返回值
    """
    if not os.path.exists("Auto/Full-Auto/cache/add_level.json"):
        return ld
    with open("Auto/Full-Auto/cache/add_level.json", 'r', encoding='utf-8') as f:
        add_data = json.load(f)
    ld = ld + add_data
    # write_to_file("log/new_level_data.json", ld, True)
    return ld


def calculate_percent(item):
    like, dislike = item.get('like', 0), item.get('dislike', 0)
    # 增加评分人数限制，人数不足10人则返回0
    if like + dislike < 10:
        return 0
    return round(like / (like + dislike) * 100, 2) if like + dislike > 0 else 0


def get_stage_id_info(_stage_dict, stage_id, key):  # 通过stage_id获取信息,失败返回stage_id
    return _stage_dict.get(stage_id, [{}])[0].get(key, stage_id)


def get_cat_three_info(_cat_three_dict, cat_three, key):  # 通过cat_three获取信息,失败返回cat_three
    return _cat_three_dict.get(cat_three, [{}])[0].get(key, cat_three)


def get_stage_info(text):  # 返回第一个-前的整数
    match = re.search(r"(\d+)-", text)
    if match:
        return int(match.group(1))
    else:
        return None


def replace_dir_char(text):
    for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
        text = text.replace(char, '')
    return text


def generate_filename(stage_id, data, mode, cat_two, stage_name=None):
    if not stage_name:
        stage_name = get_stage_id_info(stage_dict, stage_id, "cat_three")
    _stage = get_stage_info(stage_name)
    opers = data.get('opers') if data.get('opers') is not None else []
    groups = data.get('groups') if data.get('groups') is not None else []
    names_parts = ['+'.join(oper.get('name', '') for oper in opers),
                   '+'.join(group.get('name', '') for group in groups)]
    names = '+'.join(part for part in names_parts if part)  # 只连接非空的部分
    names = replace_dir_char(names)
    if data.get("difficulty", 0) == 1:
        stage_name = "(仅普通)" + stage_name
    if len(names) > 50:
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


def cache_delete_save(_cache_dict, found_ids, id_list, cat_three):
    global id_cache_dict
    missing_ids = set(id_list) - found_ids
    for missing_id in missing_ids:
        print(id_list, found_ids, f"未找到 {cat_three} - {missing_id}")
        _cache_dict = build_main_new_cache(cache_dict, cat_three, missing_id, "已删除")
        file_paths = id_cache_dict.get(missing_id, [])
        if file_paths:
            id_cache_dict[missing_id] = []
            for file_path in file_paths:
                directory, filename = os.path.split(file_path)
                new_file_path = os.path.join(directory, f"(已删除){filename}")
                try:
                    os.rename(file_path, new_file_path)
                    id_cache_dict[missing_id].append(new_file_path)
                except FileNotFoundError:
                    print(f"{file_path} 不存在")
    return _cache_dict


def less_search(keyword):
    url = f"https://prts.maa.plus/copilot/query?page=1&limit=999&levelKeyword={keyword}&desc=true&orderBy=views"
    _headers = {
        "Origin": "https://zoot.plus",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
    }
    _response = requests.get(url, headers=_headers)
    if _response.ok:
        return build_dict2(_response.json()['data']['data'], "stageName")
    else:
        print(f"请求 {keyword} 失败")


def get_complete_content(_id):
    _headers = {
        "Origin": "https://zoot.plus",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
    }
    try:
        response = requests.get(f"https://prts.maa.plus/copilot/get/{_id}", headers=_headers)
        if response.ok:
            data = response.json()
            if data.get('status_code') == 200:
                content = json.loads(data['data']['content'])
                return content
            else:
                print(f"Failed to fetch content for ID {_id}, error code: {data.get('status_code')}")
        else:
            print(f"Failed to fetch content for ID {_id}, HTTP status: {response.status_code}")
    except Exception as e:
        print(f"get_complete_content异常，已跳过：ID={_id}, 错误：{e}")
    return None


def less_filter_data(data, stage_id, path_mode=1, filter_mode=0):
    global no_result, cache_dict, id_cache_dict
    all_data = data.get(stage_id)
    cat_three = get_stage_id_info(stage_dict, stage_id, "cat_three")
    cat_two = get_stage_id_info(stage_dict, stage_id, "cat_two")
    id_list = [str(key) for key, value in cache_dict.get(cat_two, {}).get(cat_three, {}).items() if value != "已删除"]
    found_ids = set()
    if all_data:
        download_amount = 0
        # 先计算所有作业的wilson得分和热度得分
        scores = []
        hot_scores = []
        for item in all_data:
            like = item.get('like', 0)
            dislike = item.get('dislike', 0)
            view = item.get('views', 0)
            score = wilson_lower_bound(like, dislike)
            hot_score = round(score * math.log10(view + 1), 2)
            scores.append(score)
            hot_scores.append(hot_score)
        max_score = max(scores) if scores and max(scores) > 0 else 1
        max_hot_score = max(hot_scores) if hot_scores and max(hot_scores) > 0 else 1
        if filter_mode == 0:
            score_threshold = download_score_threshold
            view_threshold = download_view_threshold
        else:
            score_threshold = 80
            view_threshold = -1  # 保证只搜索一次
        while not download_amount:
            for idx, item in enumerate(all_data):
                view = item.get('views', 0)
                found_ids.add(str(item['id']))
                relative_score = round((scores[idx] / max_score), 4) * 100 if max_score else 0
                relative_hot_score = round((hot_scores[idx] / max_hot_score), 4) * 100 if max_hot_score else 0
                if relative_score >= score_threshold and view >= view_threshold:
                    if compare_main_new_cache(cache_dict, cat_three, item['id'], item['upload_time']):
                        download_amount += 1
                        continue
                    if id_cache_dict.get(str(item['id'])):
                        for file in id_cache_dict[str(item['id'])]:
                            if os.path.exists(file):
                                os.remove(file)
                                print(f"Removed {file}")
                    content = get_complete_content(item['id'])
                    file_path = generate_filename(stage_id, content, path_mode, cat_two, cat_three)
                    content['doc']['details'] = f"——————————\n作业更新日期: {item['upload_time']}\n统计更新日期: {date}\n相对评分：{relative_score}%  相对热度：{relative_hot_score}%\n来源：{item['uploader']}  ID：{item['id']}\n——————————\n" + content['doc']['details']
                    print(f"{file_path} {relative_score}% {view} 成功下载")
                    write_to_file(file_path, content)
                    cache_dict = build_main_new_cache(cache_dict, cat_three, item['id'], item['upload_time'])
                    id_cache_dict = build_id_cache(id_cache_dict, item['id'], file_path)
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
        print(f"{stage_id} 无数据")
    cache_dict = cache_delete_save(cache_dict, found_ids, id_list, cat_three)


def less_search_stage(key1):
    # 搜索主线关卡
    less_dict = less_search(key1)
    for stage_id in less_dict:
        if any(substring in stage_id for substring in ['#f#', 'easy', '#s']):
            continue
        less_filter_data(less_dict, stage_id)


def less_search_camp():
    # 搜索剿灭作战
    less_dict = less_search('剿灭作战')
    for stage_id in less_dict:
        less_filter_data(less_dict, stage_id, 2)


def resource_stage_search():
    # 搜索资源关
    less_dict = less_search('资源收集')
    for stage_id in less_dict:
        less_filter_data(less_dict, stage_id, 3, 1)


# 获取关卡数据，构建字典
level_data = get_level_data()
stage_dict = build_dict(level_data, 'stage_id')
cat_three_dict = build_dict(level_data, 'cat_three')
all_dict = build_complex_dict(level_data)
makedir()
# 读取缓存
cache_dict = load_data(cache)
id_cache_dict = load_data(id_cache)
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
# 保存缓存
write_to_file(cache, cache_dict)
write_to_file(id_cache, id_cache_dict)
print(f"搜索完毕，共耗时 {round(last - now, 2)} s.\n")
print('No_result: ', no_result)
