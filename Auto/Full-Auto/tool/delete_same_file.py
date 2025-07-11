import os
import re
import json
from datetime import datetime

base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
print(base_path)
os.chdir(base_path)
folder = r'模组任务'  # 替换为实际路径
pattern = re.compile(r'.* - (\d+)\.json$')

# 收集同id的文件
id_files = {}
for filename in os.listdir(folder):
    match = pattern.match(filename)
    if match:
        file_id = match.group(1)
        id_files.setdefault(file_id, []).append(filename)

for file_id, files in id_files.items():
    if len(files) <= 1:
        continue
    date_file_map = {}
    for fname in files:
        with open(os.path.join(folder, fname), 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                details = data['doc']['details']
                date_match = re.search(r'统计更新日期: (\d{4}-\d{2}-\d{2})', details)
                if date_match:
                    date_str = date_match.group(1)
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    date_file_map[fname] = date_obj
            except Exception as e:
                print(f'文件{fname}解析失败: {e}')
    if not date_file_map:
        continue
    # 找到最新日期的文件
    latest_file = max(date_file_map, key=date_file_map.get)
    # 删除其他文件
    for fname in files:
        if fname != latest_file:
            os.remove(os.path.join(folder, fname))
            print(f'已删除旧文件: {fname}')