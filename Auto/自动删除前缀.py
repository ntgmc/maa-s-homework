import os
import datetime

# 指定目录
directory = r'C:\Users\Administrator.Arknights-WZXKT\Downloads'

# 获取今天的日期
today = datetime.date.today()

# 遍历目录下的所有文件
for filename in os.listdir(directory):
    # 检查是否为.json文件且修改日期为今天
    if filename.endswith('.json') and datetime.date.fromtimestamp(os.path.getmtime(os.path.join(directory, filename))) == today:
        # 检查文件名是否包含"MAACopilot_"字符
        if 'MAACopilot_' in filename:
            # 生成新的文件名
            new_filename = filename.replace('MAACopilot_', '')
            # 重命名文件
            os.rename(os.path.join(directory, filename), os.path.join(directory, new_filename))
            print(f'Renamed {filename} to {new_filename}.')
# 执行您的Python代码

# 让程序等待用户输入任意内容后才关闭
input('程序执行完毕，请按任意键继续...')
