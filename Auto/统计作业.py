# import requests
import json

amount_dict = {}
views_dict = {}
likes_dict = {}
dislikes_dict = {}

# url = "https://prts.maa.plus/copilot/query?page=1&limit=99999&levelKeyword=&desc=true&orderBy=views"
# _headers = {
#     "Origin": "https://prts.plus",
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
# }
#
# response = requests.get(url, headers=_headers)
# print("Success")
# data = response.json()["data"]["data"]
with open('data.json', 'r', encoding='utf-8') as file:
    data = json.load(file)
for member in data:
    amount_dict["total"] = amount_dict.get("total", 0) + 1
    amount_dict[member["uploader"]] = amount_dict.get(member["uploader"], 0) + 1
    views_dict["total"] = views_dict.get("total", 0) + member["views"]
    views_dict[member["uploader"]] = views_dict.get(member["uploader"], 0) + member["views"]
    likes_dict["total"] = likes_dict.get("total", 0) + member["like"]
    likes_dict[member["uploader"]] = likes_dict.get(member["uploader"], 0) + member["like"]
    dislikes_dict["total"] = dislikes_dict.get("total", 0) + member["dislike"]
    dislikes_dict[member["uploader"]] = dislikes_dict.get(member["uploader"], 0) + member["dislike"]
amount_sorted_dict = {k: v for k, v in sorted(amount_dict.items(), key=lambda item: item[1], reverse=True)}
views_sorted_dict = {k: v for k, v in sorted(views_dict.items(), key=lambda item: item[1], reverse=True)}
likes_sorted_dict = {k: v for k, v in sorted(likes_dict.items(), key=lambda item: item[1], reverse=True)}
with open("amount.json", 'w', encoding='utf-8') as file:
    json.dump(amount_sorted_dict, file, ensure_ascii=False, indent=4)
with open("views.json", 'w', encoding='utf-8') as file:
    json.dump(views_sorted_dict, file, ensure_ascii=False, indent=4)
with open("likes.json", 'w', encoding='utf-8') as file:
    json.dump(likes_sorted_dict, file, ensure_ascii=False, indent=4)
average_point = likes_dict['total'] / (likes_dict['total'] + dislikes_dict['total']) * 100 if likes_dict['total'] + dislikes_dict['total'] != 0 else 0
# 整合数据
user_profiles = {"average": {
    '平均每人作业数': amount_sorted_dict['total'] / len(amount_sorted_dict),
    '平均每人浏览量': views_sorted_dict['total'] / len(amount_sorted_dict),
    '平均每人好评数': likes_sorted_dict['total'] / len(amount_sorted_dict),
    '平均每作业浏览量': views_sorted_dict['total'] / amount_sorted_dict['total'],
    '平均每作业好评数': likes_sorted_dict['total'] / amount_sorted_dict['total'],
    '平均每作业好评率': average_point,
    '好差评比': likes_dict['total'] / dislikes_dict['total'] if dislikes_dict['total'] != 0 else likes_dict['total'],
}}
for user in amount_sorted_dict.keys():
    user_profiles[user] = {
        '作业数': amount_dict[user],
        '浏览量': views_dict[user],
        '好评数': likes_dict[user],
        '每作业浏览量': views_dict[user] / amount_dict[user] if amount_dict[user] != 0 else 0,
        '每作业好评数': likes_dict[user] / amount_dict[user] if amount_dict[user] != 0 else 0,
        '每作业好评率': round(likes_dict[user] / (likes_dict[user] + dislikes_dict[user]) * 100, 2) if likes_dict[user] + dislikes_dict[user] != 0 else 0,
    }
# 保存整合数据
with open('user_profiles.json', 'w', encoding='utf-8') as file:
    json.dump(user_profiles, file, ensure_ascii=False, indent=4)
