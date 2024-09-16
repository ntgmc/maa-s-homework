from bs4 import BeautifulSoup
import requests


def extract_tr_contents(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    tr_contents = []

    for tr in soup.find_all('tr'):
        td_contents = [td.get_text().strip() for td in tr.find_all('td')]
        if len(td_contents) == 3:  # 确保td_contents包含两个元素，即干员名和关卡
            tr_contents.append((td_contents[0], td_contents[1], td_contents[2]))
        else:
            print(f"Warning: {td_contents}")

    return tr_contents


headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0',
}
response = requests.get(
    "https://prts.wiki/w/%E5%B9%B2%E5%91%98%E6%A8%A1%E7%BB%84%E4%B8%80%E8%A7%88/%E6%A8%A1%E7%BB%84%E4%BB%BB%E5%8A%A1",
    headers=headers)
# 提取HTML中的角色名
tr_contents = extract_tr_contents(response.text)
with open('module.txt', 'w', encoding='utf-8') as f:
    for tr_content in tr_contents:
        if tr_content[1] == '[[]]':
            continue
        line = '\t'.join(tr_content)
        f.write(line + '\n')
