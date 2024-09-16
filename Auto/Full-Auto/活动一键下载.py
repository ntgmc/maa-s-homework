import requests
import json
import re
import os
from datetime import datetime
from bs4 import BeautifulSoup

print(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# 设置阈值(好评率和浏览量)(不满足条件则降低阈值，但最低不低于50% 0)
download_score_threshold = 80  # 好评率阈值
download_view_threshold = 1000  # 浏览量阈值
# 设置空列表
no_result = []
# 设置日期
date = datetime.now().strftime('%Y-%m-%d')
# 设置缓存路径
cache = 'Auto/Full-Auto/cache/activity_cache.json'


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


def compare_cache(_cache_dict, _id, now_upload_time: str, others: str):  # 最新返回True，需更新返回False
    before_upload_time = _cache_dict.get(f"{_id}-{others}", '')
    if before_upload_time == now_upload_time:
        return True
    else:
        return False


def get_activity_data():
    """
    访问 https://prts.wiki/w/%E6%B4%BB%E5%8A%A8%E4%B8%80%E8%A7%88 获取活动数据，格式为{'name': 活动名, 'status': 状态}
    :return: 活动数据, 进行中的活动
    """
    response = requests.get('https://prts.wiki/w/%E6%B4%BB%E5%8A%A8%E4%B8%80%E8%A7%88')
    soup = BeautifulSoup(response.text, 'html.parser')
    activities = []
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
        if "支线故事" in category and activity_page:
            activity_name = activity_page.text.strip()
            status = "已结束"
            if status_span and "进行中" in status_span.text:
                status = "进行中"
                ongoing_activities.append(activity_name)
            elif status_span and "未开始" in status_span.text:
                status = "未开始"
            activities.append({'name': activity_name, 'status': status})
    return activities, ongoing_activities


def makedir(activity_name):
    os.makedirs(f'【当前活动】{activity_name}', exist_ok=True)


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


def calculate_percent(item) -> float:
    """
    计算好评率，保留两位小数
    :param item: 作业数据
    :return: 好评率，保留两位小数
    """
    like, dislike = item.get('like', 0), item.get('dislike', 0)
    return round(like / (like + dislike) * 100, 2) if like + dislike > 0 else 0.00


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


def generate_filename(stage_dict, stage_id, data, uploader, stage_name=None):
    if not stage_name:
        stage_name = get_stage_id_info(stage_dict, stage_id, "cat_three")
    opers = data.get('opers', [])
    groups = data.get('groups', [])
    names_parts = ['+'.join(oper.get('name', '') for oper in opers),
                   '+'.join(group.get('name', '') for group in groups)]
    names = '+'.join(part for part in names_parts if part)  # 只连接非空的部分
    names = replace_dir_char(names)
    if uploader in ["一只摆烂的42", "萨拉托加"]:
        stage_name = f"({uploader})" + stage_name
    if data.get("difficulty", 0) == 1:
        stage_name = "(仅普通)" + stage_name
    elif data.get("difficulty", 0) == 2:
        stage_name = "(仅突袭)" + stage_name
    if len(names) > 100:
        names = "文件名过长不予显示"
    file_path = os.path.join(f'【当前活动】{now_activities[0]}', f'{stage_name}_{names}.json')
    return file_path


def less_filter_data(stage_dict, data, stage_id):
    global no_result, cache_dict
    all_data = data.get(stage_id)
    if all_data:
        download_amount = 0
        cat_three = get_stage_id_info(stage_dict, stage_id, "cat_three")
        score_threshold = download_score_threshold
        view_threshold = download_view_threshold
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
                    file_path = generate_filename(stage_dict, stage_id, content, item['uploader'], cat_three)
                    content['doc']['details'] = f"作业更新日期: {item['upload_time']}\n统计更新日期: {date}\n好评率：{percent}%  浏览量：{view}\n来源：{item['uploader']}  ID：{item['id']}\n" + content['doc']['details']
                    print(f"{file_path} {percent}% {view} 成功下载")
                    if os.path.exists(file_path):
                        os.remove(file_path)
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


def less_search(cat_three_dict, keyword):
    url = f"https://prts.maa.plus/copilot/query?page=1&limit=999&levelKeyword={keyword}&desc=true&orderBy=views"
    _headers = {
        "Origin": "https://prts.plus",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
    }
    _response = requests.get(url, headers=_headers)
    if _response.ok:
        return build_dict2(cat_three_dict, _response.json()['data']['data'], "stage_name")
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
    try:
        stage_dict = build_dict(all_dict["活动关卡"][activity], "stage_id")
        cat_three_dict = build_dict(all_dict["活动关卡"][activity], "cat_three")
    except KeyError:
        activity = activity.replace("·复刻", "")
        stage_dict = build_dict(all_dict["活动关卡"][activity], "stage_id")
        cat_three_dict = build_dict(all_dict["活动关卡"][activity], "cat_three")
    activity_id = extract_activity_from_stage_id(all_dict["活动关卡"][activity][0]['stage_id'])
    stage_dict = build_activity_dict(all_dict["活动关卡"][""], activity_id, _dict=stage_dict)
    cat_three_dict = build_activity_dict(all_dict["活动关卡"][""], activity_id, _dict=cat_three_dict, key="cat_three")
    # write_to_file('Auto/Full-Auto/log/stage_dict_temp.json', stage_dict)
    # write_to_file('Auto/Full-Auto/log/cat_three_dict_temp.json', cat_three_dict)
    less_dict = less_search(cat_three_dict, activity_id)
    for key2 in less_dict:
        less_filter_data(stage_dict, less_dict, key2)


def get_level_data():
    """
    访问 https://prts.maa.plus/arknights/level 获取关卡数据
    :return: 关卡数据
    """
    response = requests.get('https://prts.maa.plus/arknights/level')
    return response.json()['data'] if response.ok else []


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


activity_data, now_activities = get_activity_data()
if not activity_data:
    print("Fail to get activity data.")
    exit(0)
if not now_activities:
    print("No ongoing activities.")
    exit(0)
makedir(now_activities[0])
# 获取关卡数据，构建字典
level_data = get_level_data()
all_dict = build_complex_dict(level_data)
# write_to_file('Auto/Full-Auto/log/activity_dict_temp.json', all_dict)
# 读取缓存
cache_dict = load_data(cache)
now = datetime.now().timestamp()
download_current_activity(now_activities[0])
last = datetime.now().timestamp()
# 保存缓存
write_to_file(cache, cache_dict)
print(f"搜索完毕，共耗时 {round(last - now, 2)} s.\n")
print('No_result: ', no_result)
