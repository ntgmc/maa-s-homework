import os
import shutil
import zipfile

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 定义源文件夹和目标压缩包文件夹路径
source_folder_base = "主线"
destination_folder = r"主线\压缩包"
destination_folder2 = r"【下载看这里】合集下载"

os.makedirs(destination_folder, exist_ok=True)

# 获取源文件夹下的所有子目录
subfolders = [f.path for f in os.scandir(source_folder_base) if f.is_dir() and f.name != '压缩包']

# 遍历需要压缩的文件夹并进行压缩
for subfolder in subfolders:
    # 构造源文件夹和目标压缩包文件路径
    source_folder_path = os.path.join(source_folder_base, os.path.basename(subfolder))
    destination_zip_path = os.path.join(destination_folder, f"{os.path.basename(subfolder)}.zip")

    # 进行压缩
    with zipfile.ZipFile(destination_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, source_folder_path))

    print(f"成功压缩文件夹'{source_folder_path}'")

# 创建一个临时目录来存放要压缩的文件夹
temp_dir = os.path.join(destination_folder, "temp")
os.makedirs(temp_dir, exist_ok=True)

# 将所有要压缩的文件夹复制到临时目录
for subfolder in subfolders:
    shutil.copytree(subfolder, os.path.join(temp_dir, os.path.basename(subfolder)))

# 创建压缩文件
shutil.make_archive(os.path.join(destination_folder2, "主线"), 'zip', temp_dir)

# 删除临时目录
shutil.rmtree(temp_dir)

print(f"成功压缩文件夹到 '{os.path.join(destination_folder2, '主线.zip')}'")
