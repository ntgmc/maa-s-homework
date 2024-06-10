import requests
import json

dict = {}

url = "https://prts.maa.plus/copilot/query?page=1&limit=99999&levelKeyword=&desc=true&orderBy=views"
_headers = {
    "Origin": "https://prts.plus",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
}

response = requests.get(url, headers=_headers)
print("Success")
data = response.json()["data"]["data"]
for member in data:
    dict[member["uploader"]] = dict.get(member["uploader"], 0) + 1
    dict["total"] = dict.get("total", 0) + 1
sorted_dict = {k: v for k, v in sorted(dict.items(), key=lambda item: item[1], reverse=True)}
with open("output.json", 'w', encoding='utf-8') as file:
    json.dump(sorted_dict, file, ensure_ascii=False, indent=4)
