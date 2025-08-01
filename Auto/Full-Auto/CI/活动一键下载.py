import requests
import json
import re
import os
from datetime import datetime
from bs4 import BeautifulSoup
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
# cache = 'Auto/Full-Auto/cache/activity_cache.json'
cache = 'Auto/Full-Auto/cache/new_activity_cache.json'
id_cache = 'Auto/Full-Auto/cache/id_cache.json'


def write_to_file(file_path, content):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(content, file, ensure_ascii=False, indent=4)


def load_data(path):
    if os.path.exists(cache):
        with open(path, 'r', encoding='utf-8') as file:
            return json.load(file)
    else:
        return {}


def build_activity_new_cache(_cache_dict, cat_three, _id: str, now_upload_time: str):
    activity_id = get_cat_three_info(cat_three_all_dict, cat_three, "stage_id").split('_')[0]
    _id = str(_id)
    if activity_id not in _cache_dict:
        _cache_dict[activity_id] = {}
    if cat_three not in _cache_dict[activity_id]:
        _cache_dict[activity_id][cat_three] = {}
    _cache_dict[activity_id][cat_three][_id] = now_upload_time
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


def compare_activity_new_cache(new_cache_dict, cat_three, _id, now_upload_time):
    activity_id = get_cat_three_info(cat_three_all_dict, cat_three, "stage_id").split('_')[0]
    before_upload_time = new_cache_dict.get(activity_id, {}).get(cat_three, {}).get(str(_id), '')
    return before_upload_time == now_upload_time


def get_activity_data():
    """
    访问 https://prts.wiki/w/%E6%B4%BB%E5%8A%A8%E4%B8%80%E8%A7%88 获取活动数据，格式为{'name': 活动名, 'status': 状态}
    :return: 活动数据, 进行中的活动
    """
    response = requests.get('https://prts.wiki/w/%E6%B4%BB%E5%8A%A8%E4%B8%80%E8%A7%88')
    soup = BeautifulSoup(response.text, 'html.parser')
    activities = {}
    ongoing_activities = []

    # Find the table containing the activity data
    table = soup.find('table', {'class': 'wikitable mw-collapsible mw-collapsible-title-center'})
    if not table:
        return False, False

    # Iterate through the rows of the table
    rows = table.find_all('tr')
    for row in rows[1:]:  # Skip the header row
        cols = row.find_all('td')
        if len(cols) < 3:
            continue

        activity_page = cols[1].find('a')
        category = cols[2].text.strip()
        status_span = cols[1].find('span', {'class': 'TLDcontainer'})
        if ("支线故事" in category or "故事集" in category or "引航者试炼" in category) and activity_page:
            activity_name = activity_page.text.strip()
            activity_id = ""
            status = "已结束"
            if status_span and "进行中" in status_span.text:
                status = "进行中"
                ongoing_activities.append(activity_name)
                response1 = requests.get("https://prts.wiki" + activity_page.get('href'))
                soup = BeautifulSoup(response1.text, 'html.parser')

                # Find all tables that match the criteria
                tables = soup.find_all('table', {'class': 'wikitable'})
                # Iterate through each table
                task_cat_three = ''
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows[1:]:  # Skip the header row
                        cols = row.find_all('td')
                        if len(cols) < 3:
                            continue
                        task_page = cols[0].find('a')
                        if task_page:
                            task_cat_three = task_page.get('title', '')
                            if "ST" in task_cat_three:
                                continue
                            if "-1" in task_cat_three:
                                task_stage_id = get_cat_three_info(cat_three_all_dict, task_cat_three, "stage_id")
                                activity_id = extract_activity_from_stage_id(task_stage_id)
                                break
                    if "-1" in task_cat_three:
                        break
            elif status_span and "未开始" in status_span.text:
                status = "未开始"
            activities[activity_name] = {'status': status, 'id': activity_id}
    return activities, ongoing_activities


def makedir(activity_name: str):
    os.makedirs(f'【当前活动】{activity_name.replace("·复刻", "")}', exist_ok=True)


def build_dict(data, key: str, _dict=None):
    """
    构建字典，将数据按关键分类
    :param data: 要分类的数据
    :param key: 生成的字典的键
    :param _dict: 字典，如果传入则在此基础上添加
    :return: 生成的字典，格式为{key: [成员1, 成员2, ...]}
    """
    if _dict is None:
        _dict = {}
    for member in data:
        _key = member[key]
        if _key in _dict:
            _dict[_key].append(member)
        else:
            _dict[_key] = [member]
    return _dict


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


def get_stage_id_info(stage_dict, stage_id, key):  # 通过stage_id获取信息,失败返回stage_id
    return stage_dict.get(stage_id, [{}])[0].get(key, stage_id)


def get_cat_three_info(cat_three_dict, cat_three, key):  # 通过cat_three获取信息,失败返回cat_three
    return cat_three_dict.get(cat_three, [{}])[0].get(key, cat_three)


def build_dict2(cat_three_dict, data, key: str):  # key为生成的字典的键
    _dict = {}
    for member in data:
        content = json.loads(member['content'])
        _key = get_cat_three_info(cat_three_dict, content[key], "stage_id")
        if _key in _dict:
            _dict[_key].append(member)
        else:
            _dict[_key] = [member]
    return _dict


def replace_dir_char(text):
    for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
        text = text.replace(char, '')
    return text


def generate_filename(stage_dict, stage_id, data, uploader, activity_name, stage_name=None):
    if not stage_name:
        stage_name = get_stage_id_info(stage_dict, stage_id, "cat_three")
    opers = data.get('opers') if data.get('opers') is not None else []
    groups = data.get('groups') if data.get('groups') is not None else []
    names_parts = ['+'.join(oper.get('name', '') for oper in opers),
                   '+'.join(group.get('name', '') for group in groups)]
    names = '+'.join(part for part in names_parts if part)  # 只连接非空的部分
    names = replace_dir_char(names)
    if data.get("difficulty", 0) == 1:
        stage_name = "(仅普通)" + stage_name
    elif data.get("difficulty", 0) == 2:
        stage_name = "(仅突袭)" + stage_name
    if uploader in ["一只摆烂的42", "萨拉托加"]:
        stage_name = f"({uploader})" + stage_name
    if len(names) > 50:
        names = "文件名过长不予显示"
    file_path = os.path.join(f'【当前活动】{activity_name}', f'{stage_name}_{names}.json')
    return file_path


def cache_delete_save(_cache_dict, found_ids, id_list, cat_three):
    global id_cache_dict
    missing_ids = set(id_list) - found_ids
    for missing_id in missing_ids:
        print(id_list, found_ids, f"未找到 {cat_three} - {missing_id}")
        _cache_dict = build_activity_new_cache(cache_dict, cat_three, missing_id, "已删除")
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


def less_filter_data(stage_dict, data, stage_id):
    global no_result, cache_dict, id_cache_dict
    if "#f#" in stage_id:
        return
    all_data = data.get(stage_id)
    activity_name = now_activities[0].replace("·复刻", "")
    cat_three = get_stage_id_info(stage_dict, stage_id, "cat_three")
    activity_id = get_cat_three_info(cat_three_all_dict, cat_three, "stage_id").split('_')[0]
    id_list = [str(key) for key, value in cache_dict.get(activity_id, {}).get(cat_three, {}).items() if value != "已删除"]
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
        if not scores or max(scores) == 0:
            max_score = 1
        else:
            max_score = max(scores)
        if not hot_scores or max(hot_scores) == 0:
            max_hot_score = 1
        else:
            max_hot_score = max(hot_scores)
        # 重新遍历，计算相对分数和相对热度分数
        score_threshold = download_score_threshold
        view_threshold = download_view_threshold
        for idx, item in enumerate(all_data):
            view = item.get('views', 0)
            found_ids.add(str(item['id']))
            relative_score = round((scores[idx] / max_score), 4) * 100 if max_score else 0
            relative_hot_score = round((hot_scores[idx] / max_hot_score), 4) * 100 if max_hot_score else 0
            # 用字符串格式化，保证只保留两位小数
            relative_score_str = f"{relative_score:.2f}"
            relative_hot_score_str = f"{relative_hot_score:.2f}"
            if relative_score >= score_threshold and view >= view_threshold:
                if compare_activity_new_cache(cache_dict, cat_three, item['id'], item['upload_time']):
                    download_amount += 1
                    continue
                if id_cache_dict.get(str(item['id'])):
                    for file in id_cache_dict[str(item['id'])]:
                        if os.path.exists(file):
                            os.remove(file)
                            print(f"Removed {file}")
                content = get_complete_content(item['id'])
                file_path = generate_filename(stage_dict, stage_id, content, item['uploader'], activity_name, cat_three)
                content['doc']['details'] = f"——————————\n作业更新日期: {item['upload_time']}\n统计更新日期: {date}\n相对评分：{relative_score_str}%  相对热度：{relative_hot_score_str}%\n来源：{item['uploader']}  ID：{item['id']}\n——————————\n" + content['doc']['details']
                print(f"{file_path} {relative_score_str}% {view} 成功下载")
                write_to_file(file_path, content)
                cache_dict = build_activity_new_cache(cache_dict, cat_three, item['id'], item['upload_time'])
                id_cache_dict = build_id_cache(id_cache_dict, item['id'], file_path)
                download_amount += 1
    else:
        # no_result.append(keyword)
        print(f"{stage_id} 无数据")
    cache_dict = cache_delete_save(cache_dict, found_ids, id_list, cat_three)


def less_search(cat_three_dict, keyword):
    url = f"https://prts.maa.plus/copilot/query?page=1&limit=999&levelKeyword={keyword}&desc=true&orderBy=views"
    _headers = {
        "Origin": "https://zoot.plus",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
    }
    _response = requests.get(url, headers=_headers)
    if _response.ok:
        return build_dict2(cat_three_dict, _response.json()['data']['data'], "stageName")
    else:
        print(f"请求 {keyword} 失败")


def extract_activity_from_stage_id(stage_id: str):
    """
    从 stage_id 中提取activity_id，如act34side
    :param stage_id: 关卡ID
    :return: {activity_id}_
    """
    match = re.search(r'(.+?)_', stage_id)
    if match:
        return match.group(1) + '_'
    return None


def download_current_activity(activity):
    """
    下载当前活动
    :param activity: 活动名
    :return: 无返回值
    """
    stage_dict = {}
    cat_three_dict = {}
    activity_id = activity_data[activity]['id']
    print(activity_data, activity_id)
    if activity in all_dict["活动关卡"]:
        stage_dict = build_dict(all_dict["活动关卡"][activity], "stage_id")
        cat_three_dict = build_dict(all_dict["活动关卡"][activity], "cat_three")
    elif activity.replace("·复刻", "") in all_dict["活动关卡"]:
        activity = activity.replace("·复刻", "")
        stage_dict = build_dict(all_dict["活动关卡"][activity], "stage_id")
        cat_three_dict = build_dict(all_dict["活动关卡"][activity], "cat_three")
    stage_dict = build_activity_dict(all_dict["活动关卡"][""], activity_id, _dict=stage_dict)
    cat_three_dict = build_activity_dict(all_dict["活动关卡"][""], activity_id, _dict=cat_three_dict, key="cat_three")
    # write_to_file('Auto/Full-Auto/log/stage_dict_temp.json', stage_dict)
    # write_to_file('Auto/Full-Auto/log/cat_three_dict_temp.json', cat_three_dict)
    less_dict = less_search(cat_three_dict, activity_id)
    for stage_id in less_dict:
        less_filter_data(stage_dict, less_dict, stage_id)


def get_level_data():
    """
    访问 https://prts.maa.plus/arknights/level 获取关卡数据
    :return: 关卡数据
    """
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


def build_activity_dict(data, act_id, _dict=None, key="stage_id"):
    """
    构建活动字典，将数据按活动分类
    :param data: 要分类的数据
    :param act_id: 活动ID，如act34side
    :param _dict: 字典，如果传入则在此基础上添加
    :param key: 生成的字典的键
    :return: 活动字典，格式为{活动名: [成员1, 成员2, ...]}
    """
    if _dict is None:
        _dict = {}
    for member in data:
        _key = member[key]
        _stage_id = member["stage_id"]
        if act_id in _stage_id:
            if _key in _dict:
                _dict[_key].append(member)
            else:
                _dict[_key] = [member]
    return _dict


def build_complex_dict(data):
    """
    构建复杂字典，将数据按分类和子分类分类
    :param data: 要分类的数据
    :return: 复杂字典，格式为{主分类: {子分类: [成员1, 成员2, ...]}}
    """
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


# 获取关卡数据，构建字典
level_data = get_level_data()
all_dict = build_complex_dict(level_data)
cat_three_all_dict = build_dict(level_data, "cat_three")
activity_data, now_activities = get_activity_data()
# 手动添加活动数据
# activity_data["引航者试炼 #05"] = {"status": "进行中", "id": "act5bossrush_"}

if not activity_data:
    print("Fail to get activity data.")
    exit(0)
if not now_activities:
    print("No ongoing activities.")
    exit(0)
makedir(now_activities[0])
# write_to_file('Auto/Full-Auto/log/activity_dict_temp.json', all_dict)
# 读取缓存
cache_dict = load_data(cache)
id_cache_dict = load_data(id_cache)
now = datetime.now().timestamp()
download_current_activity(now_activities[0])
last = datetime.now().timestamp()
# 保存缓存
write_to_file(cache, cache_dict)
write_to_file(id_cache, id_cache_dict)
print(f"搜索完毕，共耗时 {round(last - now, 2)} s.\n")
print('No_result: ', no_result)
