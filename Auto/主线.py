import os
import shutil
import zipfile

# 定义源文件夹和目标压缩包文件夹路径
source_folder_base = r"D:\GITHOME\maa\主线"
destination_folder = r"D:\GITHOME\maa\主线\压缩包"

# 遍历需要压缩的文件夹并进行压缩
for i in range(15):
    # 构造源文件夹和目标压缩包文件路径
    source_folder_path = os.path.join(source_folder_base, f"第{i}章")
    destination_zip_path = os.path.join(destination_folder, f"第{i}章.zip")
    
    # 进行压缩
    with zipfile.ZipFile(destination_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, source_folder_path))
    
    print(f"成功压缩文件夹'{source_folder_path}'为压缩包'{destination_zip_path}'")

# 压缩所有章节的压缩包
destination_all_zip_path = os.path.join(destination_folder, "主线.zip")
with zipfile.ZipFile(destination_all_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for i in range(15):
        chapter_zip_path = os.path.join(destination_folder, f"第{i}章.zip")
        zipf.write(chapter_zip_path, os.path.basename(chapter_zip_path))

# 移动压缩包
destination_all_folder = r"D:\GITHOME\maa\【下载看这里】合集下载"
shutil.move(destination_all_zip_path, os.path.join(destination_all_folder, "主线.zip"))

input('程序执行完毕，请按任意键继续...')
