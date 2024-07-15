"""
获取 excel 中 PDF下载链接下载数据
"""

import pandas as pd
import requests

# 假设你已经有了一个DataFrame，这里我们创建一个示例DataFrame
excel_name = "../data/沪市IPO_全部_updated_data.xlsx"
file_url = "../data/pdf/"
df = pd.read_excel(excel_name)

# 遍历DataFrame的每一行
for index, row in df.iterrows():

    if index > 2:
        break

    url = row['招股书PDF']
    file_name = file_url + row['公司全称'] + ".pdf"

    # 使用requests下载文件
    response = requests.get(url)

    # 确保请求成功
    if response.status_code == 200:
        # 将文件写入到以'name'列命名的文件中
        with open(file_name, 'wb') as file:
            file.write(response.content)
        print(f"文件 {file_name} 下载成功")
    else:
        print(f"无法下载 {url}，状态码：{response.status_code}")