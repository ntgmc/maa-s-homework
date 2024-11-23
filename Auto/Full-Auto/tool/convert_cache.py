import json
import os
import requests

base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
print(base_path)
os.chdir(base_path)
# 旧缓存文件路径
old_cache_file_path = 'Auto/Full-Auto/cache/cache.json'
old_cache_file_path2 = 'Auto/Full-Auto/cache/activity_cache.json'
# 新缓存文件路径
new_cache_file_path = 'Auto/Full-Auto/cache/new_cache.json'
new_cache_file_path2 = 'Auto/Full-Auto/cache/new_activity_cache.json'


def add_level_data(ld):
    if not os.path.exists("Auto/Full-Auto/cache/add_level.json"):
        return ld
    with open("Auto/Full-Auto/cache/add_level.json", 'r', encoding='utf-8') as f:
        add_data = json.load(f)
    ld = ld + add_data
    # write_to_file("log/new_level_data.json", ld, True)
    return ld


def get_level_data():
    response = requests.get('https://prts.maa.plus/arknights/level')
    return add_level_data(response.json()['data']) if response.ok else []


def build_dict(data, key: str, _dict=None):
    if _dict is None:
        _dict = {}
    for member in data:
        _key = member[key]
        if _key in _dict:
            _dict[_key].append(member)
        else:
            _dict[_key] = [member]
    return _dict


def get_cat_three_info(cat_three_dict, cat_three, key):  # 通过cat_three获取信息,失败返回cat_three
    return cat_three_dict.get(cat_three, [{}])[0].get(key, cat_three)


def convert_old_cache_to_new(old_path, new_path):
    # 加载旧缓存数据
    with open(old_path, 'r', encoding='utf-8') as file:
        old_cache_data = json.load(file)

    # 初始化新缓存数据结构
    new_cache_data = {
        "悖论": {},
        "模组": {}
    }

    # 转换旧缓存数据到新缓存数据结构
    for key, value in old_cache_data.items():
        parts = key.split('-')
        if len(parts) == 3:
            _id, name, category = parts
            if category == '悖论':
                if name not in new_cache_data["悖论"]:
                    new_cache_data["悖论"][name] = {}
                new_cache_data["悖论"][name][_id] = value
            elif category == '模组':
                if name not in new_cache_data["模组"]:
                    new_cache_data["模组"][name] = {}
                new_cache_data["模组"][name][_id] = value

    # 保存新缓存数据
    with open(new_path, 'w', encoding='utf-8') as file:
        json.dump(new_cache_data, file, ensure_ascii=False, indent=4)


def convert_old_activity_cache_to_new(old_path, new_path):
    # 加载旧缓存数据
    with open(old_path, 'r', encoding='utf-8') as file:
        old_cache_data = json.load(file)

    # 初始化新缓存数据结构
    new_cache_data = {}

    # 转换旧缓存数据到新缓存数据结构
    for key, value in old_cache_data.items():
        _id, rest = key.split('-', 1)
        activity_id = get_cat_three_info(cat_three_all_dict, rest, "stage_id").split('_')[0]
        if activity_id not in new_cache_data:
            new_cache_data[activity_id] = {}
        if rest not in new_cache_data[activity_id]:
            new_cache_data[activity_id][rest] = {}
        new_cache_data[activity_id][rest][_id] = value

    # 保存新缓存数据
    with open(new_path, 'w', encoding='utf-8') as file:
        json.dump(new_cache_data, file, ensure_ascii=False, indent=4)


level_data = get_level_data()
cat_three_all_dict = build_dict(level_data, "cat_three")
# 调用函数进行转换
convert_old_cache_to_new(old_cache_file_path, new_cache_file_path)
convert_old_activity_cache_to_new(old_cache_file_path2, new_cache_file_path2)
