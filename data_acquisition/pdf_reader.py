import os
import re
import pdfplumber



def find_chapter_title(text):
    # 正则表达式匹配类似“第一节”的章节标题
    pattern = (r'(?P<title>第一节 释 义|第一节 释义|第二节 概 览|第二节 概览|第三节 风险因素|第四节 发行人基本情况|'
               r'第五节 业务与技术|第六节 财务会计信息与管理层分析|第七节 募集资金运用与未来发展规划|第八节 公司治理与独立性|'
               r'第九节 投资者保护|第十节 其他重要事项|第十一节 声明|第十一节 声 明|第十二节 附 件|第十二节 附件)\n')
    match = re.search(pattern, text, re.MULTILINE)
    if match:
        return match.group('title')
    return None


def extract_and_save_by_chapters(pdf_path, output_dir, start_page=0):
    current_chapter_title = None
    current_chapter_text = ""
    print("处理 ", pdf_path, " 文件")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):

            if i < start_page:
                continue  # 跳过直到start_page

            page_text = page.extract_text()
            page_text = re.sub(r"\d+-\d+-\d+", "", page_text)
            # 检查页面中是否有新的章节标题
            new_chapter_title = find_chapter_title(page_text)
            if new_chapter_title:
                if current_chapter_title:
                    print("保存 ", current_chapter_title)
                    # 如果有新的章节标题出现，保存前一个章节的内容
                    save_path = os.path.join(output_dir, f"{current_chapter_title}.txt")
                    with open(save_path, 'w', encoding='utf-8') as txt_file:
                        txt_file.write(current_chapter_text)

                # 初始化新章节的文本
                current_chapter_title = new_chapter_title
                current_chapter_text = page_text[page_text.index(new_chapter_title):]
            else:
                # 如果没有找到新的章节标题，将文本添加到当前章节
                current_chapter_text += page_text + "\n"

    # 最后保存最后一个章节的内容
    if current_chapter_title:
        save_path = os.path.join(output_dir, f"{current_chapter_title}.txt")
        with open(save_path, 'w', encoding='utf-8') as txt_file:
            txt_file.write(current_chapter_text)


def process_all_pdfs_in_directory(directory_path, output_directory):
    for filename in os.listdir(directory_path):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(directory_path, filename)
            chapter_output_dir = os.path.join(output_directory, os.path.splitext(filename)[0])
            extract_and_save_by_chapters(pdf_path, chapter_output_dir)


# 主程序入口
directory_path = '../data/pdf'
output_directory = '../data/txt'

process_all_pdfs_in_directory(directory_path, output_directory)

