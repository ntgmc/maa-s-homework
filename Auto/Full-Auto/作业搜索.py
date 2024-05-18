import requests
import json
import time
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

SETTING_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings", "settings.json")
setting = {}
date = datetime.now().strftime('%Y-%m-%d')


def save_data(data):
    user_data_dir = os.path.dirname(SETTING_PATH)
    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir)
    with open(SETTING_PATH, 'w') as file:
        json.dump(data, file)
    return True


def write_to_file(file_path, content):
    with open(file_path.replace('/', ''), 'w', encoding='utf-8') as file:
        json.dump(content, file, ensure_ascii=False, indent=4)


def get_level_data():
    url = 'https://prts.maa.plus/arknights/level'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()['data']
    else:
        return []


def build_dict(data, key: str):  # key为生成的字典的键
    _dict = {}
    for member in data:
        _key = member[key]
        if _key in _dict:
            _dict[_key].append(member)
        else:
            _dict[_key] = [member]
    return _dict


def build_activity_dict(data):
    _dict = {}
    for member in data:
        if member['cat_one'] != '活动关卡':  # 只处理活动关卡
            continue
        _key = member['cat_two']
        if _key in _dict:
            _dict[_key].append(member)
        else:
            _dict[_key] = [member]
    return _dict


def load_settings():
    global setting
    if os.path.exists(SETTING_PATH):
        with open(SETTING_PATH, 'r') as file:
            setting = json.load(file)
        return True
    return False


def calculate_percent(item):
    like = item.get('like', 0)
    dislike = item.get('dislike', 0)
    total = like + dislike
    if total == 0:
        return 0
    else:
        return round(like / total * 100, 2)


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


def search(keyword, search_mode):
    if search_mode == 1:
        order_by = "hot"
    elif search_mode == 2:
        order_by = "id"
    elif search_mode == 3:
        order_by = "views"
    else:
        order_by = "hot"
    url = f"https://prts.maa.plus/copilot/query?desc=true&limit=50&page=1&order_by={order_by}&level_keyword={keyword}"
    headers = {
        "Origin": "https://prts.plus",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
    }
    try:
        response = requests.get(url, headers=headers)
        return response.text
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
    data = json.loads(search(keyword, st["order_by"]))
    total = data["data"]["total"]
    print(f"搜索 {keyword} 共获得 {total} 个数据")
    amount = 0
    for member in data["data"]["data"]:
        if member["like"] + member["dislike"] != 0:
            point = calculate_percent(member)
        else:
            point = 0
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
    if not os.path.exists(st['path']):
        os.makedirs(st['path'])
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
    order_by = get_input("设置排序方式（为空默认为3）：", 3, 1, 3)
    point = get_input("设置好评率限制(0-100)（为空不限制）：", 0, 0, 100)
    view = get_input("设置浏览量限制（大于你设置的值）（为空不限制）：", 0)
    amount = get_input("设置下载数量(1-5)（为空默认为1）：", 1, 1, 5)
    operator = input("设置禁用干员（空格分隔）（为空不限制）：").split()
    print(f"设定值：{operator}")
    uploader = input("设置只看作者（空格分隔）（为空不限制）：").split()
    print(f"设定值：{uploader}")
    input("按下Enter返回\n")
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


def replace_special_char(text):
    return text.replace('/', '').replace('\\', '')


def generate_filename_mode3(stage_name, data):
    opers = data.get('opers', [])
    groups = data.get('groups', [])
    names_parts = ['+'.join(oper.get('name', '') for oper in opers),
                   '+'.join(group.get('name', '') for group in groups)]
    names = '+'.join(part for part in names_parts if part)  # 只连接非空的部分
    names = replace_special_char(names)
    if len(names) > 220:
        names = "文件名过长不予显示"
    return f'{stage_name}_{names}.json'


def generate_filename(content, title, uploader, keyword):
    if title == 1:
        file_name = content["doc"]["title"]
    elif title == 2:
        file_name = content["doc"]["title"] + " - " + uploader
    elif title == 3:
        file_name = generate_filename_mode3(keyword, content)
    else:
        print('文件名格式错误')
        file_name = None
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
    if not os.path.exists(st["path"]):
        os.makedirs(st["path"])
    data = json.loads(search(keyword, st["order_by"]))
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
    print("2. 活动剿灭")
    print("3. 活动资源")
    print("4. 主线关卡")
    print("5. 剿灭")
    print("6. 资源关卡")
    print("7. 全部")
    choose = input("请选择要搜索的关卡类型：").replace(" ", "")
    if choose.isdigit() and 1 <= int(choose) <= 7:
        return int(choose)
    else:
        print("未知选项，请重新选择")
        return input_level()


def input_activity(_activity_dict):  # 返回活动关卡中文名
    matching_keys = list(_activity_dict.keys())  # 初始匹配所有keys
    while True:
        print("请选择活动关卡：")
        for i, key in enumerate(matching_keys):
            print(f"{i + 1}. {key}")
        user_input = input("请输入活动关卡名称或序号：").replace(" ", "")

        # 如果用户输入是数字且在范围内，直接返回对应的活动关卡
        if user_input.isdigit() and 1 <= int(user_input) <= len(matching_keys):
            return matching_keys[int(user_input) - 1]

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

        elif "back" in user_input.lower():
            return menu()

        else:
            print("未找到匹配项，请重新选择")
            # 如果没有匹配项，重置匹配列表为所有keys并继续循环
            matching_keys = list(_activity_dict.keys())
            continue


def mode2():
    os.system("cls")
    print("已进入批量搜索并下载模式，（输入back返回）")
    activity = input_activity(activity_dict)
    searches(activity_dict[activity])
    return menu()


def download_set():
    global setting
    load_settings()
    setting["download"] = configure_download_settings()
    save_data(setting)
    return menu()


def input_level_range(note, default):
    try:
        value = input(f"输入{note}关最大关卡（默认{default}）：").strip()
        value = int(value) if value else default
        print(f"设定值：{value}")
        return value
    except ValueError:
        print(f"输入无效，设置为默认值：{default}")
        return default


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


activity_dict = build_activity_dict(get_level_data())
menu_result = False
while not menu_result:
    menu_result = menu()
