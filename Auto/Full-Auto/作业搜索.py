import requests
import json
import time
import os
import re
import logging
import pyperclip

SETTING_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings", "settings.json")
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log", "app.log")
setting = {}
setting_version = "20240710"
date = time.strftime('%Y-%m-%d', time.localtime())
use_local_level = False


def is_valid_json(test_string):
    """
    检查字符串是否为有效的JSON
    :param test_string: 要检查的字符串
    :return: True or False
    """
    try:
        json.loads(test_string)
        return True
    except json.JSONDecodeError:
        return False


def save_setting(data):
    """
    保存设置
    :param data: 要保存的数据
    :return: True
    """
    os.makedirs(os.path.dirname(SETTING_PATH), exist_ok=True)
    with open(SETTING_PATH, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    log_message(f"Setting saved successfully 设置保存成功", logging.INFO, False)
    return True


def write_to_file(file_path, content):
    """
    将内容写入文件
    :param file_path: 文件路径
    :param content: 要写入的内容
    :return: 无返回值
    """
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(content, file, ensure_ascii=False, indent=4)
        log_message(f"write_to_file 写出文件: {file_path}", console_output=False)


def delete_log_file():
    """
    删除旧日志文件
    :return: 无返回值
    """
    if os.path.exists(log_path):
        os.remove(log_path)


def log_message(message, level=logging.INFO, console_output=True):
    """
    记录日志
    :param message: 要记录的消息
    :param level: 日志级别
    :param console_output: 是否输出到控制台
    :return: 无返回值
    """
    # 创建一个logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)  # 设置日志级别

    # 创建一个handler，用于写入日志文件
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    # 定义handler的输出格式
    formatter = logging.Formatter('[%(asctime)s][%(levelname)s] %(message)s')
    file_handler.setFormatter(formatter)

    # 给logger添加handler
    logger.addHandler(file_handler)

    # 如果console_output为True，则创建一个handler，用于输出到控制台
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # 根据日志级别，记录日志
    if level == logging.DEBUG:
        logger.debug(message)
    elif level == logging.INFO:
        logger.info(message)
    elif level == logging.WARNING:
        logger.warning(message)
    elif level == logging.ERROR:
        logger.error(message)
    elif level == logging.CRITICAL:
        logger.critical(message)

    # 移除handler，防止日志重复
    logger.removeHandler(file_handler)
    if console_output:
        # noinspection PyUnboundLocalVariable
        logger.removeHandler(console_handler)


def get_level_data():
    """
    获取关卡数据
    :return: 关卡数据
    """
    response = requests.get('https://prts.maa.plus/arknights/level')
    write_to_file("log/level_data_temp.json", response.json())
    log_message(f"Successfully obtained level data 成功获取关卡数据", console_output=False)
    return response.json()['data'] if response.ok else []


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


def build_data_dict(level_dict, data):
    """
    构建数据字典，将数据按关卡分类
    :param level_dict: 需要下载的关卡字典
    :param data: 作业数据
    :return: 数据字典，格式为{关卡名: [作业1, 作业2, ...]}，关卡名为stage_id<<关卡代号
    """
    data_dict = {}
    for member in data['data']['data']:
        stage = json.loads(member['content'])['stage_name']
        if any(substring in stage for substring in ['#f#', 'easy']):
            continue
        try:
            log_message("Build data dict: " + stage + "<<" + level_dict[stage][0]['cat_three'], logging.DEBUG, False)
            key = stage + "<<" + level_dict[stage][0]['cat_three']
            if key not in data_dict:
                data_dict[key] = []
            data_dict[key].append(member)
        except KeyError:
            new_stage = cat_three_dict.get(stage, [])[0].get('stage_id', '')
            if new_stage in level_dict:
                key = new_stage + "<<" + stage
                if key not in data_dict:
                    data_dict[key] = []
                data_dict[key].append(member)
            else:
                log_message(f"stage_name is not stage_id. Details: {stage} {member}", logging.WARNING)
    return data_dict


def build_operator_dict(data: dict, num: int):
    """
    构建干员字典，将干员数据按配置序号分类
    :param data: 干员数据
    :param num: 配置序号
    :return: 干员字典，格式为{配置序号: [干员1, 干员2, ...]}
    """
    op_dict = {}
    item = data[str(num)]
    for member in item:
        key = member['name']
        if key in op_dict:
            op_dict[key].append(member)
        else:
            op_dict[key] = [member]
    return op_dict


def ban_operator(a: list, b: list):  # 禁用干员检测
    """
    检查是否有禁用的干员
    :param a: 作业干员列表
    :param b: 禁用干员列表
    :return: True or False
    """
    set1 = set(a)
    set2 = set(b)
    r1 = set1 - set2
    r2 = set1 - r1
    return len(r2) > 0


def completeness_check(list1, opers, groups):
    """
    完备度检测
    :param list1: 拥有的干员
    :param opers: 作业干员列表
    :param groups: 作业干员组列表
    :return: True or False or 缺少的干员
    """
    def check_group():
        for t in groups_set:
            if not any(member in list1_set for member in t):
                result.append(t)
        if len(result) == 0:  # 完备
            return True
        elif len(result) == 1:  # 缺少一个
            return result[0]
        else:  # 缺少多个
            return False

    result = []  # 缺少的干员
    list1_set = set(list1)
    opers_set = set([oper['name'] for oper in opers])
    groups_set = {tuple(member['name'] for member in group['opers']) for group in groups}
    if opers_set.issubset(list1_set):
        list1_set -= opers_set
        return check_group()
    elif len(opers_set - list1_set) == 1:
        new_set = opers_set - list1_set
        result.append(new_set.pop())
        return check_group()
    else:  # 缺少多个
        return False


def load_settings(num="1"):
    """
    判断设置版本并加载设置到全局变量
    :param num: 下载设置序号
    :return: True or False
    """
    global setting
    if os.path.exists(SETTING_PATH):
        with open(SETTING_PATH, 'r', encoding='utf-8') as file:
            setting = json.load(file)
        if "download" in setting and setting["download"].get(num, {}).get("version", "") == setting_version:
            log_message(f"Settings loaded successfully 成功加载设置", console_output=False)
            return True
        else:
            log_message(f"Version mismatch set 设置版本不匹配", logging.ERROR, False)
    return False


def calculate_percent(item):
    """
    计算好评率
    :param item: 作业数据
    :return: 好评率，保留两位小数
    """
    like, dislike = item.get('like', 0), item.get('dislike', 0)
    return round(like / (like + dislike) * 100, 2) if like + dislike > 0 else 0


def configuration():
    """
    选择配置
    :return: 配置
    """
    print("1. 默认设置\n2. 用户设置(默认)\n3. 用户设置(其他)\n4. 自定义设置(单次)")
    _mode = input("请选择配置：")
    log_message(f"Configuration 配置: {_mode}", logging.DEBUG, False)
    if _mode == "1":
        return {"download": {"0": {
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
            'operator_num': 1,
            'ban_operator': [],
            'only_uploader': []
        }}}
    elif _mode == "2":
        if not load_settings("1"):
            return menu("未找到用户设置或用户设置已过期，请设置")
        setting["download"]["0"] = setting["download"]["1"]
        return setting
    elif _mode == "3":
        while True:
            choose = ask3('download')
            if choose in setting["download"]:
                if not load_settings(choose):
                    print("未找到用户设置或用户设置已过期，请设置")
                else:
                    setting["download"]["0"] = setting["download"][choose]
                    break
        return setting
    elif _mode == "4":
        st = configure_download_settings()
        return {"download": {"0": st}}
    elif "back" in _mode.lower():
        return menu()
    else:
        print("未知选项，请重新选择，返回请输入back")
        return configuration()


def search(keyword: str, search_mode: int) -> dict:
    """
    单次搜索
    :param keyword: 搜索level_keyword
    :param search_mode: 排序方式
    :return: 搜索结果json
    """
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


def process_and_save_content(keyword, _member, _setting, key, activity, _percent=0):
    """
    处理并保存作业内容
    :param keyword: 关卡stage_name
    :param _member: 作业数据
    :param _setting: 用户设置
    :param key: 关卡类型，如活动关卡
    :param activity: 活动中文名，如生路
    :param _percent: 好评率
    :return: True or False
    """
    st = _setting["download"]["0"]
    if key != "" and activity != "":
        path = os.path.join(st["path"], key, activity)
    else:
        log_message(f"ERROR 错误: {key}, {activity}", logging.ERROR)
        path = st["path"]
    os.makedirs(path, exist_ok=True)
    content = json.loads(_member["content"])
    names = [oper.get('name', '') for oper in content.get('opers', '')]
    file_name = generate_filename(content, st["title"], _member["uploader"], keyword)
    # 禁用干员检测
    if st["ban_operator"]:
        if ban_operator(names, st["ban_operator"]):
            log_message(f"{file_name} 禁用干员检测不通过", logging.WARNING)
            return False
    # 完备度检测
    if st["completeness"]:
        result = completeness_check(list(_setting["operator_dict"].keys()), content.get('opers', []), content.get('groups', []))
        if result is True:  # 完备
            content['doc']['details'] = f"作业更新日期: {_member['upload_time']}\n统计更新日期: {date}\n好评率：{_percent}%  浏览量：{_member['views']}\n来源：{_member['uploader']}  ID：{_member['id']}\n\n" + content['doc']['details']
        elif result is False:  # 缺少多个
            log_message(f"{file_name} 完备度检测不通过", logging.INFO, False)
            return False
        else:  # 缺少一个
            if st['completeness_mode'] == 1:  # 仅下载所有干员都有
                log_message(f"{file_name} 缺少干员：{result} 不下载", logging.INFO, False)
                return False
            else:  # 仅下载缺少干员不超过1个
                log_message(f"{file_name} 缺少干员：{result}", logging.INFO, False)
                content = json.loads(_member["content"])
                content['doc']['details'] = f"作业更新日期: {_member['upload_time']}\n统计更新日期: {date}\n好评率：{_percent}%  浏览量：{_member['views']}\n来源：{_member['uploader']}  ID：{_member['id']}\n\n缺少干员(组):  {result}\n\n" + content['doc']['details']
    else:  # 未启用完备度检测
        content['doc']['details'] = f"作业更新日期: {_member['upload_time']}\n统计更新日期: {date}\n好评率：{_percent}%  浏览量：{_member['views']}\n来源：{_member['uploader']}  ID：{_member['id']}\n\n" + content['doc']['details']
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
    write_to_file(file_path, content)
    return True


def process_level(level, st, key, activity):
    """
    进行一次搜索并处理关卡
    :param level: 关卡数据
    :param st: 用户download设置
    :param key: 关卡类型，如活动关卡
    :param activity: 活动中文名，如生路
    :return: 无返回值
    """
    keyword = level['stage_id']
    name = level['cat_three']
    if any(substring in keyword for substring in ['#f#', 'easy']):
        return
    data = search(keyword, st["order_by"])  # 搜索
    total = data["data"]["total"]
    log_message(f"搜索 {keyword} 共获得 {total} 个数据")
    amount = 0
    for member in data["data"]["data"]:
        point = calculate_percent(member)
        if member["views"] >= st["view"] and point >= st["point"] and amount < st["amount"]:
            if st["only_uploader"] == [] or member["uploader"] in st["only_uploader"]:
                if process_and_save_content(name, member, st, key, activity, point):
                    amount += 1
            if amount >= st["amount"]:
                break
        elif amount >= st["amount"]:
            break


def less_search(stage_dict, _setting, search_key, activity, keyword):  # 搜索并下载
    """
    仅搜索一次并下载
    :param stage_dict: 当前活动的关卡字典
    :param _setting: 用户设置
    :param search_key: 关卡类型，如活动关卡
    :param activity: 活动中文名，如生路
    :param keyword: 搜索词，一般为活动ID，如act34side
    :return: 无返回值
    """
    st = _setting["download"]["0"]
    os.makedirs(os.path.join(st["path"], search_key, activity), exist_ok=True)
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


def int_input(prompt: str, default: int, min_value=None, max_value=None, allow_return=False):
    """
    支持默认值输入整数
    :param prompt: 问题
    :param default: 默认值
    :param min_value: 最小值
    :param max_value: 最大值
    :param allow_return: 是否允许b返回menu
    :return: 输入的整数
    """
    try:
        log_message(f"Function 函数: int_input({prompt}, {default}, {min_value}, {max_value})", logging.DEBUG, False)
        value = input(prompt).strip()
        log_message(f"Input 输入: {value}", logging.DEBUG, False)
        if allow_return and "b" in value.lower():
            return menu()
        value = int(value) if value else default
        if min_value is not None and value < min_value:
            value = default
        if max_value is not None and value > max_value:
            value = default
        print(f"设定值：{value}")  # 打印设定值
        return value
    except ValueError:
        print(f"输入无效，设置为默认值：{default}")
        return default


def bool_input(question):
    """
    询问问题，返回布尔值
    :param question: 问题
    :return: True or False
    """
    user_input = input(question + " (yes/no, 为空no): ").lower()
    return user_input in ["yes", "y", "true", "t", "1", "是", "对", "真", "要"]


def configure_download_settings():
    """
    设置下载参数
    :return: 下载参数
    """
    log_message("Page: SETTING 设置", logging.INFO, False)
    print("1. 标题.json\n2. 标题 - 作者.json\n3. 关卡代号-干员1+干员2.json")
    title = int_input("选择文件名格式（默认为1）：", 1, 1, 3)
    print("1. 替换原来的文件\n2. 保存到新文件并加上序号如 (1)\n3. 跳过，不保存")
    save = int_input("设置文件名冲突时的处理方式（默认为2）：", 2, 1, 3)
    path = input("设置保存文件夹（为空默认当前目录\\download）：").strip()
    path = path if path and os.path.isdir(path) else os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                                  "download")
    print(f"保存文件夹：{path}")
    order_by = int_input("1. 热度\n2. 最新\n3. 浏览量\n设置排序方式（默认为3. 浏览量）：", 3, 1, 3)
    point = int_input("设置好评率限制(0-100)（为空不限制）：", 0, 0, 100)
    view = int_input("设置浏览量限制（大于你设置的值）（为空不限制）：", 0)
    amount = int_input("设置下载数量(1-5)（为空全部下载）：", 99, 1, 5)
    completeness = bool_input("是否启用干员完备度检测？")
    if completeness:
        completeness_mode = int_input("1. 所有干员都有\n2. 缺少干员不超过1个\n设置检测条件（默认为1）：", 1, 1, 2)
        operator_num = int_input("设置干员配置序号（1-9默认为1）：", 1, 1, 9)
    else:
        completeness_mode = 1
        operator_num = 1
    operator = input("设置禁用干员（多个用空格分隔）（为空不禁用）：").split()
    print(f"设定值：{operator}")
    uploader = input("设置只看作业站作者（多个用空格分隔）（为空不设置）：").split()
    print(f"设定值：{uploader}")
    log_message(f"Setting 设置: {title}, {save}, {path}, {order_by}, {point}, {view}, {amount}, {completeness}, {completeness_mode}, {operator}, {uploader}", logging.DEBUG, False)
    return {
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
        'operator_num': operator_num,
        'ban_operator': operator,
        'only_uploader': uploader
    }


def replace_dir_char(text):
    """
    替换文件名中的非法字符
    :param text: 要替换的文本
    :return: 替换后的文本
    """
    for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
        text = text.replace(char, '')
    return text


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


def generate_filename(content, title, uploader, keyword):
    """
    生成文件名
    :param content: 作业数据
    :param title: 文件名格式
    :param uploader: 作业作者
    :param keyword: 关卡代号
    :return: 文件名
    """
    if content.get("difficulty", 0) == 1:  # 普通
        file_name = "(仅普通)"
    else:  # 其他
        file_name = ""
    if title == 1:  # 标题
        file_name += content["doc"]["title"]
    elif title == 2:  # 标题 - 作者
        file_name += content["doc"]["title"] + " - " + uploader
    elif title == 3:  # 关卡代号-干员1+干员2
        file_name += generate_filename_mode3(keyword, content)
    else:  # 错误
        t = time.time()
        log_message(f'File name format error 文件名格式错误, {t}, {content}, {title}, {uploader}, {keyword}', logging.ERROR)
        file_name = f"ERROR{t}"
    return replace_dir_char(file_name)


def mode1():
    """
    单次搜索
    :return: 无返回值
    """
    log_message("Single search 单次搜索", logging.INFO, False)
    os.system("cls")
    print("已进入单次搜索并下载模式，（输入back返回）")
    keyword = input("请输入关卡代号：").strip()
    if "back" in keyword.lower():
        return menu()
    _setting = configuration()
    st = _setting["download"]
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
                if process_and_save_content(keyword, member, st, keyword, "单次下载", point):
                    amount = amount + 1
            if amount >= st["amount"]:
                break
        elif amount >= st["amount"]:
            break
    last = time.time()
    input(f"搜索完毕，共耗时 {round(last - now, 2)} s.\n按回车键返回")
    return menu()


def input_level():
    """
    选择关卡类型
    :return: 无返回值
    """
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
        else:
            stage_dict = build_dict(all_dict[key][activity], "stage_id")
            log_message(f"stage_dict: {stage_dict}", logging.DEBUG, False)
        write_to_file("log/stage_dict_temp.json", stage_dict)
        st = configuration()
        now = time.time()
        if activity == "全部":  # 搜索全部
            less_search(stage_dict, st, key, "全部", key)
        elif key == "活动关卡":  # 搜索活动关卡使用extract_activity_from_stage_id
            less_search(stage_dict, st, key, activity, extract_activity_from_stage_id(all_dict[key][activity][0]['stage_id']))
        elif key == "主题曲":  # 搜索主题曲使用extract_integer_from_stage_id
            less_search(stage_dict, st, key, activity, extract_integer_from_stage_id(all_dict[key][activity][0]['stage_id']) + "-")
        elif key == "剿灭作战" or key == "资源收集":  # 搜索剿灭作战或资源收集直接搜索activity
            less_search(stage_dict, st, key, activity, activity)
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


def extract_activity_from_stage_id(stage_id: str):
    """
    从 stage_id 中提取activity_id，如act34side
    :param stage_id: 关卡ID
    :return: [activity_id]_
    """
    match = re.search(r'(.+?)_', stage_id)
    if match:
        log_message(f"Extract activity from stage_id: {match.group(1)}", logging.DEBUG, False)
        return match.group(1) + '_'
    return None


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
            return input_level()

        else:
            print("未找到匹配项，请重新选择")
            # 如果没有匹配项，重置匹配列表为所有keys并继续循环
            matching_keys = list(_activity_dict[key_one].keys())
            matching_keys.append("全部")
            continue


def mode2():
    """
    批量搜索
    :return: 无返回值
    """
    log_message("Batch download 批量下载", logging.DEBUG, False)
    os.system("cls")
    print("已进入批量搜索并下载模式，（输入back返回）")
    return input_level()


def ask3(key: str):
    """
    选择配置
    :param key: 配置类型
    :return: 配置序号
    """
    for n in range(1, 10):
        print(f"{n}: {'已存在' if key in setting and str(n) in setting[key] and len(setting[key][str(n)]) > 0 else '无'}")
    return str(int_input("b: 返回\n请选择配置序号：", 1, 1, 9, True))


def download_set():
    """
    设置下载设置或干员设置
    :return: 无返回值
    """
    global setting
    log_message("Page: SETTING 设置", logging.DEBUG, False)
    load_settings()
    return_info = ""
    print("1. 下载设置")
    print("2. 干员设置")
    choose1 = input("请选择操作：")
    if choose1 == "1":
        choose2 = input("下载设置：\n1. 设置\n2. 查看设置\n请选择操作：")
        if choose2 == "1":
            choose3 = ask3('download')
            setting["download"][choose3] = configure_download_settings()
            save_setting(setting)
        elif choose2 == "2" and "download" in setting:
            choose3 = ask3('operator')
            if choose3 in setting["download"]:
                return_info = json.dumps(setting["download"][choose3], ensure_ascii=False, indent=4)
            else:
                return_info = "选择的配置不存在"
    elif choose1 == "2":
        choose2 = input("干员设置：\n1. 设置\n2. 查看设置\n请选择操作：")
        if choose2 == "1":
            choose3 = ask3('operator')
            input(f"正在设置配置{choose3},请使用MAA干员识别工具并复制到剪贴板\n按回车键继续\n")
            os.makedirs(os.path.dirname(SETTING_PATH), exist_ok=True)
            clipboard_content = pyperclip.paste()
            if is_valid_json(clipboard_content):
                if "operator" not in setting:
                    setting["operator"] = {}
                setting["operator"][choose3] = json.loads(clipboard_content)
                save_setting(setting)
                return_info = menu(f"干员设置已保存,共有 {len(setting['operator'][choose3])} 个干员")
            else:
                return_info = menu("无效的JSON数据,请重新设置")
        elif choose2 == "2" and "operator" in setting:
            choose3 = ask3('operator')
            return_info = menu(f"配置 {choose3} 当前共有 {len(setting['operator'][choose3])} 个干员")
    return menu(return_info)


def menu(info=""):
    """
    菜单
    :param info: 要显示的信息
    :return: 对应操作
    """
    log_message("Page: MENU 菜单", logging.DEBUG, False)
    os.system("cls")
    if info != "":
        log_message(f"info: {info}", logging.INFO, False)
        print(info)
    print("=" * 60)
    print("1. 单次搜索并下载")
    print("2. 批量搜索并下载")
    print("3. 设置")
    print("e. 退出")
    choose = input("请选择操作：")
    if choose == "1":
        return mode1()
    elif choose == "2":
        return mode2()
    elif choose == "3":
        return download_set()
    elif "e" in choose.lower():
        return True


delete_log_file()
os.makedirs("log", exist_ok=True)
log_message("Program start 程序启动", logging.INFO)
if use_local_level:
    with open("cache/level_data.json", 'r', encoding='utf-8') as f:
        level_data = json.load(f)['data']
    log_message("Successfully loaded local level data. 成功加载本地关卡数据")
else:
    level_data = get_level_data()
    log_message("Successfully retrieved online level data. 成功获取在线关卡数据")
all_dict = build_complex_dict(level_data)
cat_three_dict = build_dict(level_data, "cat_three")
# write_to_file("log/cat_three_dict_temp.json", cat_three_dict)
# write_to_file("log/all_dict_temp.json", all_dict)
while True:
    if menu():
        break
log_message("Program end 程序结束", logging.INFO)
