import json
import logging
import os
import re
import time

import pyperclip
import requests
from bs4 import BeautifulSoup

SETTING_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings", "settings.json")
LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log", "app.log")
setting = {}
setting_version = "20240830"
date = time.strftime('%Y-%m-%d', time.localtime())
use_local_level = False


def ask_setting_num(_setting, key: str, exist=False, show_name=True):
    """
    列出全部{key}配置的存在情况并选择配置
    :param _setting: 设置
    :param key: 配置类型
    :param exist: 是否判断存在，True仅返回已存在的配置，False不判断
    :param show_name: 是否显示配置名称
    :return: 配置序号
    """
    log_message(f"Function 函数: ask_setting_num({_setting}, {key}, {exist}, {show_name})", logging.DEBUG, False)
    for n in range(1, 10):
        if show_name:
            try:
                print(f"{n}: {_setting[key][str(n)]['name'] if key in _setting and str(n) in _setting[key] and len(_setting[key][str(n)]) > 0 else '无'}")
            except KeyError:
                print(f"{n}: {'已存在' if key in _setting and str(n) in _setting[key] and len(_setting[key][str(n)]) > 0 else '无'}")
        else:
            print(f"{n}: {'已存在' if key in _setting and str(n) in _setting[key] and len(_setting[key][str(n)]) > 0 else '无'}")
    choose = str(int_input("b: 返回\n请选择配置序号：", 1, 1, 9, True, False))
    if choose == "b":
        return "b"
    elif exist:  # 判断存在
        if choose in _setting[key]:
            return choose
        else:
            print("未找到配置，请重新选择")
            return ask_setting_num(_setting, key)
    else:  # 不判断存在
        return choose


def ban_operator(a: list, b: list):
    """
    禁用干员检测，检查作业是否有禁用的干员
    :param a: 作业干员列表
    :param b: 禁用干员列表
    :return: True or False
    """
    set1 = set(a)
    set2 = set(b)
    r1 = set1 - set2
    r2 = set1 - r1
    return len(r2) > 0


def bool_input(question):
    """
    询问问题，返回布尔值
    :param question: 问题
    :return: True or False
    """
    user_input = input(question + " (yes/no, 为空no): ").lower()
    return user_input in ["yes", "y", "true", "t", "1", "是", "对", "真", "要"]


def build_activity_dict(data, act_id, _dict=None, key="stage_id"):
    """
    构建活动字典，将数据按活动分类
    :param data: 要分类的数据，一般为all_dict["活动关卡"][""]
    :param act_id: 活动ID，如act34side
    :param _dict: 字典，如果传入则在此基础上添加
    :param key: 生成字典的键，默认为stage_id
    :return: 活动字典，格式为{活动名: [成员1, 成员2, ...]}
    """
    log_message("Function 函数: build_activity_dict", logging.DEBUG, False)
    if _dict is None:
        _dict = {}
    for member in data:
        _key = member[key]
        if act_id in _key:
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
    log_message("Function 函数: build_complex_dict", logging.DEBUG, False)
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


def build_data_dict(level_dict, data):
    """
    构建数据字典，将数据按关卡分类
    :param level_dict: 需要下载的关卡字典
    :param data: 作业数据
    :return: 数据字典，格式为{关卡名: [作业1, 作业2, ...]}，关卡名为stage_id<<关卡代号
    """
    log_message("Function 函数: build_data_dict", logging.DEBUG, False)
    data_dict = {}
    for member in data['data']['data']:
        stage = json.loads(member['content'])['stage_name']
        if 'easy' in stage:
            continue
        elif "#f#" in stage:
            stage = stage.split("#f#")[0]
        try:
            log_message("Build data dict: " + stage + "<<" + level_dict[stage][0]['cat_three'], logging.DEBUG, False)
            key = stage + "<<" + level_dict[stage][0]['cat_three']
            if key not in data_dict:
                data_dict[key] = []
            data_dict[key].append(member)
        except KeyError:
            try:
                new_stage = cat_three_dict.get(stage, [])[0].get('stage_id', '')
                key = new_stage + "<<" + stage
                if key not in data_dict:
                    data_dict[key] = []
                data_dict[key].append(member)
            except IndexError:
                log_message(f"stage_name is not stage_id. Details: {stage} {member}", logging.WARNING, False)
    return data_dict


def build_dict(data, key: str, _dict=None):
    """
    构建字典，将数据按关键分类
    :param data: 要分类的数据
    :param key: 生成的字典的键
    :param _dict: 字典，如果传入则在此基础上添加
    :return: 生成的字典，格式为{key: [成员1, 成员2, ...]}
    """
    log_message("Function 函数: build_dict", logging.DEBUG, False)
    if _dict is None:
        _dict = {}
    for member in data:
        _key = member[key]
        if _key in _dict:
            _dict[_key].append(member)
        else:
            _dict[_key] = [member]
    return _dict


def build_operator_dict(data: dict, num: int):
    """
    构建干员字典，将干员数据按配置序号分类
    :param data: 干员数据
    :param num: 配置序号
    :return: 干员字典，格式为{配置序号: [干员1, 干员2, ...]}
    """
    log_message("Function 函数: build_operator_dict", logging.DEBUG, False)
    op_dict = {}
    item = data[str(num)]
    for member in item:
        key = member['name']
        if key in op_dict:
            op_dict[key].append(member)
        else:
            op_dict[key] = [member]
    return op_dict


def calculate_percent(item) -> float:
    """
    计算好评率，保留两位小数
    :param item: 作业数据
    :return: 好评率，保留两位小数
    """
    like, dislike = item.get('like', 0), item.get('dislike', 0)
    return round(like / (like + dislike) * 100, 2) if like + dislike > 0 else 0.00


def completeness_check(list1, opers, groups):
    """
    完备度检测，检查作业所需干员是否完备
    :param list1: 拥有的干员
    :param opers: 作业干员列表
    :param groups: 作业干员组列表
    :return: True or False or 缺少的干员(仅一个)
    """
    result = []  # 缺少的干员
    list1_set = set(list1)
    opers_set = set([oper['name'] for oper in opers])
    groups_set = {tuple(member['name'] for member in group['opers']) for group in groups}
    # 检查干员
    if opers_set.issubset(list1_set):  # 干员完备
        list1_set -= opers_set
    elif len(opers_set - list1_set) == 1:  # 缺少一个
        new_set = opers_set - list1_set
        result.append(new_set.pop())
    else:  # 缺少多个，直接返回False
        return False
    # 检查干员组
    for t in groups_set:
        if not any(member in list1_set for member in t):  # 缺少干员组
            result.append(t)
    if len(result) == 0:  # 完备
        return True
    elif len(result) == 1:  # 缺少一个
        return result[0]
    else:  # 缺少多个
        return False


def configuration(_setting, _mode="0"):
    """
    选择配置，False则返回menu
    :param _setting: 设置
    :param _mode: 是否询问，0为询问，其他为直接选择用户设置(默认)
    :return: 配置 or False
    """
    log_message("Page: CONFIGURATION 配置", logging.INFO, False)
    if _setting.get("use_default") and judge_setting(_setting, _setting['download']['default']):
        log_message(f"Use Default Configuration 使用默认配置: {_setting['download']['default']}", logging.DEBUG, False)
        return _setting
    if _mode == "0":
        print("1. 默认设置\n2. 用户设置(默认)\n3. 用户设置(其他)\n4. 自定义设置(单次)\nb. 返回")
        _mode = input("请选择配置：")
    log_message(f"Configuration 配置: {_mode}", logging.DEBUG, False)
    if _mode == "1":  # 默认设置
        return {"download": {
            "default": "0",
            "0": {
                'name': "默认设置",
                'version': setting_version,
                'title': 1,
                'save': 2,
                'path': os.path.join(os.path.dirname(os.path.abspath(__file__)), "download"),
                'order_by': 3,
                'point': 0,
                'view': 0,
                'amount': 1,
                'completeness': False,
                'completeness_mode': 1,
                'completeness_filename': 1,
                'operator_num': 1,
                'ban_operator': [],
                'only_uploader': [],
                'prefer_uploader': []
            }}}
    elif _mode == "2":  # 用户设置(默认)
        if not judge_setting(_setting, "1"):
            print("未找到默认用户设置或默认用户设置已过期，请设置")
            return False
        _setting["download"]["default"] = "1"
        return _setting
    elif _mode == "3":  # 用户设置(其他)
        while True:
            choose = ask_setting_num(_setting, 'download')
            if choose == "b":
                return False
            _setting["download"]["default"] = choose
            break
        return _setting
    elif _mode == "4":  # 自定义设置(单次)
        st = configure_download_settings()
        return {"download": {"default": "0", "0": st}}
    elif "b" in _mode.lower():  # 返回
        return False
    else:
        print("未知选项，请重新选择.")
        return configuration(_setting)


def configure_download_settings():
    """
    设置下载参数
    :return: 下载参数dict
    """
    log_message("Page: SETTING 设置", logging.INFO, False)
    setting_name = input("设置配置名称：").strip()
    setting_name = setting_name if setting_name else "Name"
    print("1. 标题.json\n2. 标题 - 作者.json\n3. 关卡代号-干员1+干员2.json")
    title = int_input("选择文件名格式（默认为1）：", 1, 1, 3)
    print("1. 替换原来的文件\n2. 保存到新文件并加上序号如 (1)\n3. 跳过，不保存")
    save = int_input("设置文件名冲突时的处理方式（默认为2）：", 2, 1, 3)
    path = input("设置保存文件夹（为空默认当前目录\\download）：").strip()
    path = path if path and os.path.isdir(path) else os.path.join(os.path.dirname(os.path.abspath(__file__)), "download")
    print(f"保存文件夹：{path}")
    order_by = int_input("1. 热度\n2. 最新\n3. 浏览量\n设置排序方式（默认为3. 浏览量）：", 3, 1, 3)
    point = int_input("设置好评率限制(0-100)（为空不限制）：", 0, 0, 100)
    view = int_input("设置浏览量限制（大于你设置的值）（为空不限制）：", 0)
    amount = int_input("设置下载数量(1-5)（为空全部下载）：", 99, 1, 5)
    completeness = bool_input("是否启用干员完备度检测？")
    if completeness:
        print(f"设定值：{completeness}")
        completeness_mode = int_input("1. 所有干员都有\n2. 缺少干员不超过1个\n设置检测条件（默认为1）：", 1, 1, 2)
        if completeness_mode == 2:
            completeness_filename = int_input("1. 仅在作业详情中显示缺少干员\n2. 在文件名前显示\"(缺)\"\n3. 在文件名前显示\"(缺[干员名])\"\n设置提示信息（默认为1）：", 1, 1, 3)
        else:
            completeness_filename = 1
        operator_num = int_input("设置干员配置序号（1-9默认为1）：", 1, 1, 9)
    else:
        print(f"设定值：{completeness}")
        completeness_mode = 1
        completeness_filename = 1
        operator_num = 1
    operator = input("设置禁用干员（多个用空格分隔）（为空不禁用）：").split()
    print(f"设定值：{operator}")
    only_uploader = input("设置只看作业站作者（多个用空格分隔）（为空不设置）：").split()
    print(f"设定值：{only_uploader}")
    prefer_uploader = input("设置优先显示作者（多个用空格分隔）（为空不设置）：").split()
    print(f"设定值：{prefer_uploader}")
    log_message(f"Setting 设置: {title}, {save}, {path}, {order_by}, {point}, {view}, {amount}, {completeness}, {completeness_mode}, {completeness_filename}, {operator_num}, {operator}, {only_uploader}", logging.DEBUG, False)
    return {
        'name': setting_name,
        'version': setting_version,
        'title': title,
        'save': save,
        'path': path,
        'order_by': order_by,
        'point': point,
        'view': view,
        'amount': amount,
        'completeness': completeness,
        'completeness_mode': completeness_mode,
        'completeness_filename': completeness_filename,
        'operator_num': operator_num,
        'ban_operator': operator,
        'only_uploader': only_uploader,
        'prefer_uploader': prefer_uploader
    }


def download_current_activity(activity, mode):
    """
    下载当前活动
    :param activity: 活动名
    :param mode: 下载模式，1为默认设置，2为其他设置
    :return: 无返回值
    """
    global info
    log_message(f"Function 函数: download_current_activity({activity}, {mode})", logging.DEBUG, False)
    stage_dict = {}
    activity_id = activity_data[activity]['id']
    if activity in all_dict["活动关卡"]:
        stage_dict = build_dict(all_dict["活动关卡"][activity], "stage_id")
    elif activity.replace("·复刻", "") in all_dict["活动关卡"]:
        activity = activity.replace("·复刻", "")
        stage_dict = build_dict(all_dict["活动关卡"][activity], "stage_id")
    stage_dict = build_activity_dict(all_dict["活动关卡"][""], activity_id, _dict=stage_dict)
    log_message(f"stage_dict: {stage_dict}", logging.DEBUG, False)
    write_to_file("log/stage_dict_temp.json", stage_dict)
    if mode == 1:
        _setting = configuration(setting, "2")
    else:
        _setting = configuration(setting, "3")
    if not _setting:
        info = "未找到用户设置或用户设置已过期，请设置"
        return menu()
    now = time.time()
    less_search(stage_dict, _setting, "活动关卡", activity, activity_id)
    log_message(f"搜索活动关卡-{activity}完毕，共耗时 {round(time.time() - now, 2)} s.", logging.INFO, False)
    input(f"搜索完毕，共耗时 {round(time.time() - now, 2)} s.\n按回车键返回")
    return menu()


def extract_activity_from_stage_id(stage_id: str):
    """
    从 stage_id 中提取activity_id，如act34side
    :param stage_id: 关卡ID
    :return: {activity_id}_
    """
    match = re.search(r'(.+?)_', stage_id)
    if match:
        log_message(f"Extract activity from stage_id: {match.group(1)}", logging.DEBUG, False)
        return match.group(1) + '_'
    return None


def extract_integer_from_stage_id(stage_id: str):
    """
    从 stage_id 中提取章节数字
    :param stage_id: 关卡ID
    :return: 章节数字str
    """
    match = re.search(r'_(\d+)-', stage_id)
    if match:
        return match.group(1)
    return "0"


def generate_filename(content, title, uploader, keyword, prefer):
    """
    生成文件名
    :param content: 作业数据
    :param title: 文件名格式
    :param uploader: 作业作者
    :param keyword: 关卡代号
    :param prefer: 是否优先显示作者
    :return: 文件名
    """
    file_name = ""
    try:
        if prefer:  # 优先显示作者
            file_name += f"({uploader})"
        diff = content.get("difficulty", 0)
        if diff == 1:  # 仅普通
            file_name += "(仅普通)"
        elif diff == 2:  # 仅突袭
            file_name += "(仅突袭)"
        if title == 1:  # 标题
            file_name += content["doc"]["title"]
        elif title == 2:  # 标题 - 作者
            file_name += content["doc"]["title"] + " - " + uploader
        elif title == 3:  # 关卡代号-干员1+干员2
            file_name += generate_filename_mode3(keyword, content)
        else:
            input("未知文件名格式，请联系开发者")
    except KeyError:
        t = time.time()
        log_message(f'File name format error 文件名格式错误, {t}, {content}, {title}, {uploader}, {keyword}', logging.ERROR)
        file_name = f"ERROR{t}"
    return replace_dir_char(file_name)


def generate_filename_mode3(stage_name, data):
    """
    生成模式3的文件名，如关卡代号-干员1+干员2
    :param stage_name: 关卡代号
    :param data: 作业数据
    :return: 文件名
    """
    opers = data.get('opers', [])
    groups = data.get('groups', [])
    names_parts = ['+'.join(oper.get('name', '') for oper in opers), '+'.join(group.get('name', '') for group in groups)]
    names = '+'.join(part for part in names_parts if part)  # 只连接非空的部分
    if len(names) > 100:
        log_message(f"File name too long 文件名过长: {names}, {stage_name}", logging.WARNING)
        names = "文件名过长不予显示"
    return f'{stage_name}_{names}'


def get_cat_three_info(_cat_three_dict, cat_three, key):  # 通过cat_three获取信息,失败返回cat_three
    return _cat_three_dict.get(cat_three, [{}])[0].get(key, cat_three)


def get_level_data():
    """
    访问 https://prts.maa.plus/arknights/level 获取关卡数据
    :return: 关卡数据
    """
    try:
        response = requests.get('https://prts.maa.plus/arknights/level')
    except requests.exceptions.SSLError:
        log_message(f"SSL error 请求失败，请检查网络连接", logging.ERROR)
        exit(-1)
    # write_to_file("log/level_data_temp.json", response.json(), True)
    log_message(f"Successfully obtained level data 成功获取关卡数据", console_output=False)
    return response.json()['data'] if response.ok else []


def get_activity_data():
    """
    访问 https://prts.wiki/w/%E6%B4%BB%E5%8A%A8%E4%B8%80%E8%A7%88 获取活动数据，格式为{'name': 活动名, 'status': 状态}
    :return: 活动数据, 进行中的活动
    """
    try:
        response = requests.get('https://prts.wiki/w/%E6%B4%BB%E5%8A%A8%E4%B8%80%E8%A7%88')
    except requests.exceptions.SSLError:
        log_message(f"SSL error 请求失败，请检查网络连接", logging.ERROR)
        exit(-1)
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
        if ("支线故事" in category or "故事集" in category) and activity_page:
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
                                task_stage_id = get_cat_three_info(cat_three_dict, task_cat_three, "stage_id")
                                activity_id = extract_activity_from_stage_id(task_stage_id)
                                break
                    if "-1" in task_cat_three:
                        break
            elif status_span and "未开始" in status_span.text:
                status = "未开始"
            activities[activity_name] = {'status': status, 'id': activity_id}
    return activities, ongoing_activities


def input_level():
    global info
    log_message("Select type 选择类型", logging.DEBUG, False)
    keys = ["活动关卡", "主题曲", "剿灭作战", "资源收集"]
    for i, key in enumerate(keys):
        print(f"{i + 1}. {key}")
    print("b. 返回")
    choose = input("请选择要搜索的关卡类型：").strip()
    if choose.isdigit() and 1 <= int(choose) <= len(keys):
        key = keys[int(choose) - 1]
        activity = select_from_list(all_dict, key)  # 选择活动（二级）
        log_message(f"已选择 {key}-{activity}", logging.INFO, False)
        print(f"已选择 {key}-{activity}")
        if activity == "全部":
            stage_dict = {}
            for sub_key, sub_dict in all_dict[key].items():
                stage_dict = build_dict(sub_dict, "stage_id", stage_dict)
        elif not activity:
            return menu()
        else:
            stage_dict = build_dict(all_dict[key][activity], "stage_id")
            if key == "活动关卡":
                activity_id = extract_activity_from_stage_id(all_dict["活动关卡"][activity][0]['stage_id'])
                stage_dict = build_activity_dict(all_dict["活动关卡"][""], activity_id, _dict=stage_dict)
            log_message(f"stage_dict: {stage_dict}", logging.DEBUG, False)
        # write_to_file("log/stage_dict_temp.json", stage_dict, True)
        _setting = configuration(setting)
        if not _setting:
            info = "未找到用户设置或用户设置已过期，请设置"
            return menu()
        now = time.time()
        if activity == "全部":  # 搜索全部
            less_search(stage_dict, _setting, key, "全部", key)
        elif key == "活动关卡":  # 搜索活动关卡使用extract_activity_from_stage_id
            less_search(stage_dict, _setting, key, activity, extract_activity_from_stage_id(all_dict[key][activity][0]['stage_id']))
        elif key == "主题曲":  # 搜索主题曲使用extract_integer_from_stage_id
            less_search(stage_dict, _setting, key, activity, extract_integer_from_stage_id(all_dict[key][activity][0]['stage_id']) + "-")
        elif key == "剿灭作战" or key == "资源收集":  # 搜索剿灭作战或资源收集直接搜索activity
            less_search(stage_dict, _setting, key, activity, activity)
        else:
            log_message(f"不知道你怎么点进来的", logging.ERROR)
        log_message(f"搜索{key}-{activity}完毕，共耗时 {round(time.time() - now, 2)} s.", logging.INFO, False)
        input(f"搜索完毕，共耗时 {round(time.time() - now, 2)} s.\n按回车键返回")
        return menu()
    elif "b" in choose.lower():
        return menu()
    else:
        print("未知选项，请重新选择")
        return input_level()


def int_input(prompt: str, default, min_value=None, max_value=None, allow_return=False, allow_print=True):
    """
    输入整数，如果输入为空或非整数则返回默认值。若填写最小值和最大值则超出范围返回默认值
    :param prompt: 问题
    :param default: 默认值
    :param min_value: 允许的最小值
    :param max_value: 允许的最大值
    :param allow_return: 是否允许b返回menu
    :param allow_print: 是否打印设定值
    :return: 输入的整数
    """
    try:
        log_message(f"Function 函数: int_input({prompt}, {default}, {min_value}, {max_value})", logging.DEBUG, False)
        value = input(prompt).strip()
        log_message(f"Input 输入: {value}", logging.DEBUG, False)
        if allow_return and "b" in value.lower():
            return "b"
        value = int(value) if value else default
        if min_value is not None and value < min_value:
            value = default
        if max_value is not None and value > max_value:
            value = default
        if allow_print:
            print(f"设定值：{value}")  # 打印设定值
        return value
    except ValueError:
        if allow_print:
            print(f"输入无效，设置为默认值：{default}")
        return default


def is_valid_json(test_string):
    try:
        json.loads(test_string)
        return True
    except json.JSONDecodeError:
        return False


def judge_setting(_setting, num: str):
    if "download" in _setting and num in _setting["download"] and _setting["download"][num]["version"] == setting_version:
        log_message(f"设置 {num} 为最新设置", logging.DEBUG, False)
        return True
    else:
        log_message(f"设置 {num} 不存在或非最新设置", logging.DEBUG, False)
        return False


def less_search(stage_dict, _setting, search_key, activity, keyword):  # 搜索并下载
    """
    批量搜索，仅搜索一次
    :param stage_dict: 当前活动的关卡字典
    :param _setting: 用户设置
    :param search_key: 关卡类型，如活动关卡
    :param activity: 活动中文名，如生路
    :param keyword: 搜索词，一般为活动ID，如act34side
    :return: 无返回值
    """
    st = _setting["download"][_setting["download"]["default"]]
    os.makedirs(os.path.join(st["path"], search_key, activity.replace("·复刻", "")), exist_ok=True)
    data = search(keyword, st["order_by"])  # 仅搜索一次
    data_dict = build_data_dict(stage_dict, data)  # 构建关卡字典，将数据按关卡分类
    if st["completeness"]:
        _setting["operator_dict"] = build_operator_dict(_setting["operator"], st["operator_num"])
    for key, value in data_dict.items():  # 遍历关卡字典
        key1, key2 = key.split("<<")
        #  key1为stage_id，key2为name
        total = len(value)
        log_message(f"搜索 {key1} {key2} 共获得 {total} 个数据")
        amount = 0
        for member in value:
            point = calculate_percent(member)
            if member["views"] >= st["view"] and point >= st["point"] and amount < st["amount"]:
                if st["only_uploader"] == [] or member["uploader"] in st["only_uploader"]:
                    if process_and_save_content(key2, member, _setting, search_key, activity, point):
                        amount = amount + 1
                if amount >= st["amount"]:
                    break
            elif amount >= st["amount"]:
                break


def load_level_data():
    if use_local_level:
        if os.path.exists("cache/level_data.json"):
            with open("cache/level_data.json", 'r', encoding='utf-8') as f:
                _level_data = json.load(f)
            log_message("Successfully loaded local level data. 成功加载本地关卡数据")
            return _level_data
        else:
            log_message("Local level data not found. 未找到本地关卡数据", logging.ERROR)
    _level_data = get_level_data()
    # write_to_file("log/level_data_temp.json", _level_data, True)
    log_message("Successfully retrieved online level data. 成功获取在线关卡数据")
    _level_data = add_level_data(_level_data)
    log_message("Successfully added additional level data. 成功添加额外关卡数据")
    return _level_data


def add_level_data(ld):
    log_message("Function 函数: add_level_data", logging.DEBUG, False)
    if not os.path.exists("cache/add_level.json"):
        log_message("Additional level data not found. 未找到额外关卡数据", logging.ERROR)
        return ld
    with open("cache/add_level.json", 'r', encoding='utf-8') as f:
        add_data = json.load(f)
    ld = ld + add_data
    # write_to_file("log/new_level_data.json", ld, True)
    return ld


def load_settings():
    global setting, info
    try:
        if os.path.exists(SETTING_PATH):
            with open(SETTING_PATH, 'r', encoding='utf-8') as file:
                setting = json.load(file)
            log_message("Setting loaded successfully 设置加载成功", logging.INFO, False)
            return True
    except json.JSONDecodeError:
        log_message("Setting file is not valid JSON 设置文件不是有效的JSON", logging.ERROR)
        info = "设置文件不是有效的JSON"
        return False


# 初始化日志配置
def setup_logging():
    _logger = logging.getLogger(__name__)
    _logger.setLevel(logging.DEBUG)

    # 创建一个handler，用于写入日志文件
    try:
        file_handler = logging.FileHandler(LOG_PATH, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
    except (OSError, IOError) as e:
        print(f"无法创建文件处理器: {e}")
        return None

    # 定义handler的输出格式
    formatter = logging.Formatter('[%(asctime)s][%(levelname)s] %(message)s')
    file_handler.setFormatter(formatter)

    # 给logger添加handler
    _logger.addHandler(file_handler)

    return _logger


def log_message(message, level=logging.INFO, console_output=True):
    """
    记录日志
    :param message: 要记录的消息
    :param level: 日志级别
    :param console_output: 是否输出到控制台
    :return: 无返回值
    """
    if logger is None:
        return

    # 如果console_output为True，则创建一个handler，用于输出到控制台
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter('[%(asctime)s][%(levelname)s] %(message)s'))
        logger.addHandler(console_handler)

    # 根据日志级别，记录日志
    logger.log(level, message)

    # 移除handler，防止日志重复
    if console_output:
        logger.removeHandler(console_handler)


def menu():
    log_message("Page: MENU 菜单", logging.DEBUG, False)
    choice_dict = {1: "单次搜索并下载", 2: "批量搜索并下载", 999: "设置"}
    os.system("cls")
    if now_activities:
        choice_dict[11] = f"以 用户配置(默认) 下载: {now_activities[0]}"
        choice_dict[12] = f"以 用户配置(其他) 下载: {now_activities[0]}"
    if info != "":
        log_message(f"info: {info}", logging.INFO, False)
        print(info)
    print("=" * 60)
    if "download" in setting and setting.get("use_default") and "default" in setting["download"]:
        try:
            print(f"当前默认配置: 配置 {setting['download']['default']} {setting['download'][setting['download']['default']]['name']}")  # 显示当前下载设置
        except KeyError:
            print(f"当前默认配置: 配置 {setting['download']['default']}")  # 显示当前下载设置
    choice_dict = dict(sorted(choice_dict.items()))  # 根据数字排序dict
    new_list = [value for i, (key, value) in enumerate(choice_dict.items(), start=1)]
    for i, value in enumerate(new_list, start=1):
        print(f"{i}. {value}")
    print("e. 退出")
    choose = input("请选择操作：")
    if choose.isdigit() and 1 <= int(choose) <= len(new_list):
        key = new_list[int(choose) - 1]
        print(f"已选择 {key}")
        if key == "单次搜索并下载":
            return mode1()
        elif key == "批量搜索并下载":
            log_message("Batch download 批量下载", logging.DEBUG, False)
            os.system("cls")
            print("已进入批量搜索并下载模式，（输入b返回）")
            return input_level()
        elif "以 用户配置(默认) 下载: " in key:
            log_message("Download current activity 默认配置下载当前活动", logging.DEBUG, False)
            os.system("cls")
            return download_current_activity(now_activities[0], 1)
        elif "以 用户配置(其他) 下载: " in key:
            log_message("Download current activity 其他配置下载当前活动", logging.DEBUG, False)
            os.system("cls")
            return download_current_activity(now_activities[0], 2)
        elif key == "设置":
            return settings_set()
    elif "e" in choose.lower():
        return True


def mode1():
    global info
    log_message("Single search 单次搜索", logging.INFO, False)
    os.system("cls")
    print("已进入单次搜索并下载模式，（输入back返回）")
    keyword = input("请输入关卡代号：").strip().upper()
    if "back" in keyword.lower():
        return menu()
    _setting = configuration(setting)
    if not _setting:
        info = "未找到用户设置或用户设置已过期，请设置"
        return menu()
    st = _setting["download"][_setting["download"]["default"]]
    os.system("cls")
    now = time.time()
    log_message(f'保存目录：{st["path"]}')
    os.makedirs(st["path"], exist_ok=True)
    data = search(keyword, st["order_by"])
    total = data["data"]["total"]
    log_message(f"搜索 {keyword} 共获得 {total} 个数据")
    amount = 0
    for member in data["data"]["data"]:
        point = calculate_percent(member)
        if member["views"] >= st["view"] and point >= st["point"] and amount < st["amount"]:
            if st["only_uploader"] == [] or member["uploader"] in st["only_uploader"]:
                if process_and_save_content(keyword, member, _setting, keyword, "单次下载", point):
                    amount = amount + 1
            if amount >= st["amount"]:
                break
        elif amount >= st["amount"]:
            break
    last = time.time()
    input(f"搜索完毕，共耗时 {round(last - now, 2)} s.\n按回车键返回")
    return menu()


def process_and_save_content(keyword, _member, _setting, key, activity, _percent=0.00):
    """
    进行禁用干员检测、完备度检测并写出文件
    :param keyword: 关卡stage_name
    :param _member: 作业数据
    :param _setting: 用户设置
    :param key: 关卡类型，如活动关卡
    :param activity: 活动中文名，如生路
    :param _percent: 好评率
    :return: True or False
    """
    st = _setting["download"][_setting["download"]["default"]]
    if key != "" and activity != "":
        path = os.path.join(st["path"], key, activity.replace("·复刻", ""))
    else:
        log_message(f"ERROR 错误: {key}, {activity}", logging.ERROR)
        path = st["path"]
    os.makedirs(path, exist_ok=True)
    content = json.loads(_member["content"])
    names = [oper.get('name', '') for oper in content.get('opers', '')]
    prefer = _member["uploader"] in st["prefer_uploader"]
    file_name = generate_filename(content, st["title"], _member["uploader"], keyword, prefer)
    # 禁用干员检测
    if st["ban_operator"]:
        if ban_operator(names, st["ban_operator"]):
            log_message(f"{file_name} 禁用干员检测不通过", logging.WARNING)
            return False
    # 完备度检测
    if st["completeness"]:
        result = completeness_check(list(_setting["operator_dict"].keys()), content.get('opers', []), content.get('groups', []))
        if result is True:  # 完备
            content['doc']['details'] = f"——————————\n作业更新日期: {_member['upload_time']}\n统计更新日期: {date}\n好评率：{_percent}%  浏览量：{_member['views']}\n来源：{_member['uploader']}  ID：{_member['id']}\n——————————\n" + content['doc']['details']
        elif result is False:  # 缺少多个
            log_message(f"{file_name} 完备度检测不通过", logging.INFO, False)
            return False
        else:  # 缺少一个
            if st['completeness_mode'] == 1:  # 仅下载所有干员都有
                log_message(f"模式1 {file_name} 缺少干员(组)：{result} 不下载", logging.INFO, False)
                return False
            else:  # 仅下载缺少干员不超过1个
                log_message(f"{file_name} 缺少干员(组)：{result}", logging.INFO, False)
                if st['completeness_filename'] == 2:  # 在文件名前显示"(缺)"
                    file_name = f"(缺) " + file_name
                elif st['completeness_filename'] == 3:  # 在文件名前显示"(缺[干员名])"
                    file_name = f"(缺{result})" + file_name
                content = json.loads(_member["content"])
                content['doc']['details'] = f"——————————\n作业更新日期: {_member['upload_time']}\n统计更新日期: {date}\n好评率：{_percent}%  浏览量：{_member['views']}\n来源：{_member['uploader']}  ID：{_member['id']}\n——————————\n\n缺少干员(组):  {result}\n\n" + content['doc']['details']
    else:  # 未启用完备度检测
        content['doc']['details'] = f"——————————\n作业更新日期: {_member['upload_time']}\n统计更新日期: {date}\n好评率：{_percent}%  浏览量：{_member['views']}\n来源：{_member['uploader']}  ID：{_member['id']}\n——————————\n" + content['doc']['details']
    file_path = os.path.join(path, f"{file_name}.json")
    if st["save"] == 1:  # 替换原来的文件
        if os.path.exists(file_path):
            os.remove(file_path)
    elif st["save"] == 2:  # 保存到新文件并加上序号如 (1)
        _ = 1
        while os.path.exists(file_path):  # 文件已存在
            file_path = os.path.join(path, f"{file_name} ({_}).json")
            _ = _ + 1
    elif st["save"] == 3:  # 跳过，不保存
        if os.path.exists(file_path):
            log_message(f"跳过文件：{file_path}", logging.INFO)
            return False
    else:
        log_message(f"ERROR 错误: {st['save']}", logging.ERROR)
        return False
    write_to_file(file_path, content)
    return True


def replace_dir_char(text):
    for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
        text = text.replace(char, '')
    return text


def save_setting(data):
    os.makedirs(os.path.dirname(SETTING_PATH), exist_ok=True)
    with open(SETTING_PATH, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    log_message(f"Setting saved successfully 设置保存成功", logging.INFO, False)
    return True


def search(keyword: str, search_mode: int) -> dict:
    order_by = {1: "hot", 2: "id", 3: "views"}.get(search_mode, "views")
    url = f"https://prts.maa.plus/copilot/query?desc=true&limit=99999&page=1&order_by={order_by}&level_keyword={keyword}"
    headers = {
        "Origin": "https://prts.plus",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
    }
    try:
        log_message(f"Search URL: {url}", logging.DEBUG, False)
        response = requests.get(url, headers=headers)
        return response.json()
    except requests.exceptions.SSLError:
        log_message("SSL certificate verification failed SSL证书验证失败", logging.ERROR)
        print("=" * 60)
        input("!!!SSL证书验证失败，请关闭系统代理!!!\n")
        return menu()


def select_from_list(_activity_dict, key_one):
    """
    选择活动（二级）可输入数字或关键字，支持模糊匹配，若匹配多个则继续选择
    :param _activity_dict: 活动字典
    :param key_one: 关卡类型
    :return: 二级中文名
    """
    log_message("选择关卡", logging.INFO, False)
    if key_one == "主题曲":
        stage_dict = {}
        for stage_name, item in _activity_dict[key_one].items():
            key = int(extract_integer_from_stage_id(item[0]['stage_id']))
            stage_dict[key] = stage_name
        matching_keys = [value for key, value in sorted(stage_dict.items())]
    else:
        matching_keys = list(_activity_dict[key_one].keys())  # 初始匹配所有keys
    matching_keys.append("全部")
    while True:
        print("请选择关卡：")
        for i, key in enumerate(matching_keys):
            print(f"{i}. {key}")
        user_input = input("请输入关卡名称或序号：").strip()

        # 如果用户输入是数字且在范围内，直接返回对应的活动关卡
        if user_input.isdigit() and 0 <= int(user_input) <= len(matching_keys) - 1:
            return matching_keys[int(user_input)]

        # 更新匹配的keys列表
        new_matching_keys = [key for key in matching_keys if user_input.lower() in key.lower()]
        if new_matching_keys:
            if len(new_matching_keys) == 1:
                # 如果只有一个匹配的key，直接返回这个key
                return new_matching_keys[0]
            else:
                # 如果有多个匹配的key，更新匹配列表并继续循环
                matching_keys = new_matching_keys
                continue

        elif "b" in user_input.lower():
            return False

        else:
            print("未找到匹配项，请重新选择")
            # 如果没有匹配项，重置匹配列表为所有keys并继续循环
            matching_keys = list(_activity_dict[key_one].keys())
            matching_keys.append("全部")
            continue


def settings_set():
    global setting, info
    os.system("cls")
    log_message("Page: SETTING 设置", logging.DEBUG, False)
    if "download" in setting and setting.get("use_default") and "default" in setting["download"]:
        print(f"当前默认配置: 配置 {setting['download']['default']}")  # 显示当前下载设置
    print(f"0. 是否使用默认配置: {setting.get('use_default', False)}")
    print("1. 设置默认配置")
    print("2. 下载配置")
    print("3. 干员配置")
    print("b. 返回并保存")
    choose1 = input("请选择操作：")
    if choose1 == "0":  # 是否使用默认配置
        setting['use_default'] = not setting.get('use_default', False)
    elif choose1 == "1":  # 设置默认配置
        if "download" in setting and setting.get("use_default") and "default" in setting["download"]:
            print(f"当前默认配置: 配置 {setting['download']['default']}")  # 显示当前下载设置
        choose2 = ask_setting_num(setting, 'download', True)
        if choose2 != "b":
            if "download" not in setting:
                setting["download"] = {}
            setting["download"]["default"] = choose2
            print(f"已设置默认配置为: 配置 {choose2}")
    elif choose1 == "2":  # 下载配置
        choose2 = str(int_input("下载配置：\n1. 设置\n2. 查看配置\n请选择操作：", "b", 1, 2))
        if choose2 == "1":  # 设置下载配置
            choose3 = ask_setting_num(setting, 'download', True)
            if choose3 != "b":
                if "download" not in setting:
                    setting["download"] = {}
                setting["download"][choose3] = configure_download_settings()
        elif choose2 == "2":  # 查看下载配置
            if "download" in setting:
                choose3 = ask_setting_num(setting, 'download', True)
                if choose3 != "b":
                    print(f"配置{choose3}: " + json.dumps(setting["download"][choose3], ensure_ascii=False, indent=4))
            else:
                print("未找到下载配置, 请先设置")
    elif choose1 == "3":  # 干员配置
        choose2 = str(int_input("干员配置：\n1. 设置\n2. 查看配置\n请选择操作：", "b", 1, 2))
        if choose2 == "1":  # 设置干员配置
            choose3 = ask_setting_num(setting, 'operator', show_name=False)
            if choose3 != "b":
                input(f"正在设置: 配置 {choose3} , 请使用MAA干员识别工具并复制到剪贴板\n按回车键继续\n")
                os.makedirs(os.path.dirname(SETTING_PATH), exist_ok=True)
                clipboard_content = pyperclip.paste()
                if is_valid_json(clipboard_content):  # 检查是否为有效的JSON
                    if "operator" not in setting:
                        setting["operator"] = {}
                    setting["operator"][choose3] = json.loads(clipboard_content)
                    print(f"干员配置 {choose3} 已保存, 共有 {len(setting['operator'][choose3])} 个干员")
                else:
                    print("无效的JSON数据, 请重新设置")
        elif choose2 == "2":  # 查看干员配置
            if "operator" in setting:
                choose3 = ask_setting_num(setting, 'operator', True, False)
                if choose3 != "b":
                    print(f"配置 {choose3} 当前共有 {len(setting['operator'][choose3])} 个干员")
            else:
                print("未找到干员配置, 请先设置")
    elif choose1 == "b":  # 返回并保存
        save_setting(setting)
        info = "设置保存成功"
        return menu()
    return settings_set()


def write_to_file(file_path, content, overwrite=False):
    if not overwrite and os.path.exists(file_path):
        return False
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(content, file, ensure_ascii=False, indent=4)
        log_message(f"write_to_file 写出文件: {file_path}", console_output=False)
    return True


if os.path.exists(LOG_PATH):
    os.remove(LOG_PATH)
os.makedirs("log", exist_ok=True)
# 单例日志记录器
logger = setup_logging()
log_message("Program start 程序启动", logging.INFO)
info = ""
level_data = load_level_data()
all_dict = build_complex_dict(level_data)
cat_three_dict = build_dict(level_data, "cat_three")
activity_data, now_activities = get_activity_data()
# 手动添加活动
# activity_data["追迹日落以西"] = {"status": "进行中", "id": "act37side"}
# now_activities = ['追迹日落以西']

if load_settings():
    log_message("Successfully loaded settings. 成功加载设置")
# write_to_file("log/cat_three_dict_temp.json", cat_three_dict, True)
# write_to_file("log/all_dict_temp.json", all_dict, True)
while True:
    if menu():
        break
log_message("Program end 程序结束", logging.INFO)
