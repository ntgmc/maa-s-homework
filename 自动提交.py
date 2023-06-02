import subprocess
import sys

def generate_summary_commit():
    # 使用Git命令行工具获取更改的文件列表
    result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
    if result.returncode != 0:
        print('Error: Failed to retrieve changed files.')
        return

    status_output = result.stdout.strip().split('\n')

    if len(status_output) == 0:
        print('No changes found.')
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
            print(f'Error: Failed to retrieve diff for file {file_path}')
            continue

        diff_output = result.stdout.strip().split('\n')
        summary_message += f'{file_path}: {diff_output[0]}\n'

    if summary_message == '':
        print('No summary message generated.')
        return

    # 提交总结性的commit
    subprocess.run(['git', 'add', '--all'])
    subprocess.run(['git', 'commit', '-m', f'Summary of changes:\n\n{summary_message}'])

    print('Summary commit generated successfully.')

# 在这里调用函数来自动生成总结性的commit
generate_summary_commit()
