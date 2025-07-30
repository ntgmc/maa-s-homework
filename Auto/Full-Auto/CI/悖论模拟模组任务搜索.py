import re
import requests
from bs4 import BeautifulSoup
import json
import os
import math
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
print(base_path)
os.chdir(base_path)
download_mode = True
download_score_threshold = 50
job_categories = ['先锋', '近卫', '重装', '狙击', '术师', '医疗', '辅助', '特种']
ids = []
date = datetime.now().strftime('%Y-%m-%d')
# 设置缓存路径
# cache = 'Auto/Full-Auto/cache/cache.json'
cache = 'Auto/Full-Auto/cache/new_cache.json'
id_cache = 'Auto/Full-Auto/cache/id_cache.json'


def write_json_to_file(file_path, content):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(content, file, ensure_ascii=False, indent=4)


def save_data(path, data):
    with open(path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def load_data(path):
    if os.path.exists(cache):
        with open(path, 'r', encoding='utf-8') as file:
            return json.load(file)
    else:
        return {}


def build_new_cache(_cache_dict, _type, _subtype, _id, now_upload_time: str, _sub_type=None):
    _id = str(_id)
    if _type not in _cache_dict:
        _cache_dict[_type] = {}
    if _subtype not in _cache_dict[_type]:
        _cache_dict[_type][_subtype] = {}
    if _sub_type:
        if _sub_type not in _cache_dict[_type][_subtype]:
            _cache_dict[_type][_subtype][_sub_type] = {}
        _cache_dict[_type][_subtype][_sub_type][_id] = now_upload_time
    else:
        _cache_dict[_type][_subtype][_id] = now_upload_time
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


def cache_delete_save(_cache_dict, _type, found_ids, id_list, name, stage=None):
    missing_ids = set(id_list) - found_ids
    for missing_id in missing_ids:
        print(id_list, found_ids, f"未找到 {_type} {name} - {missing_id}")
        _cache_dict = build_new_cache(_cache_dict, _type, name, missing_id, "已删除", stage)
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


def compare_new_cache(new_cache_dict, _type, _subtype, _id, now_upload_time, stage=""):
    sub_dict = new_cache_dict.get(_type, {}).get(_subtype, {})
    before_upload_time = sub_dict.get(stage, sub_dict).get(str(_id), '')
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


def built_paradox_dict(data):
    _dict = {}
    for member in data:
        if member['cat_one'] == '悖论模拟':
            _key = member['cat_three']
            if _key in _dict:
                _dict[_key].append(member)
            else:
                _dict[_key] = [member]
    return _dict


def build_dict2(data, key: str):  # key为生成的字典的键
    _dict = {}
    for member in data:
        content = json.loads(member['content'])
        _key = get_stage_id_info(content[key], "cat_three")
        if _key in _dict:
            _dict[_key].append(member)
        else:
            _dict[_key] = [member]
    return _dict


def get_level_data():
    response = requests.get('https://prts.maa.plus/arknights/level')
    return add_level_data(response.json()['data']) if response.ok else []


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


def get_stage_id_info(stage_id, key):  # 通过stage_id获取信息,失败返回stage_id
    return stage_dict.get(stage_id, [{}])[0].get(key, stage_id)


def calculate_percent(item):
    like, dislike = item.get('like', 0), item.get('dislike', 0)
    return round(like / (like + dislike) * 100, 2) if like + dislike > 0 else 0


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


def code_output(percent, _id, mode):
    percent_str = f"{percent:.2f}"
    if mode == 1:  # Develop
        if percent <= 30:
            return f"***maa://{_id} ({percent_str})"
        elif percent <= 50:
            return f"**maa://{_id} ({percent_str})"
        elif percent <= 80:
            return f"*maa://{_id} ({percent_str})"
        else:
            return f"maa://{_id} ({percent_str})"
    else:  # User
        if percent <= 30:
            return f"***maa://{_id}"
        elif percent <= 50:
            return f"**maa://{_id}"
        elif percent <= 80:
            return f"*maa://{_id}"
        else:
            return f"maa://{_id}"


def less_search_paradox():
    url = "https://prts.maa.plus/copilot/query?page=1&limit=9999&levelKeyword=mem_&desc=true&orderBy=views"
    _headers = {
        "Origin": "https://zoot.plus",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
    }

    _response = requests.get(url, headers=_headers)
    if _response.status_code == 200:
        return build_dict2(_response.json()['data']['data'], 'stageName')
    else:
        raise Exception("请求失败！ERR_CONNECTION_REFUSED in less_search_paradox")


def filter_paradox(data, name, _job):
    global cache_dict, id_cache_dict
    all_data = data.get(name)
    id_list = [str(key) for key, value in cache_dict.get("悖论", {}).get(name, {}).items() if value != "已删除"]
    if all_data:
        total = len(all_data)
        ids_develop = []
        ids_user = []
        items_to_download = []
        all_below_threshold = True
        found_ids = set()
        has_high_score_90 = any(calculate_percent(item) > 90 for item in all_data)  # Check for scores > 90%
        has_high_score_80 = any(calculate_percent(item) > 80 for item in all_data)  # Check for scores > 80%

        # 计算所有作业的wilson下界得分和热度得分
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

        for idx, item in enumerate(all_data):
            percent = calculate_percent(item)
            relative_score = round((scores[idx] / max_score), 4) * 100 if max_score else 0
            relative_hot_score = round((hot_scores[idx] / max_hot_score), 4) * 100 if max_hot_score else 0
            if has_high_score_90 and percent < 70:  # Ignore scores < 70% if a high score exists
                continue
            if has_high_score_80 and percent < 50:  # Ignore scores < 50% if a high score exists
                continue
            found_ids.add(str(item['id']))
            if relative_score > 0:
                ids_develop.append(code_output(relative_score, item['id'], 1))
                if relative_score >= 20:
                    ids_user.append(code_output(relative_score, item['id'], 2))
                if relative_score >= download_score_threshold:
                    all_below_threshold = False
            if total > 1 and relative_score >= download_score_threshold or total == 1:
                items_to_download.append((relative_score, relative_hot_score, item))

        if download_mode and _job:
            # Sort items by score in descending order
            items_to_download.sort(key=lambda x: x[0], reverse=True)
            # Download the top 3 items
            for relative_score, relative_hot_score, item in items_to_download[:3]:
                file_path = f"悖论模拟/{_job}/{name} - {int(relative_score)} - {item['id']}.json"
                if compare_new_cache(cache_dict, "悖论", name, item['id'], item['upload_time']):
                    if os.path.exists(file_path):  # Skip if file exists with the same score
                        continue
                # Handle data or score changes
                if id_cache_dict.get(str(item['id'])):
                    for file in id_cache_dict[str(item['id'])]:
                        if re.search(rf"{name}", file):
                            if os.path.exists(file):
                                os.remove(file)
                                print(f"Removed {file}")
                content = get_complete_content(item['id'])
                if content is None:
                    print(f"ID={item['id']} 获取内容失败，已跳过")
                    continue
                content['doc']['details'] = f"——————————\n作业更新日期: {item['upload_time']}\n统计更新日期: {date}\n相对评分：{relative_score}%  相对热度：{relative_hot_score}%\n来源：{item['uploader']}  ID：{item['id']}\n——————————\n" + content['doc']['details']
                write_json_to_file(file_path, content)
                cache_dict = build_new_cache(cache_dict, "悖论", name, item['id'], item['upload_time'])
                id_cache_dict = build_id_cache(id_cache_dict, str(item['id']), file_path)

        cache_dict = cache_delete_save(cache_dict, "悖论", found_ids, id_list, name)
        print(f"成功搜索 {_job} - {name}")
        return name, len(ids_develop), len(ids_user), ', '.join(ids_develop), ', '.join(ids_user), all_below_threshold
    else:
        return name, 0, 0, "None", "None", False


def search_module(name, stage):
    global ids, cache_dict, id_cache_dict
    if "(" in name:
        doc = re.search(r'\((.*?)\)', name).group(1)
        name = name.split("(")[0]
    else:
        doc = "模组"
    url = f"https://prts.maa.plus/copilot/query?page=1&limit=15&levelKeyword={stage}&operator={name}&document={doc}&desc=true&orderBy=views"
    _headers = {
        "Origin": "https://zoot.plus",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
    }
    try:
        response = requests.get(url, headers=_headers)
        response.raise_for_status()  # 检查请求是否成功
        data = response.json()
        total = len(data['data']) if 'data' in data else 0
        id_list = [str(key) for key, value in cache_dict.get("模组", {}).get(name, {}).get(stage, {}).items() if value != "已删除"]
        found_ids = set()
        ids_develop = []
        ids_user = []
        items_to_download = []
        all_below_threshold = True

        # 先计算所有作业的wilson得分和热度得分
        scores = []
        hot_scores = []
        for item in data['data']['data']:
            like = item.get('like', 0)
            dislike = item.get('dislike', 0)
            view = item.get('views', 0)
            score = wilson_lower_bound(like, dislike)
            hot_score = round(score * math.log10(view + 1), 2)
            scores.append(score)
            hot_scores.append(hot_score)
        max_score = max(scores) if scores and max(scores) > 0 else 1
        max_hot_score = max(hot_scores) if hot_scores and max(hot_scores) > 0 else 1
        for idx, item in enumerate(data['data']['data']):
            relative_score = round((scores[idx] / max_score), 4) * 100 if max_score else 0
            relative_hot_score = round((hot_scores[idx] / max_hot_score), 4) * 100 if max_hot_score else 0
            found_ids.add(str(item['id']))
            if relative_score > 0:
                ids_develop.append(code_output(relative_score, item['id'], 1))
                if relative_score >= 50:
                    ids_user.append(code_output(relative_score, item['id'], 2))
                if relative_score >= download_score_threshold:
                    all_below_threshold = False
            elif item['uploader'] == '作业代传——有问题联系原作者':
                ids.append(int(item['id']))
            if total > 1 and relative_score >= download_score_threshold or total == 1:
                items_to_download.append((relative_score, relative_hot_score, item))
        if download_mode and job:
            # 对列表按照评分进行排序，评分最高的在前面
            items_to_download.sort(key=lambda x: x[0], reverse=True)

            # 只下载评分最高的三个项目
            for relative_score, relative_hot_score, item in items_to_download[:3]:
                file_path = f"模组任务/{name} - {stage} - {int(relative_score)} - {item['id']}.json"
                if compare_new_cache(cache_dict, "模组", name, item['id'], item['upload_time'], stage):
                    if os.path.exists(file_path):
                        continue
                if id_cache_dict.get(str(item['id'])):
                    for file in id_cache_dict[str(item['id'])]:
                        if re.search(rf"{name} - {stage}", file):
                            if os.path.exists(file):
                                os.remove(file)
                                print(f"Removed {file}")
                content = get_complete_content(item['id'])
                content['doc'][
                    'details'] = f"——————————\n作业更新日期: {item['upload_time']}\n统计更新日期: {date}\n相对评分：{relative_score}%  相对热度：{relative_hot_score}%\n来源：{item['uploader']}  ID：{item['id']}\n——————————\n" + \
                                 content['doc']['details']
                write_json_to_file(file_path, content)
                cache_dict = build_new_cache(cache_dict, "模组", name, item['id'], item['upload_time'], stage)
                id_cache_dict = build_id_cache(id_cache_dict, item['id'], file_path)
        cache_dict = cache_delete_save(cache_dict, "模组", found_ids, id_list, name, stage=stage)
        print(f"成功搜索 {name} - {stage}")
        return name, stage, len(ids_develop), len(ids_user), ', '.join(ids_develop) if ids_develop else 'None', ', '.join(ids_user) if ids_user else 'None', all_below_threshold
    except requests.exceptions.RequestException as e:
        print(f"请求失败！{e}")
        return name, stage, 0, 0, "None", "None", False


def extract_tr_contents(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    tr_contents = []

    for tr in soup.find_all('tr'):
        td_contents = [td.get_text().strip() for td in tr.find_all('td')]
        if len(td_contents) == 3:  # 确保td_contents包含两个元素，即干员名和关卡
            tr_contents.append((td_contents[0], td_contents[1], td_contents[2]))
        else:
            print(f"Warning: {td_contents}")

    return tr_contents


def get_operators():
    url = "https://prts.wiki/w/%E5%B9%B2%E5%91%98%E4%B8%80%E8%A7%88"
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0',
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    divs = soup.find_all('div')
    table_data = []
    for div in divs:
        row_data = []
        for attr in div.attrs.values():
            if isinstance(attr, str):
                row_data.append(attr)
            elif isinstance(attr, list):
                row_data.append(','.join(attr))
            else:
                row_data.append('')
        table_data.append(row_data)
    operators = {}
    for row in table_data:
        if len(row) > 30:
            name = row[0].strip()
            profession = row[1].strip()
            sort_id = int(row[30].strip())  # Assuming data_sort_id is the third element
            if profession not in operators:
                operators[profession] = []
            operators[profession].append((name, sort_id))
    sorted_operators = {k: sorted(operators[k], key=lambda x: x[1]) for k in job_categories if k in operators}
    text = ''
    for profession, names in sorted_operators.items():
        text += f"{profession}\n" + '\n'.join([name for name, _ in names]) + "\n\n"
    with open(f"Auto/Full-Auto/CI/keywords.txt", "w", encoding='utf-8') as f:
        f.write(text)


def main_paradox():
    # 读取关键字文件
    keywords_file = 'Auto/Full-Auto/CI/keywords.txt'
    output_file_develop = 'Auto/Full-Auto/CI/paradox_develop.txt'
    output_file_user = 'Auto/Full-Auto/CI/paradox_user.txt'
    results = []
    job_now = -1
    paradox_all_dict = less_search_paradox()
    with open(keywords_file, 'r', encoding='utf-8') as f:
        with ThreadPoolExecutor() as executor:
            futures = []
            for index, line in enumerate(f):
                # 如果是空行，提交一个表示空行的任务
                if not line.strip():
                    futures.append((index, executor.submit(lambda: ('empty_line',))))
                    continue
                keyword = line.strip()
                if job_now + 1 < len(job_categories) and keyword == job_categories[job_now + 1]:
                    job_now += 1
                    continue
                stage_id = paradox_dict.get(keyword, [{}])[0].get('stage_id')
                if stage_id:
                    future = executor.submit(filter_paradox, paradox_all_dict, keyword, job_categories[job_now])
                    futures.append((index, future))
                else:
                    def create_no_paradox_task(_keyword):
                        return lambda: ('no-paradox', _keyword)

                    no_paradox_task = create_no_paradox_task(keyword)
                    futures.append((index, executor.submit(no_paradox_task)))
            for index, future in futures:
                result = future.result()
                # 将结果和序号一起存储
                results.append((index, result))
    # 根据序号对结果进行排序
    results.sort(key=lambda x: x[0])
    # 提取排序后的结果
    output_lines_develop = []
    output_lines_user = []
    for index, result in results:
        # 如果结果是表示空行的标记，添加一个空行到输出列表
        if result[0] == 'empty_line':
            output_lines_develop.append('\n')
            output_lines_user.append('\n')
        elif result[0] == 'no-paradox':
            result_keyword = result[1]
            output_lines_develop.append(f"{result_keyword}\t-\t-\n")
            output_lines_user.append(f"{result_keyword}\t-\t-\n")
        else:
            result_keyword, id_count_develop, id_count_user, str_ids_develop, str_ids_user, all_below_threshold = result
            output_lines_develop.append(f"{result_keyword}\t{id_count_develop}\t{str_ids_develop}\t{all_below_threshold}\n")
            output_lines_user.append(f"{result_keyword}\t{id_count_user}\t{str_ids_user}\n")
    with open(output_file_develop, 'w', encoding='utf-8') as output_develop, open(output_file_user, 'w',
                                                                                  encoding='utf-8') as output_user:
        output_develop.writelines(output_lines_develop)
        output_user.writelines(output_lines_user)
    print("输出Paradox完成！")


def main_module():
    output_file_develop = 'Auto/Full-Auto/CI/module_develop.txt'
    output_file_user = 'Auto/Full-Auto/CI/module_user.txt'
    results = []
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0',
    }
    response = requests.get(
        "https://prts.wiki/w/%E5%B9%B2%E5%91%98%E6%A8%A1%E7%BB%84%E4%B8%80%E8%A7%88/%E6%A8%A1%E7%BB%84%E4%BB%BB%E5%8A%A1",
        headers=headers)
    # 提取HTML中的角色名
    tr_contents = extract_tr_contents(response.text)
    with ThreadPoolExecutor() as executor:
        futures = []
        for index, (name, stage, task) in enumerate(tr_contents):
            if stage != "[[]]":
                future = executor.submit(search_module, name, stage)
                futures.append((index, future))
        for index, future in futures:
            result = future.result()
            # 将结果和序号一起存储
            results.append((index, result))
    # 根据序号对结果进行排序
    results.sort(key=lambda x: x[0])
    # 提取排序后的结果
    output_lines_develop = []
    output_lines_user = []
    for index, result in results:
        result_name, result_stage, id_count_develop, id_count_user, str_ids_develop, str_ids_user, all_below_threshold = result
        output_lines_develop.append(f"{result_name}\t{result_stage}\t{id_count_develop}\t{str_ids_develop}\t{all_below_threshold}\n")
        output_lines_user.append(f"{result_name}\t{result_stage}\t{id_count_user}\t{str_ids_user}\n")
    with open(output_file_develop, 'w', encoding='utf-8') as output_develop, open(output_file_user, 'w',
                                                                                  encoding='utf-8') as output_user:
        output_develop.writelines(output_lines_develop)
        output_user.writelines(output_lines_user)
    print("输出Module完成！")


level_data = get_level_data()
stage_dict = build_dict(level_data, 'stage_id')
paradox_dict = built_paradox_dict(level_data)
# cat_three_dict = build_dict(level_data, 'cat_three')
if download_mode:
    for job in job_categories:
        os.makedirs(f'悖论模拟/{job}', exist_ok=True)
    os.makedirs(f'模组任务', exist_ok=True)
os.makedirs('Auto/Full-Auto/cache', exist_ok=True)
cache_dict = load_data(cache)
id_cache_dict = load_data(id_cache)
now = datetime.now().timestamp()
get_operators()
main_paradox()
main_module()
last = datetime.now().timestamp()
save_data(cache, cache_dict)
save_data(id_cache, id_cache_dict)
print(f"搜索完毕，共耗时 {round(last - now, 2)} s.\n")
print(ids)
