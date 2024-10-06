import json
import os

base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
print(base_path)
os.chdir(base_path)
# 假设旧缓存文件路径为 'Auto/Full-Auto/cache/cache.json'
old_cache_file_path = 'Auto/Full-Auto/cache/cache.json'
# 假设新缓存文件路径为 'Auto/Full-Auto/cache/new_cache.json'
new_cache_file_path = 'Auto/Full-Auto/cache/new_cache.json'


def convert_old_cache_to_new():
    # 加载旧缓存数据
    with open(old_cache_file_path, 'r', encoding='utf-8') as file:
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
    with open(new_cache_file_path, 'w', encoding='utf-8') as file:
        json.dump(new_cache_data, file, ensure_ascii=False, indent=4)


# 调用函数进行转换
convert_old_cache_to_new()
