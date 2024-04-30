import requests
import json
import time
import os

SETTING_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings", "settings.json")
setting = {}


def save_data(data):
    user_data_dir = os.path.dirname(SETTING_PATH)
    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir)
    with open(SETTING_PATH, 'w') as file:
        json.dump(data, file)
    return True


def write_to_file(file_path, content):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(content, file, ensure_ascii=False, indent=4)


def load_settings():
    global setting
    if os.path.exists(SETTING_PATH):
        with open(SETTING_PATH, 'r') as file:
            setting = json.load(file)
        return True
    return False


def configuration():
    print("1. 默认配置")
    print("2. 用户配置")
    print("3. 自定义模式（单次）")
    mode1 = input("请选择配置：")
    if mode1.lower() == "back":
        return menu()
    if mode1 == "1":
        st = {
            'stitle': "1",
            'path': os.path.join(os.path.dirname(os.path.abspath(__file__)), "download"),
            'order_by': 1,
            'spoint': 0,
            'sview': 0,
            'samount': 1,
            'soperater': [],
            'suploader': []
        }
    elif mode1 == "2":
        if not load_settings():
            print("未找到用户配置，请先设置")
            input()
            return menu()
        st = setting["download"]
    elif mode1 == "3":
        st = configure_download_settings()
    else:
        print("未知选项，请重新选择，返回请输入back")
        return configuration()
    return st


def search(keyword, searchmode):
    if searchmode == 1:
        order_by = "hot"
    elif searchmode == 2:
        order_by = "id"
    elif searchmode == 3:
        order_by = "views"
    url = f"https://prts.maa.plus/copilot/query?desc=true&limit=50&page=1&order_by={order_by}&level_keyword={keyword}"
    headers = {
        "Origin": "https://prts.plus",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
    }
    response = requests.get(url, headers=headers)
    return response.text


def searches(keyword_perfix, range_max, mode):
    def searches_(range_max, mode):
        def searches__(member):
            content = json.loads(member["content"])
            names = [oper["name"] for oper in content["opers"]]
            opers_bool = False
            for opers in soperater:
                if opers in names:
                    opers_bool = True
                    break
            if opers_bool:
                return False
            file_name = generate_filename(content, stitle, uploader, keyword)
            file_path = os.path.join(path, f"{file_name}.json")
            i = 1
            while os.path.exists(file_path):
                file_path = os.path.join(path, f"{file_name} ({i}).json")
                i = i + 1
            write_to_file(file_path, content)
            print(f"成功写出文件：{file_path}")
            return True

        if mode == 1:  # 普通关
            keyword_concatenate = f"-"
        elif mode == 2:  # EX
            keyword_concatenate = f"-EX-"
        elif mode == 3:  # S
            keyword_concatenate = f"-S-"
        elif mode == 4:  # TR
            keyword_concatenate = f"-TR-"
        elif mode == 5:  # MO
            keyword_concatenate = f"-MO-"
        elif mode == 6:  # 全部
            for i in range(5):
                if load_settings() and setting["range"] is not None:
                    range_max = setting["range"][f"{i + 1}_range"]
                else:
                    input("请先设置【批量设置】再使用下载【全部关】\n")
                    return menu()
                searches_(range_max, i + 1)
            return menu()
        print(f"保存目录：{path}")
        if not os.path.exists(path):
            os.makedirs(path)
        now = time.time()
        if range_max == 0:
            if setting["range"][f"{mode}_range"]:
                range_max = setting["range"][f"{mode}_range"]
        for i in range(range_max):
            keyword = f"{keyword_perfix}{keyword_concatenate}{i + 1}"
            data = json.loads(search(keyword, order_by))
            total = data["data"]["total"]
            print(f"搜索 {keyword} 共获得 {total} 个数据")
            amount = 0
            for member in data["data"]["data"]:
                view = member["views"]
                uploader = member["uploader"]
                if member["like"] + member["dislike"] != 0:
                    point = round(member["like"] / (member["like"] + member["dislike"]) * 100, 0)
                else:
                    point = 0
                if view >= sview and point >= spoint and amount < samount:
                    if suploader == [] or uploader in suploader:
                        if searches__(member):
                            amount = amount + 1
                    if amount >= samount:
                        break
                elif amount >= samount:
                    break
        last = time.time()
        input(f"搜索完毕，共耗时 {round(last - now, 2)} s.\n")

    st = configuration()
    stitle = st["stitle"]
    path = st["path"]
    order_by = st["order_by"]
    spoint = st["spoint"]
    sview = st["sview"]
    samount = st["samount"]
    soperater = st["soperater"]
    suploader = st["suploader"]
    searches_(range_max, mode)


def configure_download_settings():
    print("1. 标题.json")
    print("2. 标题 - 作者.json")
    print("3. 关卡代号-干员1+干员2.json")
    stitle = input("选择文件名格式（默认为1）：").replace(" ", "")
    if stitle.replace(" ", "") not in ["1", "2", "3"]:
        stitle = "1"
    print(f"设定值：{stitle}")
    path = input("设置保存文件夹（为空默认当前目录\\download）：").replace(" ", "")
    if path == "" or not os.path.isdir(path):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "download")
    print(f"成功设置保存文件夹为：{path}")
    print("1. 热度")
    print("2. 最新")
    print("3. 浏览量")
    order_by = input("设置排序方式（为空默认为1）：").replace(" ", "")
    try:
        order_by = int(order_by)
        if order_by > 3 or order_by < 1:
            order_by = 1
    except:
        order_by = 1
    print(f"设定值：{order_by}")
    spoint = input("设置好评率限制(0-100)（为空不限制）：").replace(" ", "")
    try:
        spoint = int(spoint)
        if spoint > 99 or spoint < 0:
            spoint = 0
    except:
        spoint = 0
    print(f"设定值：{spoint}")
    sview = input("设置浏览量限制（大于你设置的值）（为空不限制）：").replace(" ", "")
    try:
        sview = int(sview)
    except:
        sview = 0
    print(f"设定值：{sview}")
    samount = input("设置下载数量(1-5)（为空默认为1）：").replace(" ", "")
    try:
        samount = int(samount)
    except:
        samount = 1
    print(f"设定值：{samount}")
    soperater = input("设置禁用干员（空格分隔）（为空不限制）：").split()
    print(f"设定值：{soperater}")
    suploader = input("设置只看作者（空格分隔）（为空不限制）：").split()
    print(f"设定值：{suploader}")
    input("按下Enter返回\n")
    return {
        'stitle': stitle,
        'path': path,
        'order_by': order_by,
        'spoint': spoint,
        'sview': sview,
        'samount': samount,
        'soperater': soperater,
        'suploader': suploader
    }


def generate_filename_mode3(keyword, data):
    #stage_name = data.get('stage_name', '')
    stage_name = keyword.upper()
    opers = data.get('opers', [])
    names = '+'.join(oper.get('name', '') for oper in opers)
    filename = f"{stage_name}_{names}"
    return filename


def generate_filename(content, stitle, uploader, keyword):
    if stitle == "1":
        file_name = content["doc"]["title"]
    elif stitle == "2":
        file_name = content["doc"]["title"] + " - " + uploader
    elif stitle == "3":
        file_name = generate_filename_mode3(keyword, content)
    return file_name


def mode1():
    def search_(member):
        content = json.loads(member["content"])
        names = [oper["name"] for oper in content["opers"]]
        opers_bool = False
        for opers in soperater:
            if opers in names:
                opers_bool = True
                break
        if opers_bool:
            return False
        file_name = generate_filename(content, stitle, uploader, keyword)
        file_path = os.path.join(path, f"{file_name}.json")
        i = 1
        while os.path.exists(file_path):
            file_path = os.path.join(path, f"{file_name} ({i}).json")
            i = i + 1
        write_to_file(file_path, content)
        print(f"成功写出文件：{file_path}")
        return True

    os.system("cls")
    print("已进入单次搜索并下载模式，（输入back返回）")
    keyword = input("请输入关卡代号：").replace(" ", "")
    if keyword.lower() == "back":
        return menu()
    st = configuration()
    stitle = st["stitle"]
    path = st["path"]
    order_by = st["order_by"]
    spoint = st["spoint"]
    sview = st["sview"]
    samount = st["samount"]
    soperater = st["soperater"]
    suploader = st["suploader"]
    os.system("cls")
    now = time.time()
    print(f"保存目录：{path}")
    if not os.path.exists(path):
        os.makedirs(path)
    data = json.loads(search(keyword, order_by))
    total = data["data"]["total"]
    print(f"搜索 {keyword} 共获得 {total} 个数据")
    amount = 0
    for member in data["data"]["data"]:
        view = member["views"]
        uploader = member["uploader"]
        if member["like"] + member["dislike"] != 0:
            point = round(member["like"] / (member["like"] + member["dislike"]) * 100, 0)
        else:
            point = 0
        if view >= sview and point >= spoint and amount < samount:
            if suploader == [] or uploader in suploader:
                if search_(member):
                    amount = amount + 1
            if amount >= samount:
                break
        elif amount >= samount:
            break
    last = time.time()
    input(f"搜索完毕，共耗时 {round(last - now, 2)} s.\n")
    return menu()


def mode2():
    os.system("cls")
    print("已进入批量搜索并下载模式，（输入back返回）")
    while True:
        keyword = input("请输入关卡代号(如WD,OD)：").replace(" ", "")
        if keyword.lower() == "back":
            return menu()
        elif "-" in keyword or len(keyword) != 2:
            print("仅输入前两个字母即可，请重新输入")
            continue
        else:
            break
    while True:
        print("1. 普通关")
        print("2. EX关")
        print("3. S关")
        print("4. TR关")
        print("5. MO关")
        print("6. 全部关")
        mode = input("请选择批量下载的关卡：").replace(" ", "")
        if mode in ["1", "2", "3", "4", "5", "6"]:
            mode = int(mode)
            break
        elif mode.lower() == "back":
            return menu()
        else:
            continue
    if mode == 6:
        return searches(keyword, 0, mode)
    if load_settings() and setting["range"] is not None:
        range_max = setting["range"][f"{mode}_range"]
        searches(keyword, range_max, mode)
        return menu()
    else:
        while True:
            range_max = input("请输入最大关卡：").replace(" ", "")
            if range_max in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]:
                range_max = int(range_max)
                break
            elif range_max.lower() == "back":
                return menu()
            else:
                print("尚不支持，请重新输入(1-9)")
                continue
    searches(keyword, range_max, mode)
    return menu()


def mode3():
    print("1. 下载设置")
    print("2. 批量设置")
    choose = input("请选择操作（输入back返回）：").replace(" ", "")
    if choose == "1":
        return download_set()
    elif choose == "2":
        return level_set()
    elif choose.lower() == "back":
        return menu()
    else:
        print("未知操作，请重新输入")
        return mode3()


def download_set():
    global setting
    load_settings()
    setting["download"] = configure_download_settings()
    save_data(setting)
    return menu()


def level_set():
    global setting
    normal_range = input("输入普通关最大关卡（默认9）：").replace(" ", "")
    try:
        normal_range = int(normal_range)
    except:
        normal_range = 9
    print(f"设定值：{normal_range}")
    ex_range = input("输入EX关最大关卡（默认8）：").replace(" ", "")
    try:
        ex_range = int(ex_range)
    except:
        ex_range = 8
    print(f"设定值：{ex_range}")
    s_range = input("输入S关最大关卡（默认5）：").replace(" ", "")
    try:
        s_range = int(s_range)
    except:
        s_range = 5
    print(f"设定值：{s_range}")
    tr_range = input("输入TR关最大关卡（默认3）：").replace(" ", "")
    try:
        tr_range = int(tr_range)
    except:
        tr_range = 3
    print(f"设定值：{tr_range}")
    mo_range = input("输入MO关最大关卡（默认1）：").replace(" ", "")
    try:
        mo_range = int(mo_range)
    except:
        mo_range = 1
    print(f"设定值：{mo_range}")
    load_settings()
    setting["range"] = {
        "1_range": normal_range,
        "2_range": ex_range,
        "3_range": s_range,
        "4_range": tr_range,
        "5_range": mo_range,
    }
    if save_data(setting):
        input("保存成功，按下回车键返回\n")
    else:
        input("保存失败，按下回车键返回\n")
    return menu()


def menu():
    os.system("cls")
    print("-" * 60)
    print("1. 单次搜索并下载")
    print("2. 批量搜索并下载")
    print("3. 设置")
    choose = input("请选择操作：")
    if choose == "1":
        return mode1()
    elif choose == "2":
        return mode2()
    elif choose == "3":
        return mode3()


while True:
    menu()
