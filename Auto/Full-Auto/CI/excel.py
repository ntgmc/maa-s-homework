from openpyxl import load_workbook
import os
import datetime
import pytz

base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
print(base_path)
os.chdir(base_path)
file_path = os.path.join('Auto', 'Full-Auto', 'CI', 'paradox_develop.txt')
job_categories = ['先锋', '近卫', '重装', '狙击', '术师', '医疗', '辅助', '特种']
now = datetime.datetime.now()
date = now.astimezone(pytz.timezone('Asia/Shanghai')).strftime('%Y.%m.%d %H:%M:%S')


class DoTxt:
    def __init__(self, file_name):
        self.file_name = file_name

    def read_paradox_lines(self):
        data = []
        with open(self.file_name, "r", encoding="utf-8") as f:
            lines = f.readlines()
        job_num = 0
        sub_data = [[job_categories[job_num], '有无', '代码', None]]
        for line in lines:
            if line == '\n':
                data.append(sub_data)
                if job_num == 7:
                    break
                job_num += 1
                sub_data = [[job_categories[job_num], '有无', '代码', None]]
                continue
            parts = line.strip().split('\t')
            job = parts[0]
            num = parts[1]
            try:
                codes = parts[2]
            except IndexError:
                codes = ''
            sub_data.append([job, num, codes, None])
        return data

    def read_module_user_lines(self):
        data = [[f'更新日期：{date}'], ['干员', '关卡', '数量', '代码']]
        with open(self.file_name, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines:
            parts = line.strip().split('\t')
            oper = parts[0]
            level = parts[1]
            num = parts[2]
            try:
                codes = parts[3]
            except IndexError:
                codes = 'None'
            data.append([oper, level, num, codes])
        return data

    def read_module_develop_lines(self):
        data = [[f'更新日期：{date}'], ['干员', '关卡', '数量', '代码', '内容']]
        with open(self.file_name, "r", encoding="utf-8") as f:
            lines = f.readlines()
        i = 1
        for line in lines:
            parts = line.strip().split('\t')
            oper = parts[0]
            level = parts[1]
            num = parts[2]
            try:
                codes = parts[3]
            except IndexError:
                codes = 'None'
            content = module_task[i + 1][2]
            data.append([oper, level, num, codes, content])
            i += 1
        return data

    def read_module_task_lines(self):
        data = [[f'更新日期：{date}'], ['干员', '关卡', '内容']]
        with open(self.file_name, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines:
            parts = line.strip().split('\t')
            oper = parts[0]
            level = parts[1]
            content = parts[2]
            data.append([oper, level, content])
        return data


class DoExcel:
    def __init__(self, file_name, sheet_name):
        self.file_name = file_name
        self.sheet_name = sheet_name

    def get_data(self):
        wb = load_workbook(self.file_name)
        sheet = wb[self.sheet_name]
        test_data = []
        for i in range(1, sheet.max_row + 1):
            sub_data = []
            for j in range(1, sheet.max_column + 1):
                sub_data.append(sheet.cell(row=i, column=j).value)
            test_data.append(sub_data)
        return test_data

    def write_data(self, data, start_column=1):
        wb = load_workbook(self.file_name)
        sheet = wb[self.sheet_name]

        for row_idx, row_data in enumerate(data, start=1):
            for col_idx, value in enumerate(row_data, start=start_column):
                if isinstance(value, list):
                    for sub_col_idx, sub_value in enumerate(value, start=col_idx):
                        sheet.cell(row=row_idx, column=sub_col_idx, value=sub_value)
                else:
                    sheet.cell(row=row_idx, column=col_idx, value=value)

        wb.save(self.file_name)

    def write_paradox_data(self, data):
        for i, sub_list in enumerate(data, start=1):
            self.write_data(sub_list, start_column=i * 4 - 3)

    def write_module_data(self, data):
        self.write_data(data)


if __name__ == '__main__':
    # test_data1 = Do_excel("Excel/悖论模拟干员名单作者版.xlsx", "Sheet1").get_data()
    # print(test_data1)
    # test_data2 = Do_excel("Excel/悖论模拟干员名单用户版.xlsx", "Sheet1").get_data()
    # print(test_data2)

    paradox_develop = DoTxt('Auto/Full-Auto/CI/paradox_develop.txt').read_paradox_lines()
    # print(paradox_develop)
    DoExcel("Excel/悖论模拟干员名单作者版.xlsx", "Sheet1").write_paradox_data(paradox_develop)

    paradox_user = DoTxt('Auto/Full-Auto/CI/paradox_user.txt').read_paradox_lines()
    # print(paradox_user)
    DoExcel("Excel/悖论模拟干员名单用户版.xlsx", "Sheet1").write_paradox_data(paradox_user)

    module_task = DoTxt('Auto/Full-Auto/CI/module.txt').read_module_task_lines()
    # print(module_task)
    DoExcel("Excel/模组任务.xlsx", "Sheet1").write_module_data(module_task)

    module_develop = DoTxt('Auto/Full-Auto/CI/module_develop.txt').read_module_develop_lines()
    # print(module_develop)
    DoExcel("Excel/模组任务干员名单作者版.xlsx", "Sheet1").write_module_data(module_develop)

    module_user = DoTxt('Auto/Full-Auto/CI/module_user.txt').read_module_user_lines()
    # print(module_user)
    DoExcel("Excel/模组任务干员名单用户版.xlsx", "Sheet1").write_module_data(module_user)
