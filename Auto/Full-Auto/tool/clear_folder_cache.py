import os
import json

base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
print(base_path)
os.chdir(base_path)
# 缓存文件路径（请根据实际情况修改）
ID_CACHE_PATH = 'Auto/Full-Auto/cache/id_cache.json'
ACTIVITY_CACHE_PATH = 'Auto/Full-Auto/cache/new_activity_cache.json'

# 需要清除缓存的作业文件夹路径（如：'【当前活动】引航者试炼 #05/'）
TARGET_DIR = '【当前活动】引航者试炼 #05/'

def clear_id_cache_and_get_ids(target_dir, id_cache_path=ID_CACHE_PATH):
    """
    清除id_cache中指定文件夹的作业，并返回被清除的id集合
    """
    if not os.path.exists(id_cache_path):
        print(f"未找到缓存文件: {id_cache_path}")
        return set()
    with open(id_cache_path, 'r', encoding='utf-8') as f:
        id_cache = json.load(f)
    changed = False
    removed_ids = set()
    for key in list(id_cache.keys()):
        new_files = [f for f in id_cache[key] if not f.replace('\\', '/').startswith(target_dir.replace('\\', '/'))]
        if len(new_files) != len(id_cache[key]):
            changed = True
            removed_ids.add(key)
            if new_files:
                id_cache[key] = new_files
            else:
                del id_cache[key]
    if changed:
        with open(id_cache_path, 'w', encoding='utf-8') as f:
            json.dump(id_cache, f, ensure_ascii=False, indent=4)
        print(f"已清除 {target_dir} 下的id_cache缓存")
    else:
        print(f"未发现 {target_dir} 下的缓存记录")
    return removed_ids

def clear_activity_cache_by_ids(ids, activity_cache_path=ACTIVITY_CACHE_PATH):
    """
    在activity_cache中删除指定id
    """
    if not os.path.exists(activity_cache_path):
        print(f"未找到缓存文件: {activity_cache_path}")
        return
    with open(activity_cache_path, 'r', encoding='utf-8') as f:
        activity_cache = json.load(f)
    changed = False
    for act_id in activity_cache:
        for cat_three in activity_cache[act_id]:
            for work_id in list(activity_cache[act_id][cat_three].keys()):
                if work_id in ids:
                    del activity_cache[act_id][cat_three][work_id]
                    changed = True
    if changed:
        with open(activity_cache_path, 'w', encoding='utf-8') as f:
            json.dump(activity_cache, f, ensure_ascii=False, indent=4)
        print(f"已从activity_cache中删除{len(ids)}个id")
    else:
        print("未在activity_cache中发现需删除的id")

def main():
    ids = clear_id_cache_and_get_ids(TARGET_DIR)
    if ids:
        clear_activity_cache_by_ids(ids)

if __name__ == '__main__':
    main()
