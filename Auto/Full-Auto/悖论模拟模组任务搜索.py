import requests
from bs4 import BeautifulSoup
import json
import os
import glob
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
download_mode = True
download_score_threshold = 50
job_categories = ['先锋', '近卫', '重装', '狙击', '术士', '医疗', '辅助', '特种']
ids = []
date = datetime.now().strftime('%Y-%m-%d')
# 设置缓存路径
cache = 'Auto/Full-auto/cache/cache.json'


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


def get_level_data():
    response = requests.get('https://prts.maa.plus/arknights/level')
    return response.json()['data'] if response.ok else []


def calculate_percent(item):
    like, dislike = item.get('like', 0), item.get('dislike', 0)
    return round(like / (like + dislike) * 100, 2) if like + dislike > 0 else 0


def code_output(percent, _id, mode):
    if mode == 1:  # Develop
        if percent <= 30:
            return f"***maa://{_id} ({percent})"
        elif percent <= 50:
            return f"**maa://{_id} ({percent})"
        elif percent <= 80:
            return f"*maa://{_id} ({percent})"
        else:
            return f"maa://{_id} ({percent})"
    else:  # User
        if percent <= 30:
            return f"***maa://{_id}"
        elif percent <= 50:
            return f"**maa://{_id}"
        elif percent <= 80:
            return f"*maa://{_id}"
        else:
            return f"maa://{_id}"


def check_file_exists(pattern):  # 判断是否存在相同id但评分不同的文件
    matching_files = glob.glob(pattern)
    if len(matching_files) > 0:
        for file_name in matching_files:
            os.remove(file_name)
            print(f"Removed {file_name}")


def search_paradox(name, stage_id, _job=None):
    global cache_dict
    url = f"https://prts.maa.plus/copilot/query?page=1&limit=15&levelKeyword={stage_id}&document=&desc=true&orderBy=views"
    _headers = {
        "Origin": "https://prts.plus",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
    }

    _response = requests.get(url, headers=_headers)
    if _response.status_code == 200:
        data = _response.json()
        total = data['data'].get('total', 0)
        if total > 0:
            ids_develop = []
            ids_user = []
            items_to_download = []
            for item in data['data']['data']:
                percent = calculate_percent(item)
                if percent > 0:
                    ids_develop.append(code_output(percent, item['id'], 1))
                    if percent >= 20:
                        ids_user.append(code_output(percent, item['id'], 2))
                if total > 1 and percent >= download_score_threshold or total == 1:
                    items_to_download.append((percent, item))
            if download_mode and _job:
                # 对列表按照评分进行排序，评分最高的在前面
                items_to_download.sort(key=lambda x: x[0], reverse=True)

                # 只下载评分最高的三个项目
                for percent, item in items_to_download[:3]:
                    if compare_cache(cache_dict, item['id'], item['upload_time'], name + "-悖论"):
                        print(f"{item['id']} 未改变数据，无需更新")
                        continue
                    file_path = f"悖论模拟/{_job}/{name} - {int(percent)} - {item['id']}.json"
                    if not os.path.exists(file_path):
                        check_file_exists(f"悖论模拟/{_job}/{name} - * - {item['id']}.json")
                    content = json.loads(item['content'])
                    content['doc'][
                        'details'] = f"统计日期：{date}\n好评率：{percent}%  浏览量：{item['views']}\n来源：{item['uploader']}  ID：{item['id']}\n" + \
                                     content['doc']['details']
                    write_to_file(file_path, content)
                    cache_dict = build_cache(cache_dict, item['id'], item['upload_time'], name + "-悖论")
            print(f"成功搜索 {_job} - {name}")
            return name, len(ids_develop), len(ids_user), ', '.join(ids_develop), ', '.join(ids_user)
        else:
            return name, 0, 0, "None", "None"
    else:
        print(f"请求失败！ERR_CONNECTION_REFUSED in search({name})")
        return name, 0, 0, "None", "None"


def search_module(name, stage):
    global ids, cache_dict
    url = f"https://prts.maa.plus/copilot/query?page=1&limit=15&levelKeyword={stage}&document={name}&desc=true&orderBy=views"
    _headers = {
        "Origin": "https://prts.plus",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
    }
    _response = requests.get(url, headers=_headers)
    if _response.status_code == 200:
        data = _response.json()
        total = data['data'].get('total', 0)
        if total > 0:
            ids_develop = []
            ids_user = []
            items_to_download = []
            for item in data['data']['data']:
                percent = calculate_percent(item)
                if percent > 0:
                    ids_develop.append(code_output(percent, item['id'], 1))
                    if percent >= 50:
                        ids_user.append(code_output(percent, item['id'], 2))
                elif item['uploader'] == '作业代传——有问题联系原作者':
                    ids.append(int(item['id']))
                if total > 1 and percent >= download_score_threshold or total == 1:
                    items_to_download.append((percent, item))
            if download_mode and job:
                # 对列表按照评分进行排序，评分最高的在前面
                items_to_download.sort(key=lambda x: x[0], reverse=True)

                # 只下载评分最高的三个项目
                for percent, item in items_to_download[:3]:
                    if compare_cache(cache_dict, item['id'], item['upload_time'], name + "-模组"):
                        print(f"{item['id']} 未改变数据，无需更新")
                        continue
                    file_path = f"模组任务/{name} - {stage} - {int(percent)} - {item['id']}.json"
                    if not os.path.exists(file_path):
                        check_file_exists(f"模组任务/{name} - {stage} - * - {item['id']}.json")
                    content = json.loads(item['content'])
                    content['doc'][
                        'details'] = f"统计日期：{date}\n好评率：{percent}%  浏览量：{item['views']}\n来源：{item['uploader']}  ID：{item['id']}\n" + \
                                     content['doc']['details']
                    write_to_file(file_path, content)
                    cache_dict = build_cache(cache_dict, item['id'], item['upload_time'], name + "-模组")
            print(f"成功搜索 {name} - {stage}")
            return name, stage, len(ids_develop), len(ids_user), ', '.join(ids_develop), ', '.join(ids_user)
        else:
            return name, stage, 0, 0, "None", "None"
    else:
        print(f"请求失败！ERR_CONNECTION_REFUSED in search({name} - {stage})")
        return name, stage, 0, 0, "None", "None"


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


def main_paradox():
    # 读取关键字文件
    keywords_file = 'Auto/Full-Auto/keywords.txt'
    output_file_develop = 'Auto/Full-Auto/paradox_develop.txt'
    output_file_user = 'Auto/Full-Auto/paradox_user.txt'
    results = []
    job_now = -1
    paradox_dict = built_paradox_dict(get_level_data())
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
                    future = executor.submit(search_paradox, keyword, stage_id, job_categories[job_now])
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
            result_keyword, id_count_develop, id_count_user, str_ids_develop, str_ids_user = result
            output_lines_develop.append(f"{result_keyword}\t{id_count_develop}\t{str_ids_develop}\n")
            output_lines_user.append(f"{result_keyword}\t{id_count_user}\t{str_ids_user}\n")
    with open(output_file_develop, 'w', encoding='utf-8') as output_develop, open(output_file_user, 'w',
                                                                                  encoding='utf-8') as output_user:
        output_develop.writelines(output_lines_develop)
        output_user.writelines(output_lines_user)
    print("输出Paradox完成！")


def main_module():
    output_file_develop = 'Auto/Full-Auto/module_develop.txt'
    output_file_user = 'Auto/Full-Auto/module_user.txt'
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
        result_name, result_stage, id_count_develop, id_count_user, str_ids_develop, str_ids_user = result
        output_lines_develop.append(f"{result_name}\t{result_stage}\t{id_count_develop}\t{str_ids_develop}\n")
        output_lines_user.append(f"{result_name}\t{result_stage}\t{id_count_user}\t{str_ids_user}\n")
    with open(output_file_develop, 'w', encoding='utf-8') as output_develop, open(output_file_user, 'w',
                                                                                  encoding='utf-8') as output_user:
        output_develop.writelines(output_lines_develop)
        output_user.writelines(output_lines_user)
    print("输出Module完成！")


if download_mode:
    for job in job_categories:
        os.makedirs(f'悖论模拟/{job}', exist_ok=True)
    os.makedirs(f'模组任务', exist_ok=True)
os.makedirs('Auto/Full-auto/cache', exist_ok=True)
if os.path.exists(cache):
    cache_dict = load_data()
else:
    cache_dict = {}
# search("缪尔赛思", '先锋')
main_paradox()
main_module()
save_data(cache_dict)
print(ids)
