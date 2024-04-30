import requests
from bs4 import BeautifulSoup
import json
import os
import glob

download_mode = True
download_score_threshold = 50
job_categories = ['先锋', '近卫', '重装', '狙击', '术士', '医疗', '辅助', '特种']


def write_to_file(file_path, content):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(content, file, ensure_ascii=False, indent=4)


def calculate_percent(item):
    like = item.get('like', 0)
    dislike = item.get('dislike', 0)
    total = like + dislike
    if total == 0:
        return 0
    else:
        return round(like / total * 100, 2)


def code_output(percent, id, mode):
    if mode == 1:
        if percent <= 30:
            return f"***maa://{id} ({percent})"
        elif percent <= 50:
            return f"**maa://{id} ({percent})"
        elif percent <= 80:
            return f"*maa://{id} ({percent})"
        else:
            return f"maa://{id} ({percent})"
    else:
        if percent <= 30:
            return f"***maa://{id}"
        elif percent <= 50:
            return f"**maa://{id}"
        elif percent <= 80:
            return f"*maa://{id}"
        else:
            return f"maa://{id}"


def check_file_exists(job, keyword, id):  # 判断是否存在相同id但评分不同的文件
    pattern = f"./download/{job}/{keyword} - * - {id}.json"
    matching_files = glob.glob(pattern)
    if len(matching_files) > 0:
        for file_name in matching_files:
            os.remove(file_name)
            print(f"Removed {file_name}")


def search(keyword, job=None):
    if keyword == "W":
        print(f"成功搜索 {job} - {keyword}")
        return 0, 0, "None", "None"
    else:
        url = f"https://prts.maa.plus/copilot/query?page=1&limit=15&levelKeyword=悖论模拟&document={keyword}&desc=true&orderBy=hot"
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
            if download_mode and job:
                # 对列表按照评分进行排序，评分最高的在前面
                items_to_download.sort(key=lambda x: x[0], reverse=True)

                # 只下载评分最高的三个项目
                for percent, item in items_to_download[:3]:
                    file_path = f"./download/{job}/{keyword} - {int(percent)} - {item['id']}.json"
                    if not os.path.exists(file_path):
                        check_file_exists(job, keyword, item['id'])
                        write_to_file(file_path, json.loads(item['content']))
            print(f"成功搜索 {job} - {keyword}")
            return len(ids_develop), len(ids_user), ', '.join(ids_develop), ', '.join(ids_user)
        else:
            return 0, 0, "None", "None"
    else:
        print(f"请求失败！ERR_CONNECTION_REFUSED in search({keyword})")
        return 0, 0, "None", "None"


# 解析HTML并提取角色名
def extract_character_names(html_content):
    _character_names = set()
    soup = BeautifulSoup(html_content, 'html.parser')
    prop_cells = soup.find_all('div', class_='smw-table-cell smwprops')
    for cell in prop_cells:
        _name = cell.find('a').text.strip()
        _character_names.add(_name)
    return _character_names


def main():
    # 读取关键字文件
    keywords_file = './keywords.txt'
    output_file_develop = './output_develop.txt'
    output_file_user = './output_user.txt'
    output_lines_develop = []
    output_lines_user = []
    job_now = -1
    with open(keywords_file, 'r', encoding='utf-8') as f:
        with open(output_file_develop, 'w', encoding='utf-8') as output_develop, open(output_file_user, 'w',
                                                                                      encoding='utf-8') as output_user:
            for line in f:
                # 如果是空行，保留空行并继续下一行的处理
                if not line.strip():
                    output_lines_develop.append(line)
                    output_lines_user.append(line)
                    continue
                keyword = line.strip()
                if job_now + 1 < len(job_categories) and keyword == job_categories[job_now + 1]:
                    job_now += 1
                    continue
                id_count_develop, id_count_user, str_ids_develop, str_ids_user = search(keyword,
                                                                                        job_categories[job_now])
                output_lines_develop.append(f"{keyword}\t{id_count_develop}\t{str_ids_develop}\n")
                output_lines_user.append(f"{keyword}\t{id_count_user}\t{str_ids_user}\n")
            output_develop.writelines(output_lines_develop)
            output_user.writelines(output_lines_user)
    print("输出完成！")
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0',
    }
    params = {
        'title': '属性:悖论模拟对象',
        'limit': '500',
        'offset': '0',
        'filter': '',
    }
    response = requests.get('https://prts.wiki/index.php', params=params, headers=headers)
    # 提取HTML中的角色名
    character_names = extract_character_names(response.text)
    for file_name in ['output_develop.txt', 'output_user.txt']:
        # 处理txt文件
        with open(file_name, 'r', encoding='utf-8') as txt_file:
            lines = txt_file.readlines()
        # 处理每一行
        output_lines = []
        for line in lines:
            # 如果是空行，保留空行并继续下一行的处理
            if not line.strip():
                output_lines.append(line)
                continue
            parts = line.split('\t')
            name = parts[0]
            if name in character_names:
                output_lines.append(line)
            else:
                # 如果角色名不存在，将后面两个内容都变为"-"
                output_lines.append(name + '\t-\t-\n')
        # 写入处理后的内容到原来的txt文件中
        with open(file_name, 'w', encoding='utf-8') as output_file:
            output_file.writelines(output_lines)
    print("输出完成！")


if download_mode:
    for job in job_categories:
        if not os.path.exists(f'./download/{job}'):
            os.makedirs(f'./download/{job}')
# search("缪尔赛思", '先锋')
main()
