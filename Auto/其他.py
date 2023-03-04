import os
import shutil
import zipfile

# 定义压缩指定类型文件的函数
def zip_json_files(source_folder, destination_file):
    with zipfile.ZipFile(destination_file, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_folder):
            for file in files:
                if file.endswith(".json"):
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, arcname=os.path.relpath(file_path, source_folder))

# 往期剿灭
source_folder = r"D:\GITHOME\maa\往期剿灭"
destination_file = os.path.join(r"D:\GITHOME\maa\【下载看这里】合集下载", os.path.basename(source_folder) + "-" + str(len(os.listdir(source_folder))) + ".zip")
# 如果目标文件存在，就删除它
if os.path.exists(destination_file):
    os.remove(destination_file)

# 压缩指定类型文件
zip_json_files(source_folder, destination_file)
print(f"成功压缩{destination_file}")

# 模组任务
source_folder = r"D:\GITHOME\maa\模组任务"
destination_file = os.path.join(r"D:\GITHOME\maa\【下载看这里】合集下载", os.path.basename(source_folder) + "-" + str(len(os.listdir(source_folder))) + ".zip")
# 如果目标文件存在，就删除它
if os.path.exists(destination_file):
    os.remove(destination_file)

# 压缩指定类型文件
zip_json_files(source_folder, destination_file)
print(f"成功压缩{destination_file}")

# 资源关
source_folder = r"D:\GITHOME\maa\资源关"
destination_file = os.path.join(r"D:\GITHOME\maa\【下载看这里】合集下载", os.path.basename(source_folder) + "-" + str(len(os.listdir(source_folder))) + ".zip")
# 如果目标文件存在，就删除它
if os.path.exists(destination_file):
    os.remove(destination_file)

# 压缩指定类型文件
zip_json_files(source_folder, destination_file)
print(f"成功压缩{destination_file}")
