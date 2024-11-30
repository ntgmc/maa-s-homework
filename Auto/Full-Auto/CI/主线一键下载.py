import requests
import json
import re
from datetime import datetime
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

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
# TODO: 根据id缓存文件名


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


def build_cache(_cache_dict, _id, now_upload_time: str, others: str):
    _cache_dict[f"{_id}-{others}"] = now_upload_time
    return _cache_dict


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
        _cache_dict[_id].append(file_path)
    return _cache_dict


def compare_cache(_cache_dict, _id, now_upload_time: str, others: str):  # 最新返回True，需更新返回False
    before_upload_time = _cache_dict.get(f"{_id}-{others}", '')
    return before_upload_time == now_upload_time


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
    opers = data.get('opers', [])
    groups = data.get('groups', [])
    names_parts = ['+'.join(oper.get('name', '') for oper in opers),
                   '+'.join(group.get('name', '') for group in groups)]
    names = '+'.join(part for part in names_parts if part)  # 只连接非空的部分
    names = replace_dir_char(names)
    if data.get("difficulty", 0) == 1:
        stage_name = "(仅普通)" + stage_name
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


def cache_delete_save(_cache_dict, found_ids, id_list, cat_three):
    missing_ids = set(id_list) - found_ids
    for missing_id in missing_ids:
        print(id_list, found_ids, f"未找到 {cat_three} - {missing_id}")
        _cache_dict = build_main_new_cache(cache_dict, cat_three, missing_id, "已删除")
    return _cache_dict


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


def less_filter_data(data, stage_id, path_mode=1, filter_mode=0):
    global no_result, cache_dict, id_cache_dict
    all_data = data.get(stage_id)
    cat_three = get_stage_id_info(stage_dict, stage_id, "cat_three")
    cat_two = get_stage_id_info(stage_dict, stage_id, "cat_two")
    id_list = [str(key) for key, value in cache_dict.get(cat_two, {}).get(cat_three, {}).items() if value != "已删除"]
    found_ids = set()
    if all_data:
        download_amount = 0
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
                found_ids.add(str(item['id']))
                if percent >= score_threshold and view >= view_threshold:
                    # if compare_cache(cache_dict, item['id'], item['upload_time'], cat_three):
                    #     # print(f"{item['id']} 未改变数据，无需更新")
                    #     download_amount += 1
                    #     continue
                    if compare_main_new_cache(cache_dict, cat_three, item['id'], item['upload_time']):
                        download_amount += 1
                        continue
                    content = json.loads(item['content'])
                    file_path = generate_filename(stage_id, content, path_mode, cat_two, cat_three)
                    content['doc']['details'] = f"作业更新日期: {item['upload_time']}\n统计更新日期: {date}\n好评率：{percent}%  浏览量：{view}\n来源：{item['uploader']}  ID：{item['id']}\n" + content['doc']['details']
                    print(f"{file_path} {percent}% {view} 成功下载")
                    write_to_file(file_path, content)
                    # cache_dict = build_cache(cache_dict, item['id'], item['upload_time'], cat_three)
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
        # no_result.append(keyword)
        print(f"{stage_id} 无数据")
    cache_dict = cache_delete_save(cache_dict, found_ids, id_list, cat_three)


def less_search_stage(key1):
    # 搜索主线关卡
    less_dict = less_search(key1)
    for stage_id in less_dict:
        if any(substring in stage_id for substring in ['#f#', 'easy']):
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
