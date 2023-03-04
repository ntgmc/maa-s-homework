import os
import shutil

# 定义源文件夹和目标压缩包文件夹路径
source_folder_base = r"D:\GITHOME\maa\插曲&别传\插曲"
destination_folder = r"D:\GITHOME\maa\插曲&别传\插曲\压缩包"

# 遍历需要压缩的文件夹并进行压缩
for folder_name in os.listdir(source_folder_base):
    if folder_name.startswith("插曲"):
        # 构造源文件夹和目标压缩包文件路径
        source_folder_path = os.path.join(source_folder_base, folder_name)
        destination_zip_path = os.path.join(destination_folder, folder_name + ".zip")
        
        # 如果目标文件夹中已经存在同名的文件，先删除它
        if os.path.exists(destination_zip_path):
            os.remove(destination_zip_path)
        
        # 进行压缩
        shutil.make_archive(destination_zip_path[:-4], 'zip', source_folder_path)
        
        # 输出提示信息
        print("成功压缩文件夹'{}'为压缩包'{}'".format(source_folder_path, destination_zip_path))
        
# 压缩整个压缩包文件夹，并移动到目标文件夹中
shutil.make_archive(os.path.join(destination_folder, "插曲"), 'zip', destination_folder)
file_path = r"D:\GITHOME\maa\【下载看这里】合集下载\插曲.zip"
if os.path.exists(file_path):
    os.remove(file_path)
shutil.move(os.path.join(destination_folder, "插曲.zip"), r"D:\GITHOME\maa\【下载看这里】合集下载")

# 输出作者信息
print("程序作者：ChatGPT")
