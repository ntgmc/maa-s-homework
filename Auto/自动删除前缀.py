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
        # 检查文件名是否包含需要删除的字符
        chars_to_remove = ['序章 黑暗时代·上 - ', '第一章 黑暗时代·下 - ', '第二章 异卵同生 - ', '第三章 二次呼吸 - ', '第四章 急性衰竭 - ',
                           '第五章 靶向药物 - ', '第六章 局部坏死 - ', '第七章 苦难摇篮 - ', '第八章 怒号光明 - ', '第九章 风暴瞭望 - ',
                           '第十章 破碎日冕 - ', '第十一章 淬火尘霾 - ', '第十二章 惊霆无声 - ', '炎国 - ', '乌萨斯 - ', '伊比利亚 - ',
                           '哥伦比亚 - ', '卡西米尔 - ', '玻利瓦尔 - ', '莱塔尼亚 - ', '萨尔贡 - ', '拉特兰 - ', '汐斯塔 - ', '先锋 - ',
                           '术士 - ', '重装 - ', '狙击 - ', '医疗 - ', '特种 - ', '近卫 - ', '辅助 -']
        found = False
        for char in chars_to_remove:
            if char in filename:
                # 生成新的文件名
                new_filename = filename.replace(f'MAACopilot_{char}', '')
                # 重命名文件
                os.rename(os.path.join(directory, filename), os.path.join(directory, new_filename))
                print(f'Renamed {filename} to {new_filename}.')
                found = True
                break
        if not found and 'MAACopilot_' in filename:
            # 生成新的文件名
            new_filename = filename.replace('MAACopilot_', '')
            # 重命名文件
            os.rename(os.path.join(directory, filename), os.path.join(directory, new_filename))
            print(f'Renamed {filename} to {new_filename}.')
# 让程序等待用户输入任意内容后才关闭
input('程序执行完毕，请按任意键继续...')
