import os
import shutil

# 定义源文件夹和目标压缩包文件夹路径
source_folder_base = r"D:\GITHOME\maa\主线"
destination_folder = r"D:\GITHOME\maa\主线\压缩包"

# 遍历需要压缩的文件夹并进行压缩
for i in range(12):
    # 构造源文件夹和目标压缩包文件路径
    source_folder_path = os.path.join(source_folder_base, "主线-第{:02d}章".format(i))
    destination_zip_path = os.path.join(destination_folder, "主线-第{:02d}章".format(i))
    
    # 进行压缩
    shutil.make_archive(destination_zip_path, 'zip', source_folder_path)
    
    # 输出提示信息
    print("成功压缩文件夹'{}'为压缩包'{}'".format(source_folder_path, destination_zip_path))

# 输出作者信息
print("程序作者：ChatGPT")
