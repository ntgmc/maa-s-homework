import os
import zipfile
import datetime
import shutil

# 压缩文件夹列表
folders = [
    r"D:\GITHOME\maa\资源关",
    r"D:\GITHOME\maa\主线",
    r"D:\GITHOME\maa\往期剿灭",
    r"D:\GITHOME\maa\模组任务",
    r"D:\GITHOME\maa\插曲&别传",
    r"D:\GITHOME\maa\悖论模拟"
]

# 指定目标文件夹路径
target_dir = r"D:\GITHOME\maa\【下载看这里】合集下载"

# 创建目标文件夹
if not os.path.exists(target_dir):
    os.makedirs(target_dir)

# 生成压缩文件名
zip_file_name = "ALL-" + datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + ".zip"

# 压缩文件夹
zip_file_path = os.path.join(target_dir, zip_file_name)
with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
    for folder in folders:
        for root, dirs, files in os.walk(folder):
            for file in files:
                file_path = os.path.join(root, file)
                zip_file.write(file_path, os.path.relpath(file_path, os.path.dirname(folder)))

# 移动压缩文件到目标文件夹
shutil.move(zip_file_path, os.path.join(target_dir, zip_file_name))
print("所有文件已成功压缩为: {}".format(os.path.join(target_dir, zip_file_name)))
