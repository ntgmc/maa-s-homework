import requests
import json
import time
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import pyperclip

SETTING_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings", "settings.json")
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log", "app.log")
setting = {}
setting_version = "20240710"
date = time.strftime('%Y-%m-%d', time.localtime())
use_local_level = False


def is_valid_json(test_string):
    try:
        json.loads(test_string)
        return True
    except json.JSONDecodeError:
        return False


def save_setting(data):
    os.makedirs(os.path.dirname(SETTING_PATH), exist_ok=True)
    with open(SETTING_PATH, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    log_message(f"Setting saved successfully 设置保存成功", logging.INFO, False)
    return True


def load_data(path) -> any:
    if os.path.exists(path):
        log_message(f"Load data from {path}", logging.INFO, False)
        with open(path, 'r', encoding='utf-8') as file:
            return json.load(file)
    return False


def write_to_file(file_path, content):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(content, file, ensure_ascii=False, indent=4)
        log_message(f"write_to_file 写出文件: {file_path}", console_output=False)


def delete_log_file():
    if os.path.exists(log_path):
        os.remove(log_path)


def log_message(message, level=logging.INFO, console_output=True):
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
    response = requests.get('https://prts.maa.plus/arknights/level')
    write_to_file("log/level_data_temp.json", response.json())
    log_message(f"Successfully obtained level data 成功获取关卡数据", console_output=False)
    return response.json()['data'] if response.ok else []


def build_complex_dict(data):
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


def build_dict(data, key: str, _dict=None):  # key为生成的字典的键
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
    data_dict = {}
    for member in data['data']['data']:
        stage = json.loads(member['content'])['stage_name']
        if any(substring in stage for substring in ['#f#', 'easy']):
            continue
        log_message("Build data dict: " + stage + "<<" + level_dict[stage][0]['cat_three'], logging.DEBUG, False)
        key = stage + "<<" + level_dict[stage][0]['cat_three']
        if key not in data_dict:
            data_dict[key] = []
        data_dict[key].append(member)
    return data_dict


def build_operator_dict(data: dict, num: int):  # num为配置序号
    op_dict = {}
    item = data[str(num)]
    for member in item:
        key = member['name']
        if key in op_dict:
            op_dict[key].append(member)
        else:
            op_dict[key] = [member]
    return op_dict


def ban_operator(a, b):  # 禁用干员检测
    set1 = set(a)
    set2 = set(b)
    r1 = set1 - set2
    r2 = set1 - r1
    print(r1, r2)
    return len(r2) > 0


def completeness_check(list1, opers, groups):
    def check_group():
        for t in groups_set:
            if not any(member in list1_set for member in t):
                result.append(t)
        if len(result) == 0:
            # print("完备")
            return True
        elif len(result) == 1:
            # print("缺少一个", result[0])
            return result[0]
        else:
            # print("缺少多个", result)
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
    else:
        return False


def load_settings():  # 自动加载设置到全局变量
    global setting
    if os.path.exists(SETTING_PATH):
        with open(SETTING_PATH, 'r', encoding='utf-8') as file:
            setting = json.load(file)
        if "download" in setting and setting["download"].get("version", "") == setting_version:
            log_message(f"Settings loaded successfully 成功加载设置", console_output=False)
            return True
        else:
            log_message(f"Version mismatch set 设置版本不匹配", logging.ERROR, False)
    return False


def calculate_percent(item):
    like, dislike = item.get('like', 0), item.get('dislike', 0)
    return round(like / (like + dislike) * 100, 2) if like + dislike > 0 else 0


def configuration():
    print("1. 默认设置\n2. 用户设置\n3. 自定义设置（单次）")
    _mode = input("请选择配置：")
    log_message(f"Configuration 配置: {_mode}", logging.DEBUG, False)
    if _mode == "1":
        return {"download": {
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
        }}
    elif _mode == "2":
        if not load_settings():
            return menu("未找到用户设置或用户设置已过期，请设置")
        return setting
    elif _mode == "3":
        st = configure_download_settings()
        return {"download": st}
    elif "back" in _mode.lower():
        return menu()
    else:
        print("未知选项，请重新选择，返回请输入back")
        return configuration()


def search(keyword, search_mode):  # 返回json
    order_by = {1: "hot", 2: "id", 3: "views"}.get(search_mode, "views")
    url = f"https://prts.maa.plus/copilot/query?desc=true&limit=99&page=1&order_by={order_by}&level_keyword={keyword}"
    headers = {
        "Origin": "https://prts.plus",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
    }
    try:
        response = requests.get(url, headers=headers)
        return response.json()
    except requests.exceptions.SSLError:
        log_message("SSL certificate verification failed SSL证书验证失败", logging.ERROR)
        print("=" * 60)
        input("!!!SSL证书验证失败，请关闭系统代理!!!\n")
        return menu()


def process_and_save_content(keyword, _member, _setting, key, activity, _percent=0):
    st = _setting["download"]
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
        result = completeness_check(list(_setting["operator_dict"].keys()), content.get('opers', []),
                                    content.get('groups', []))
        if result is True:  # 完备
            content['doc'][
                'details'] = f"作业更新日期: {_member['upload_time']}\n统计更新日期: {date}\n好评率：{_percent}%  浏览量：{_member['views']}\n来源：{_member['uploader']}  ID：{_member['id']}\n\n" + \
                             content['doc']['details']
        elif result is False:  # 缺少多个
            log_message(f"{file_name} 完备度检测不通过", logging.INFO, False)
            return False
        else:  # 缺少一个
            if st['completeness_mode'] == 1:  # 所有干员都有
                log_message(f"{file_name} 缺少干员：{result} 不下载", logging.INFO, False)
                return False
            else:  # 缺少干员不超过1个
                log_message(f"{file_name} 缺少干员：{result}", logging.INFO, False)
                content = json.loads(_member["content"])
                content['doc'][
                    'details'] = f"作业更新日期: {_member['upload_time']}\n统计更新日期: {date}\n好评率：{_percent}%  浏览量：{_member['views']}\n来源：{_member['uploader']}  ID：{_member['id']}\n\n缺少干员(组):  {result}\n\n" + \
                                 content['doc']['details']
    else:
        content['doc'][
            'details'] = f"作业更新日期: {_member['upload_time']}\n统计更新日期: {date}\n好评率：{_percent}%  浏览量：{_member['views']}\n来源：{_member['uploader']}  ID：{_member['id']}\n\n" + \
                         content['doc']['details']
    file_path = os.path.join(path, f"{file_name}.json")
    if st["save"] == 1:
        if os.path.exists(file_path):
            os.remove(file_path)
    elif st["save"] == 2:
        _ = 1
        while os.path.exists(file_path):
            file_path = os.path.join(path, f"{file_name} ({_}).json")
            _ = _ + 1
    elif st["save"] == 3:
        if os.path.exists(file_path):
            log_message(f"跳过文件：{file_path}", logging.INFO)
            return False
    write_to_file(file_path, content)
    return True


def process_level(level, st, key, activity):
    keyword = level['stage_id']
    name = level['cat_three']
    if any(substring in keyword for substring in ['#f#', 'easy']):
        return
    data = search(keyword, st["order_by"])
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


def searches(activity_list, mode=0, keyword="", activity=""):
    _setting = configuration()
    st = _setting["download"]
    os.makedirs(st["path"], exist_ok=True)
    log_message(f"保存目录：{st['path']}")
    now = time.time()

    if mode == 0:
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(process_level, level, st, keyword, activity) for level in activity_list if
                       not any(substring in level['stage_id'] for substring in ['#f#', 'easy'])]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    log_message(f"{e}", logging.ERROR)
    else:  # 下载全部
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for sub, sub_list in activity_list.items():
                for level in sub_list:
                    if any(substring in level['stage_id'] for substring in ['#f#', 'easy']):
                        continue
                    futures.append(executor.submit(process_level, level, st, keyword, activity))
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        log_message(f"{e}", logging.ERROR)

    last = time.time()
    log_message(f"搜索完毕，共耗时 {round(last - now, 2)} s.", logging.INFO, False)
    input(f"搜索完毕，共耗时 {round(last - now, 2)} s.\n")
    return menu()


def less_search(stage_dict, _setting, search_key, activity, keyword):
    st = _setting["download"]
    os.makedirs(os.path.join(st["path"], search_key, activity), exist_ok=True)
    data = search(keyword, st["order_by"])
    data_dict = build_data_dict(stage_dict, data)
    _setting["operator_dict"] = build_operator_dict(_setting["operator"], st["operator_num"])
    for key, value in data_dict.items():
        key1, key2 = key.split("<<")
        #  key1为stage_id，key2为name
        total = len(value)
        log_message(f"搜索 {key1} {key2} 共获得 {total} 个数据")
        amount = 0
        for member in value:
            if any(substring in member['content'] for substring in ['#f#', 'easy']):
                continue
            point = calculate_percent(member)
            if member["views"] >= st["view"] and point >= st["point"] and amount < st["amount"]:
                if st["only_uploader"] == [] or member["uploader"] in st["only_uploader"]:
                    if process_and_save_content(key2, member, _setting, search_key, activity, point):
                        amount = amount + 1
                if amount >= st["amount"]:
                    break
            elif amount >= st["amount"]:
                break


def int_input(prompt, default, min_value=None, max_value=None, allow_return=False):
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
    user_input = input(question + " (yes/no, 为空no): ").lower()
    return user_input in ["yes", "y", "true", "t", "1", "是", "对", "真", "要"]


def configure_download_settings():
    log_message("Page: SETTING 设置", logging.INFO, False)
    print("1. 标题.json\n2. 标题 - 作者.json\n3. 关卡代号-干员1+干员2.json")
    title = int_input("选择文件名格式（默认为1）：", 1, 1, 3)
    print("1. 替换原来的文件\n2. 保存到新文件并加上序号如 (1)\n3. 跳过，不保存")
    save = int_input("设置文件名冲突时的处理方式（默认为2）：", 2, 1, 3)
    path = input("设置保存文件夹（为空默认当前目录\\download）：").replace(" ", "")
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
    # train_degree = bool_input("是否启用练度判断？")
    # if train_degree:
    #     train_degree_mode = int_input("1. 仅下载练度满足条件的作业\n2. 下载时/完后提示练度不满足的作业\n3. 在作业文件Detail中提示练度不满足的干员\n设置处理方式（默认为1）：", 1, 1, 3)
    # else:
    #     train_degree_mode = 1
    operator = input("设置禁用干员（多个用空格分隔）（为空不禁用）：").split()
    print(f"设定值：{operator}")
    uploader = input("设置只看作业站作者（多个用空格分隔）（为空不设置）：").split()
    print(f"设定值：{uploader}")
    log_message(
        f"Setting 设置: {title}, {save}, {path}, {order_by}, {point}, {view}, {amount}, {completeness}, {completeness_mode}, {operator}, {uploader}",
        logging.DEBUG, False)
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
    for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
        text = text.replace(char, '')
    return text


def generate_filename_mode3(stage_name, data):
    opers = data.get('opers', [])
    groups = data.get('groups', [])
    names_parts = ['+'.join(oper.get('name', '') for oper in opers),
                   '+'.join(group.get('name', '') for group in groups)]
    names = '+'.join(part for part in names_parts if part)  # 只连接非空的部分
    names = replace_dir_char(names)
    if len(names) > 100:
        log_message(f"File name too long 文件名过长: {names}, {stage_name}", logging.WARNING)
        names = "文件名过长不予显示"
    return f'{stage_name}_{names}'


def generate_filename(content, title, uploader, keyword):
    if content.get("difficulty", 0) == 1:
        file_name = "(仅普通)"
    else:
        file_name = ""
    if title == 1:
        file_name += content["doc"]["title"]
    elif title == 2:
        file_name += content["doc"]["title"] + " - " + uploader
    elif title == 3:
        file_name += generate_filename_mode3(keyword, content)
    else:
        t = time.time()
        log_message(f'File name format error 文件名格式错误, {t}, {content}, {title}, {uploader}, {keyword}',
                    logging.ERROR)
        file_name = f"ERROR{t}"
    return file_name


def mode1():
    log_message("Single search 单次搜索", logging.INFO, False)
    os.system("cls")
    print("已进入单次搜索并下载模式，（输入back返回）")
    keyword = input("请输入关卡代号：").replace(" ", "")
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
            if st["uploader"] == [] or member["uploader"] in st["uploader"]:
                if process_and_save_content(keyword, member, st, keyword, "单次下载", point):
                    amount = amount + 1
            if amount >= st["amount"]:
                break
        elif amount >= st["amount"]:
            break
    last = time.time()
    input(f"搜索完毕，共耗时 {round(last - now, 2)} s.\n")
    return menu()


def input_level():
    log_message("Select type 选择类型", logging.DEBUG, False)
    keys = ["活动关卡", "主题曲", "剿灭作战", "资源收集"]
    for i, key in enumerate(keys):
        print(f"{i + 1}. {key}")
    print("b. 返回")
    choose = input("请选择要搜索的关卡类型：").replace(" ", "")
    if choose.isdigit() and 1 <= int(choose) <= len(keys):
        key = keys[int(choose) - 1]
        activity = select_from_list(all_dict, key)
        if activity == "全部":
            stage_dict = {}
            for sub_key, sub_dict in all_dict[key].items():
                stage_dict = build_dict(sub_dict, "stage_id", stage_dict)
        else:
            stage_dict = build_dict(all_dict[key][activity], "stage_id")
            log_message(f"stage_dict: {stage_dict}", logging.DEBUG, False)
        write_to_file("log/stage_dict_temp.json", stage_dict)
        if key == "活动关卡":
            if activity == "全部":
                st = configuration()
                now = time.time()
                with ThreadPoolExecutor(max_workers=10) as executor:
                    futures = [executor.submit(less_search, stage_dict, st, key, activity,
                                               extract_activity_from_stage_id(all_dict[key][activity][0]['stage_id']))
                               for activity in all_dict[key]
                               if activity != "全部" and activity != ""]
                    for future in as_completed(futures):
                        try:
                            future.result()
                        except Exception as e:
                            log_message(f"{e}", logging.ERROR)
                log_message(f"搜索{key}-{activity}完毕，共耗时 {round(time.time() - now, 2)} s.", logging.INFO, False)
                input(f"搜索完毕，共耗时 {round(time.time() - now, 2)} s.\n")
                return menu()
            else:
                st = configuration()
                now = time.time()
                less_search(stage_dict, st, key, activity,
                            extract_activity_from_stage_id(all_dict[key][activity][0]['stage_id']))
                log_message(f"搜索{key}-{activity}完毕，共耗时 {round(time.time() - now, 2)} s.", logging.INFO, False)
                input(f"搜索完毕，共耗时 {round(time.time() - now, 2)} s.\n")
                return menu()
        elif key == "剿灭作战" and activity == "全部":
            st = configuration()
            now = time.time()
            less_search(stage_dict, st, "剿灭作战", activity, "camp_")
            log_message(f"搜索{key}-{activity}完毕，共耗时 {round(time.time() - now, 2)} s.", logging.INFO, False)
            input(f"搜索完毕，共耗时 {round(time.time() - now, 2)} s.\n")
            return menu()
        if activity == "全部":
            return searches(all_dict[key], mode=1, keyword=key, activity=activity)
        else:
            return searches(all_dict[key][activity], keyword=key, activity=activity)
    elif "b" in choose.lower():
        return menu()
    else:
        print("未知选项，请重新选择")
        return input_level()


def extract_integer_from_stage_id(stage_id):
    # 从 stage_id 中提取数字
    match = re.search(r'_(\d+)-', stage_id)
    if match:
        return int(match.group(1))
    return 0


def extract_activity_from_stage_id(stage_id):
    # 从 stage_id 中提取数字
    match = re.search(r'(.+?)_', stage_id)
    if match:
        return match.group(1) + '_'
    return None


def select_from_list(_activity_dict, key_one):  # 返回二级中文名
    log_message("选择关卡", logging.INFO, False)
    if key_one == "主题曲":
        stage_dict = {}
        for stage_name, item in _activity_dict[key_one].items():
            key = extract_integer_from_stage_id(item[0]['stage_id'])
            stage_dict[key] = stage_name
        matching_keys = [value for key, value in sorted(stage_dict.items())]
    else:
        matching_keys = list(_activity_dict[key_one].keys())  # 初始匹配所有keys
    matching_keys.append("全部")
    while True:
        print("请选择关卡：")
        for i, key in enumerate(matching_keys):
            print(f"{i}. {key}")
        user_input = input("请输入关卡名称或序号：").replace(" ", "")

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
            matching_keys = list(_activity_dict.keys())
            continue


def mode2():
    log_message("Batch download 批量下载", logging.DEBUG, False)
    os.system("cls")
    print("已进入批量搜索并下载模式，（输入back返回）")
    return input_level()


def download_set():
    global setting

    def ask3():
        for n in range(1, 10):
            print(
                f"{n}: {'已存在' if 'operator' in setting and str(n) in setting['operator'] and len(setting['operator'][str(n)]) > 0 else '无'}")
        return str(int_input("b: 返回\n请选择配置序号：", 1, 1, 9, True))
    log_message("Page: SETTING 设置", logging.DEBUG, False)
    load_settings()
    return_info = ""
    print("1. 下载设置")
    print("2. 干员设置")
    choose1 = input("请选择操作：")
    if choose1 == "1":
        choose2 = input("下载设置：\n1. 设置\n2. 查看设置\n请选择操作：")
        if choose2 == "1":
            setting["download"] = configure_download_settings()
            save_setting(setting)
        elif choose2 == "2" and setting.get("download"):
            return_info = json.dumps(setting["download"], ensure_ascii=False, indent=4)
    elif choose1 == "2":
        choose2 = input("干员设置：\n1. 设置\n2. 查看设置\n请选择操作：")
        if choose2 == "1":
            choose3 = ask3()
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
            choose3 = ask3()
            return_info = menu(f"配置 {choose3} 当前共有 {len(setting['operator'][choose3])} 个干员")
    return menu(return_info)


def menu(info=""):
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
        all_dict = build_complex_dict(json.load(f)['data'])
    log_message("Successfully loaded local level data. 成功加载本地关卡数据")
else:
    all_dict = build_complex_dict(get_level_data())
    log_message("Successfully retrieved online level data. 成功获取在线关卡数据")
while True:
    if menu():
        break
log_message("Program end 程序结束", logging.INFO)
