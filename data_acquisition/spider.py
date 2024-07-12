import re
import time

import requests
from bs4 import BeautifulSoup
import pandas as pd

# 定义请求的URL
shenzhen_url = 'http://eid.csrc.gov.cn/ipo/1017/index_f.html'
shanghai_url = 'http://eid.csrc.gov.cn/ipo/1010/index_f.html'
# 定义请求头
shenzhen_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Content-Length': '373',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Host': 'eid.csrc.gov.cn',
    'Origin': 'http://eid.csrc.gov.cn',
    'Referer': 'http://eid.csrc.gov.cn/ipo/1017/index_f.html',
    'Upgrade-Insecure-Requests': '1',
}

shanghai_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Content-Length': '391',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Host': 'eid.csrc.gov.cn',
    'Origin': 'http://eid.csrc.gov.cn',
    'Referer': 'http://eid.csrc.gov.cn/ipo/1010/index_f.html',
    'Upgrade-Insecure-Requests': '1',
}

def get_url(url, headers, form_data):
    # 发送GET请求
    response = requests.post(url, headers=headers, data=form_data)
    url_pattern = r"('http[s]?://[^']+')"
    # 检查请求是否成功
    if response.status_code == 200:
        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        # 在这里，你可以使用soup来解析HTML并提取所需的数据
        # 找到所有的tr元素
        for tr in soup.find_all('tr'):
            # 尝试获取第五个td元素（索引为4，因为索引是从0开始的）
            fifth_td = tr.find_all('td')[5] if len(tr.find_all('td')) >= 6 else None
            # 检查第五个td元素是否包含“你好”
            if fifth_td and '招股说明书' in fifth_td.get_text():
                # 如果包含，则处理这一行（比如打印所有td的内容）
                print("符合条件的行：")
                onclick_value = tr['onclick']
                # 查找匹配项
                match = re.search(url_pattern, onclick_value)
                # 如果找到了匹配项，就提取URL（去掉单引号）
                if match:
                    url = match.group(1).strip("'")
                    print(url)
                    print("---")
                    return url
                else:
                    break
    else:
        print("请求失败，状态码：", response.status_code)


def package_form(company, update_time=''):
    # 找到"("的位置
    paren_pos = company.find("(")
    # 如果找到了"("，则截取它之前的部分，否则保留原字符串
    if paren_pos != -1:
        new_company_name = company[:paren_pos]
    else:
        new_company_name = company
    # 定义表单数据
    form_data = {
        'keyWord': new_company_name,
        'endDate': update_time,
    }
    return form_data


def decompose_excel(url, headers, filename):
    # 写回Excel文件，覆盖原文件或写入新文件
    output_file_path = filename + '_updated_data.xlsx'  # 替换为你想要保存的文件名

    df = pd.read_excel(filename + ".xlsx")
    df['招股书PDF'] = ''
    # 遍历每行数据进行数据获取
    for index, row in df.iterrows():
        # 测试代码
        if int(index) % 50 == 0:
            df.to_excel(output_file_path, index=False, sheet_name='Sheet1')  # index=False表示不写入行索引
        # 每隔0.5运行一次
        time.sleep(0.2)
        company = row['公司全称']
        update_time = row['更新日期']
        form_data = package_form(company, update_time)
        PDF_url = get_url(url, headers, form_data)
        df.at[index, '招股书PDF'] = PDF_url


if __name__ == "__main__":
    # 提取上海的IPO公司的数据
    decompose_excel(shanghai_url, shanghai_headers, '../data/沪市IPO_全部')