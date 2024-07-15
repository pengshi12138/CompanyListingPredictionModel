# JSON对象
import json

json_obj = {
    "name": "中尉",
    "age": 30,
    "city": "New York"
}

# 将JSON对象转换为字符串
json_str = json.dumps(json_obj, indent=4, ensure_ascii=False)

# 写入TXT文件
with open('data.txt', 'w', encoding="utf-8") as file:
    file.write(json_str)

print("JSON object has been written to TXT file.")