import requests

def calculate_persent(item):
    like = item.get('like', 0)
    dislike = item.get('dislike', 0)
    total = like + dislike
    if total == 0:
        return 0
    else:
        return like / total * 100

def search(keyword):
    url = f"https://prts.maa.plus/copilot/query?desc=true&limit=15&page=1&order_by=hot&level_keyword={keyword}"
    headers = {
        "Origin": "https://prts.plus",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        total = data['data'].get('total', 0)
        if total > 0:
            ids = []
            for item in data['data']['data']:
                persent = calculate_persent(item)
                if persent < 80:
                    ids.append("*maa://" + str(item['id']))
                else:
                    ids.append("maa://" + str(item['id']))
            return len(ids), ', '.join(ids)
        else:
            return 0, "None"
    else:
        return 0, "None"

# 读取关键字文件
keywords_file = r'C:\Users\Administrator.Arknights-WZXKT\Desktop\python\maa\悖论模拟\keywords.txt'
output_file = r'C:\Users\Administrator.Arknights-WZXKT\Desktop\python\maa\悖论模拟\output.txt'
output_lines = []
with open(keywords_file, 'r', encoding='utf-8') as f:
    with open(output_file, 'w', encoding='utf-8') as output:
        for line in f:
            # 如果是空行，保留空行并继续下一行的处理
            if not line.strip():
                output_lines.append(line)
                continue
            keyword = line.strip()
            id_count, str_ids = search(keyword)
            output_lines.append(f"{keyword}\t{id_count}\t{str_ids}\n")
            print(f"{keyword}\t{id_count}\t{str_ids}\n")
        output.writelines(output_lines)

print("输出完成！")