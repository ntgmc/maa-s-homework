import requests
from bs4 import BeautifulSoup

# 解析HTML并提取角色名
def extract_character_names(html_content):
    character_names = set()
    soup = BeautifulSoup(html_content, 'html.parser')
    prop_cells = soup.find_all('div', class_='smw-table-cell smwprops')
    for cell in prop_cells:
        name = cell.find('a').text.strip()
        character_names.add(name)
    return character_names

headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache',
        # 'cookie': '__bid_n=1873e38250c9d8666b4207; FPTOKEN=Bb5B78HBWcCGWrrLe2GuIs3YJaGnPjFd3022zsYumjLJKDIN8UOVc1eKRNjuDDPh+ABo7KcavqXfLMk3bpH6aVi83/X0Z7CDw1njp2+5mDczu9sr45zTz7ZQySlapmJA4uPF6vsF/RzayndfJv8vRvmrwdi/SqQRXZBuGO5AMUZzRvePBcuD49LwFWG5MYr5Ieo/dpwLBCJSSW0DIlGd8juAd1YzZZLAEeXr13+Hkc2A1+rlJA4Rcw8rE7DFMQK8ssQfUJ0CBvuncimvyfFRMRklVWrK/caSxc6AXM4oFU1knGmUTcLC5siKFsvbxfzFeOv1iOuTjUDklh2bqqmKj/oian8lwZej8THAl5xIGaBfth4dha7rYWrBoFtDoBUnVqaV3+Zsc/gx2UPbt8AUpQ==|/4lCKBu7B5SAE2MJChua0/ya8hmW312cxuZdTsI8viY=|10|7a1d354a6ff92a0880cdbd4a7d23f85c; Hm_lvt_e1369c7d981281aa581e68b669c5a75c=1711251082,1712909234; Hm_lpvt_e1369c7d981281aa581e68b669c5a75c=1712909234',
        'pragma': 'no-cache',
        'sec-ch-ua': '"Microsoft Edge";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'upgrade-insecure-requests': '1',
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

file_path = r"C:\Users\Administrator.Arknights-WZXKT\Desktop\python\maa\悖论模拟\output.txt"
file_path2 = r"C:\Users\Administrator.Arknights-WZXKT\Desktop\python\maa\悖论模拟\output2.txt"

# 处理txt文件
with open(file_path, 'r', encoding='utf-8') as txt_file:
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


# 写入处理后的内容到新的txt文件中
with open(file_path2, 'w', encoding='utf-8') as output_file:
    output_file.writelines(output_lines)

