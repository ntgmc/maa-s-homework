import os
import shutil

# 定义源文件夹和目标文件夹路径
source_folder = r"C:\Users\Administrator.Arknights-WZXKT\Downloads\测试"
destination_folder_base = r"C:\Users\Administrator.Arknights-WZXKT\Downloads\测试"

# 遍历需要移动的文件并进行移动
for file_name in os.listdir(source_folder):
    if file_name.endswith(".json"):
        # 解析文件名并获取目标文件夹路径
        chapter_num = file_name.split("-")[0].strip("磨难SHsh")
        chapter_num = int(chapter_num)
        destination_folder_path = os.path.join(destination_folder_base, "主线-第{:02d}章".format(chapter_num))
        
        # 创建目标文件夹（如果不存在）
        os.makedirs(destination_folder_path, exist_ok=True)
        
        # 构造源文件路径和目标文件路径
        source_file_path = os.path.join(source_folder, file_name)
        destination_file_path = os.path.join(destination_folder_path, file_name)
        
        # 移动文件
        shutil.move(source_file_path, destination_file_path)
        
        # 输出提示信息
        print("成功移动文件'{}'到文件夹'{}'".format(source_file_path, destination_folder_path))

# 输出作者信息
print("程序作者：ChatGPT")
