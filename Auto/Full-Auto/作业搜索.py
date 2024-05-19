import requests
import json
import time
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

SETTING_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings", "settings.json")
setting = {}
date = time.strftime('%Y-%m-%d', time.localtime())


def save_data(data):
    os.makedirs(os.path.dirname(SETTING_PATH), exist_ok=True)
    with open(SETTING_PATH, 'w') as file:
        json.dump(data, file)
    return True


def write_to_file(file_path, content):
    with open(file_path.replace('/', ''), 'w', encoding='utf-8') as file:
        json.dump(content, file, ensure_ascii=False, indent=4)


def get_level_data():
    response = requests.get('https://prts.maa.plus/arknights/level')
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


def load_settings():
    global setting
    if os.path.exists(SETTING_PATH):
        with open(SETTING_PATH, 'r') as file:
            setting = json.load(file)
        return True
    return False


def calculate_percent(item):
    like, dislike = item.get('like', 0), item.get('dislike', 0)
    return round(like / (like + dislike) * 100, 2) if like + dislike > 0 else 0


def configuration():
    print("1. 默认配置\n2. 用户配置\n3. 自定义模式（单次）")
    _mode = input("请选择配置：")
    if _mode == "1":
        return {
            'title': 1,
            'path': os.path.join(os.path.dirname(os.path.abspath(__file__)), "download"),
            'order_by': 3,
            'point': 0,
            'view': 0,
            'amount': 1,
            'operator': [],
            'uploader': []
        }
    elif _mode == "2":
        if not load_settings():
            print("未找到用户配置，请先设置")
            input()
            return menu()
        return setting["download"]
    elif _mode == "3":
        return configure_download_settings()
    else:
        print("未知选项，请重新选择，返回请输入back")
        return configuration()


def search(keyword, search_mode):  # 返回json
    order_by = {1: "hot", 2: "id", 3: "views"}.get(search_mode, "views")
    url = f"https://prts.maa.plus/copilot/query?desc=true&limit=50&page=1&order_by={order_by}&level_keyword={keyword}"
    headers = {
        "Origin": "https://prts.plus",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
    }
    try:
        response = requests.get(url, headers=headers)
        return response.json()
    except requests.exceptions.SSLError:
        print("=" * 60)
        input("!!!SSL证书验证失败，请关闭系统代理!!!\n")
        return menu()


def process_and_save_content(keyword, _member, st, _percent=0, _view=0, _uploader="", _id=""):
    content = json.loads(_member["content"])
    content['doc']['details'] = f"统计日期：{date}\n好评率：{_percent}%  浏览量：{_view}\n来源：{_uploader}  ID：{_id}\n" + content['doc']['details']
    names = [oper.get('name', '') for oper in content.get('opers', '')]
    opers_bool = False
    for opers in st["operator"]:
        if opers in names:
            opers_bool = True
            break
    if opers_bool:
        return False
    file_name = generate_filename(content, st["title"], _member["uploader"], keyword)
    file_path = os.path.join(st["path"], f"{file_name}.json")
    _ = 1
    while os.path.exists(file_path):
        file_path = os.path.join(st["path"], f"{file_name} ({_}).json")
        _ = _ + 1
    write_to_file(file_path, content)
    print(f"成功写出文件：{file_path}")
    return True


def process_level(level, st):
    keyword = level['stage_id']
    name = level['cat_three']
    if '#f#' in keyword:
        return
    data = search(keyword, st["order_by"])
    total = data["data"]["total"]
    print(f"搜索 {keyword} 共获得 {total} 个数据")
    amount = 0
    for member in data["data"]["data"]:
        point = calculate_percent(member)
        if member["views"] >= st["view"] and point >= st["point"] and amount < st["amount"]:
            if st["uploader"] == [] or member["uploader"] in st["uploader"]:
                if process_and_save_content(name, member, st, point, member["views"], member["uploader"], member["id"]):
                    amount += 1
            if amount >= st["amount"]:
                break
        elif amount >= st["amount"]:
            break


def searches(activity_list):
    st = configuration()
    print(f"保存目录：{st['path']}")
    os.makedirs(st['path'], exist_ok=True)
    now = time.time()

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_level, level, st) for level in activity_list]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Task generated an exception: {e}")

    last = time.time()
    input(f"搜索完毕，共耗时 {round(last - now, 2)} s.\n")
    return menu()


def get_input(prompt, default, min_value=None, max_value=None):
    try:
        value = input(prompt).strip()
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


def configure_download_settings():
    print("1. 标题.json")
    print("2. 标题 - 作者.json")
    print("3. 关卡代号-干员1+干员2.json")
    title = get_input("选择文件名格式（默认为1）：", 1, 1, 3)
    path = input("设置保存文件夹（为空默认当前目录\\download）：").replace(" ", "")
    path = path if path and os.path.isdir(path) else os.path.join(os.path.dirname(os.path.abspath(__file__)), "download")
    print(f"成功设置保存文件夹为：{path}")
    print("1. 热度")
    print("2. 最新")
    print("3. 浏览量")
    order_by = get_input("设置排序方式（默认为3. 浏览量）：", 3, 1, 3)
    point = get_input("设置好评率限制(0-100)（为空不限制）：", 0, 0, 100)
    view = get_input("设置浏览量限制（大于你设置的值）（为空不限制）：", 0)
    amount = get_input("设置下载数量(1-5)（为空默认为1）：", 1, 1, 10)
    operator = input("设置禁用干员（空格分隔）（为空不限制）：").split()
    print(f"设定值：{operator}")
    uploader = input("设置只看作业站作者（空格分隔）（为空不限制）：").split()
    print(f"设定值：{uploader}")
    return {
        'title': title,
        'path': path,
        'order_by': order_by,
        'point': point,
        'view': view,
        'amount': amount,
        'operator': operator,
        'uploader': uploader
    }


def replace_dir_char(text):
    return text.replace('/', '').replace('\\', '')


def generate_filename_mode3(stage_name, data):
    opers = data.get('opers', [])
    groups = data.get('groups', [])
    names_parts = ['+'.join(oper.get('name', '') for oper in opers),
                   '+'.join(group.get('name', '') for group in groups)]
    names = '+'.join(part for part in names_parts if part)  # 只连接非空的部分
    names = replace_dir_char(names)
    if len(names) > 220:
        names = "文件名过长不予显示"
    return f'{stage_name}_{names}'


def generate_filename(content, title, uploader, keyword):
    if title == 1:
        file_name = content["doc"]["title"]
    elif title == 2:
        file_name = content["doc"]["title"] + " - " + uploader
    elif title == 3:
        file_name = generate_filename_mode3(keyword, content)
    else:
        print('文件名格式错误')
        file_name = f"ERROR{time.time()}"
    return file_name


def mode1():
    os.system("cls")
    print("已进入单次搜索并下载模式，（输入back返回）")
    keyword = input("请输入关卡代号：").replace(" ", "")
    if keyword.lower() == "back":
        return menu()
    st = configuration()
    os.system("cls")
    now = time.time()
    print(f'保存目录：{st["path"]}')
    os.makedirs(st["path"], exist_ok=True)
    data = search(keyword, st["order_by"])
    total = data["data"]["total"]
    print(f"搜索 {keyword} 共获得 {total} 个数据")
    amount = 0
    for member in data["data"]["data"]:
        point = calculate_percent(member)
        if member["views"] >= st["view"] and point >= st["point"] and amount < st["amount"]:
            if st["uploader"] == [] or member["uploader"] in st["uploader"]:
                if process_and_save_content(keyword, member, st, point, member["views"], member["uploader"], member["id"]):
                    amount = amount + 1
            if amount >= st["amount"]:
                break
        elif amount >= st["amount"]:
            break
    last = time.time()
    input(f"搜索完毕，共耗时 {round(last - now, 2)} s.\n")
    return menu()


def input_level():
    print("1. 活动关卡")
    print("2. 主题曲")
    print("3. 剿灭作战")
    print("4. 资源收集")
    print("b. 返回")
    choose = input("请选择要搜索的关卡类型：").replace(" ", "")
    if choose.isdigit() and 1 <= int(choose) <= 5:
        key = ["活动关卡", "主题曲", "剿灭作战", "资源收集"][int(choose) - 1]
        activity = select_from_list(all_dict, key)
        return searches(all_dict[key][activity])
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


def select_from_list(_activity_dict, key_one):  # 返回二级中文名
    if key_one == "主题曲":
        stage_dict = {}
        for stage_name, item in _activity_dict[key_one].items():
            key = extract_integer_from_stage_id(item[0]['stage_id'])
            stage_dict[key] = stage_name
        matching_keys = [value for key, value in sorted(stage_dict.items())]
    else:
        matching_keys = list(_activity_dict[key_one].keys())  # 初始匹配所有keys
    while True:
        print("请选择关卡：")
        for i, key in enumerate(matching_keys):
            print(f"{i}. {key}")
        user_input = input("请输入关卡名称或序号：").replace(" ", "")

        # 如果用户输入是数字且在范围内，直接返回对应的活动关卡
        if user_input.isdigit() and 0 <= int(user_input) <= len(matching_keys):
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
    os.system("cls")
    print("已进入批量搜索并下载模式，（输入back返回）")
    return input_level()


def download_set():
    global setting
    load_settings()
    setting["download"] = configure_download_settings()
    save_data(setting)
    return menu()


def menu():
    os.system("cls")
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


all_dict = build_complex_dict(get_level_data())
menu_result = False
while not menu_result:
    menu_result = menu()
