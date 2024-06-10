import requests
import json

amount_dict = {}
views_dict = {}
likes_dict = {}
# point_dict = {}

url = "https://prts.maa.plus/copilot/query?page=1&limit=99999&levelKeyword=&desc=true&orderBy=views"
_headers = {
    "Origin": "https://prts.plus",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
}

response = requests.get(url, headers=_headers)
print("Success")
data = response.json()["data"]["data"]
for member in data:
    amount_dict[member["uploader"]] = amount_dict.get(member["uploader"], 0) + 1
    amount_dict["total"] = amount_dict.get("total", 0) + 1
    views_dict[member["uploader"]] = views_dict.get(member["uploader"], 0) + member["views"]
    views_dict["total"] = views_dict.get("total", 0) + member["views"]
    likes_dict[member["uploader"]] = likes_dict.get(member["uploader"], 0) + member["like"]
    likes_dict["total"] = likes_dict.get("total", 0) + member["like"]
    # point_dict[member["uploader"]] = point_dict.get(member["uploader"], 0) + member["point"]
amount_sorted_dict = {k: v for k, v in sorted(amount_dict.items(), key=lambda item: item[1], reverse=True)}
views_sorted_dict = {k: v for k, v in sorted(views_dict.items(), key=lambda item: item[1], reverse=True)}
likes_sorted_dict = {k: v for k, v in sorted(likes_dict.items(), key=lambda item: item[1], reverse=True)}
with open("amount.json", 'w', encoding='utf-8') as file:
    json.dump(amount_sorted_dict, file, ensure_ascii=False, indent=4)
with open("views.json", 'w', encoding='utf-8') as file:
    json.dump(views_sorted_dict, file, ensure_ascii=False, indent=4)
with open("likes.json", 'w', encoding='utf-8') as file:
    json.dump(likes_sorted_dict, file, ensure_ascii=False, indent=4)
