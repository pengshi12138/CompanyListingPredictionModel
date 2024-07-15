import json
import os
import re
import time
from collections import Counter
import pandas as pd
import tiktoken
from sparkai.llm.llm import ChatSparkLLM, ChunkPrintHandler
from sparkai.core.messages import ChatMessage

# 星火认知大模型Spark Max的URL值，其他版本大模型URL值请前往文档（https://www.xfyun.cn/doc/spark/Web.html）查看
SPARKAI_URL = 'wss://spark-api.xf-yun.com/v1.1/chat'
# 星火认知大模型调用秘钥信息，请前往讯飞开放平台控制台（https://console.xfyun.cn/services/bm35）查看
SPARKAI_APP_ID = '02c5d0b0'
SPARKAI_API_SECRET = 'MmZkOWUwYzk4MDkxMmJhNzA2NWRjZmVh'
SPARKAI_API_KEY = 'b5ea824c5676390e883416d0d804c44d'
# 星火认知大模型Spark Max的domain值，其他版本大模型domain值请前往文档（https://www.xfyun.cn/doc/spark/Web.html）查看
SPARKAI_DOMAIN = 'general'
# txt存放的文件夹路径
txt_path = "../data/txt/"
# 创建一个tokenizer
tokenizer = tiktoken.get_encoding("cl100k_base")  # 使用与你的模型兼容的tokenizer
# 最大字输入的token大小
MAX_TOKENS_PER_REQUEST = 3000
# prompt 提示词
prompts = {
    "system": '你现在是金融分析师，回答的格式只能是json格式的字符串，如字符串"{"A":"B", "C":"D"}"，根据用户所给的语句块提取金融相关的特征信息，无需联网查询。对应的金融信息特征和值采用键值对的格式，也就是key:value，其中要注意对于提取不出来的特征，value值设置为None',
    "第二节": '分析语句块，提取对应的特征以键值对的JSON格式形式输出。提取如下两个特征，一是是否为国家支持行业，判断“是”与“否”，或者None；二是运营情况良好程度，根据你的理解，按照“中”、“高”和“低”，或者None的值进行程度判定。回答结果返回JSON格式字符串，如“{"是否为国家支持行业": "是","运营情况良好程度":"高"}”。如果字段中不存在相关的特征提取，则value值写上None，如“{"是否为国家支持行业": None,"运营情况良好程度":None}”',
    "第三节": '分析语句块，提取对应的特征以键值对的JSON格式形式输出。提取如下两个特征，一是风险等级，按照你的理解判断“高”，“中”，“低”和None，其中None表示该语句块不存在该特征；二是风险类型，按照你的理解风险类型是“创新风险”，“经营风险”，“技术风险”，“财务风险”，“内控风险”，“法律风险”和None，其中None表示该语句块不存在该特征。回答结果返回JSON格式字符串，如:{"风险等级": "高","风险类型":"创新风险"}。',
    "第四节": '分析语句块，提取对应的特征以键值对的JSON格式形式输出。提取如下一个特征，一是公司大股东分散情况，统计具有5%以上股票的大股东个数，如果该语句块不存在该相关特征，值为None。回答结果格式JSON格式字符串，举一个例子如“{"大股东分散情况": None}”。',
    "第五节": '分析语句块，提取对应的特征以键值对的JSON格式形式输出。提取如下三个特征，一是专利数量，分析语句中公司及其子公司拥有的专利数量，需要注意是发明人专利还是公司拥有的专利进行判断，需要的是公司拥有的专利数量而不是发明人专利，如果该语句块不存在相关公司专利信息和专利特征，输出为None；二是是否有核心技术，输出结果为“是”、“否”或者None，如果该语句块设计核心专利的讲述，输出为None；；三是文本情感，根据你的理解判断文本透露出来的情感，输出结果为“积极”、“消极”和“中性”。回答的结果格式为JSON格式字符串，举一个例子，如“{"专利数量":None, "是否有核心技术":"是", "文本情感":"积极"}”',
    "第六节": '分析语句块，提取对应的特征以键值对的JSON格式形式输出。提取如下三个特征，一是营业收入，找出最新记录的营业收入具体的值，以万元为单位，如果该语句块不存在，则为None；二是净利润，找出最新记录净利润的具体值，以万元为单位，如果该语句块不存在该相关特征，则为None；三是资产负债率，找出最新记录资产负债率的具体值，以百分比为单位，如果该语句块不存在该相关特征，则为None；四是利润占营收的比例，找出最近记录利润占营收的比例的具体值，以百分比为单位，如果该语句块不存在该相关特征，则为None。返回的结果格式需要按照JSON格式回答，不能够有其它说明性语句，举一个例子，如“{"营业收入": 1000,"净利润":1000,"资产负债率":60,"利润":20}”',
    "第七节": '分析语句块，提取对应的特征以键值对的JSON格式形式输出。提取如下一个特征，一是未来憧憬程度，根据你的理解进行分析该文本信息进行判断，输出结果为“积极”，“消极”和“中性”。回答的结果为JSON格式字符串，如“{"未来憧憬程度":"积极"}”',
    "第八节": '分析语句块，提取对应的特征以键值对的JSON格式形式输出。提取如下两个特征，一是违法违规行为的恶劣程度，根据你的分析判断他的恶劣程度，输出结果为“高”、“中”和“低”，如果该语句块不存在该相关特征，则为None；二是公司创始人的品德，根据你的理解判断他的道德情况，输出结果为“高”、“中”和“低”，如果该语句块不存在该相关特征，则为None。回答的结果为JSON格式字符串，如“{"违法违规行为的恶劣程度":"高", "公司创始人的品德":"高"}”',
}


# 分割文本
def split_text_with_overlap(text, max_new_tokens, overlap=500):
    chunks = []
    if len(text) < max_new_tokens:
        chunks.append(text)
        return chunks
    block_num = int(len(text) / max_new_tokens)
    for i in range(block_num):
        if i == 0:
            chunks.append(text[max_new_tokens * i: max_new_tokens * (i + 1)])
            continue
        chunks.append(text[max_new_tokens * i - overlap: max_new_tokens * (i + 1)])
    if len(text) % max_new_tokens != 0:
        chunks.append(text[max_new_tokens * (block_num + 1):])
    return chunks


def split_text_with_keywords(text, keywords, window_size=MAX_TOKENS_PER_REQUEST):
    contexts = []
    last_match_end = 0  # 截停点
    # 定义关键词的正则表达式
    keyword_pattern = '|'.join(keywords)
    # 查找所有匹配关键词的位置
    for match in re.finditer(keyword_pattern, text):
        if last_match_end >= match.start():
            continue
        # 计算上下文的起始和结束位置
        start_index = max(0, match.start() - window_size // 2)
        end_index = min(len(text), match.start() + window_size // 2)
        # 更新上一次匹配结束的位置
        last_match_end = end_index
        # 提取上下文
        context = text[start_index : end_index]
        # 添加到结果列表
        contexts.append(context)
    return contexts


# 调用API
def call_api(chunk, prompt):
    spark = ChatSparkLLM(
        spark_api_url=SPARKAI_URL,
        spark_app_id=SPARKAI_APP_ID,
        spark_api_key=SPARKAI_API_KEY,
        spark_api_secret=SPARKAI_API_SECRET,
        spark_llm_domain=SPARKAI_DOMAIN,
        streaming=False,
    )
    messages = [
        ChatMessage(
            role="system",
            content=prompts['system']
        ),
        ChatMessage(
            role="user",
            content='"' + chunk + '"。' + prompt
        )
    ]
    handler = ChunkPrintHandler()
    response = spark.generate([messages], callbacks=[handler])
    if is_json(response.generations[0][0].text):
        print(response.generations[0][0].text)
        return json.loads(response.generations[0][0].text)
    return None


def is_json(myjson):
    try:
        json_object = json.loads(myjson)
    except json.JSONDecodeError:
        return False
    return True


def analyze_txt_files(directory):
    results = []
    # 遍历所有子目录
    for i, subdir in enumerate(os.listdir(directory)):
        subdir_path = os.path.join(directory, subdir)

        # 检查是否为文件夹
        if os.path.isdir(subdir_path):
            # 处理.txt文件
            txt_files = [f for f in os.listdir(subdir_path) if f.endswith('.txt')]
            # 存储当前文件夹的信息
            final_result = {'company': subdir}
            # 分析每个.txt文件
            for txt_file in txt_files:
                file_path = os.path.join(subdir_path, txt_file)
                # if str(txt_file).find("第二节") >= 0:
                #     with open(file_path, 'r', encoding='utf-8') as file:
                #         content = file.read()
                #         api_result_2 = analysis_txt(content, "第二节")
                #         final_result.update(api_result_2)
                #         print(api_result_2)
                #
                # if str(txt_file).find("第三节") >= 0:
                #     with open(file_path, 'r', encoding='utf-8') as file:
                #         content = file.read()
                #         api_result_3 = analysis_txt(content, "第三节")
                #         final_result.update(api_result_3)
                #         print(api_result_3)
                #
                # if str(txt_file).find("第四节") >= 0:
                #     with open(file_path, 'r', encoding='utf-8') as file:
                #         content = file.read()
                #         api_result_4 = analysis_txt(content, "第四节")
                #         final_result.update(api_result_4)
                #         print(api_result_4)

                if str(txt_file).find("第五节") >= 0:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                        api_result_5 = analysis_txt(content, "第五节", ["专利"])
                        final_result.update(api_result_5)
                        print(api_result_5)

                if str(txt_file).find("第六节") >= 0:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                        api_result_6 = analysis_txt(content, "第六节", ["净利润"])
                        final_result.update(api_result_6)
                        print(api_result_6)
                #
                # if str(txt_file).find("第七节") >= 0:
                #     with open(file_path, 'r', encoding='utf-8') as file:
                #         content = file.read()
                #         api_result_7 = analysis_txt(content, "第七节")
                #         final_result.update(api_result_7)
                #         print(api_result_7)
                #
                # if str(txt_file).find("第八节") >= 0:
                #     with open(file_path, 'r', encoding='utf-8') as file:
                #         content = file.read()
                #         api_result_8 = analysis_txt(content, "第八节")
                #         final_result.update(api_result_8)
                #         print(api_result_8)

                time.sleep(0.2)
            # 写入TXT文件
            with open(os.path.join(subdir_path, 'result.txt'), 'w', encoding="utf-8") as file:
                file.write(json.dumps(final_result, indent=4, ensure_ascii=False))
            # 将文件夹数据添加到结果列表中
    time.sleep(0.5)


def analysis_txt(content, key, keywords=None):
    if keywords is None:
        text_chunks = split_text_with_overlap(content, MAX_TOKENS_PER_REQUEST)
    else:
        text_chunks = split_text_with_keywords(content, keywords=keywords)
    api_responses = []
    for chunk in text_chunks:
        result_json = call_api(chunk, prompts[key])
        if result_json is not None:
            api_responses.append(result_json)
    api_result = merge_jsons(api_responses)
    return api_result


# 合并结果
def merge_jsons(json_objects):
    merged_counter = {}

    # 遍历每一个JSON对象
    for obj in json_objects:
        for key, value in obj.items():
            # 忽略None值
            if value is not None:
                # 如果键不在merged_counter中，初始化一个空的Counter
                if key not in merged_counter:
                    merged_counter[key] = Counter()
                # 更新计数
                merged_counter[key][value] += 1

    # 创建最终的合并后的JSON对象
    merged_json = {}
    for key, counter in merged_counter.items():
        # 选择出现次数最多的值
        most_common_value, _ = counter.most_common(1)[0]
        merged_json[key] = most_common_value

    return merged_json


if __name__ == '__main__':
    analyze_txt_files(txt_path)
