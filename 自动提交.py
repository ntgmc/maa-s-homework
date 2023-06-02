import subprocess

def generate_summary_commit():
    # 使用Git命令行工具获取更改的文件列表
    result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
    if result.returncode != 0:
        print('错误：无法获取更改的文件列表。')
        return

    status_output = result.stdout.strip().split('\n')

    if len(status_output) == 0:
        print('未发现更改的文件。')
        return

    # 生成总结性commit消息
    summary_message = ''
    for line in status_output:
        # 提取文件路径
        file_path = line[3:]

        # 跳过被删除的文件
        if line.startswith('D'):
            continue

        # 使用Git命令行工具获取每个文件的更改行数
        result = subprocess.run(['git', 'diff', '--stat', '--', file_path], capture_output=True, text=True)
        if result.returncode != 0:
            print(f'错误：无法获取文件 {file_path} 的差异。')
            continue

        diff_output = result.stdout.strip().split('\n')
        # 转义为中文
        diff_summary = diff_output[0].replace('insertions(+)', '个插入').replace('deletions(-)', '个删除')
        summary_message += f'{file_path}: {diff_summary}\n'

    if summary_message == '':
        print('未生成总结性消息。')
        return

    # 提交总结性的commit
    subprocess.run(['git', 'add', '--all'])
    subprocess.run(['git', 'commit', '-m', f'更改总结：\n\n{summary_message}'])

    print('成功生成总结性commit。')

# 在这里调用函数来自动生成总结性的commit
generate_summary_commit()
