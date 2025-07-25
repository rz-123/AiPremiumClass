"""
借助langchain实现图书管理系统开发扩展，通过图书简介为借阅读者提供咨询。

- 读取外部csv文件来加载图书信息
- 使用langchain的LLM模型进行图书简介的生成和查询
- 支持根据聊天历史来调整图书咨询的内容
"""

import os
import pandas as pd
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage

# 加载.env文件
load_dotenv()
API_KEY = os.getenv("API_KEY")
AES_URL = os.getenv("AES_URL")

# 初始化LLM
llm = ChatOpenAI(
    openai_api_key=API_KEY,
    openai_api_base=AES_URL,
    model_name="glm-4-airx",
    temperature=0.7
)

# 读取图书信息
def load_books(csv_path):
    """
     读取 csv 文件用于图书咨询系统
    """
    df = pd.read_csv(csv_path)
    books = df.to_dict(orient="records")
    return books

# 生成图书简介（如简介为空时自动生成）
def generate_book_intro(book):
    if pd.isna(book["简介"]) or not book["简介"]:
        prompt = f"请为以下图书生成简短简介：书名《{book['书名']}》，作者：{book['作者']}。"
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content
    return book["简介"]

# 图书咨询对话
def consult_book(books, user_query, chat_history=None):
    if chat_history is None:
        chat_history = []
    # 拼接所有图书信息，去掉库存字段
    books_info = "\n".join([
        f"{b['编号']}《{b['书名']}》, 作者：{b['作者']}, 类型：{b['类型']}, 简介：{generate_book_intro(b)}"
        for b in books
    ])
    # user role system prompt template
    system_prompt = (
        "你是一个图书馆咨询助手，以下是图书信息：\n"
        f"{books_info}\n"
        "请根据用户提问，结合图书简介和聊天历史，给出专业、简明的推荐或解答。只能推荐图书信息中的书目。"
    )
    messages = [SystemMessage(content=system_prompt)]
    # 拼接用户和助手的聊天历史
    for msg in chat_history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))
    messages.append(HumanMessage(content=user_query))
    # 将对话历史和用户输入一起传入LLM
    response = llm.invoke(messages)
    return response.content

# 聊天历史保存
def save_history(session_id, chat_history):
    """
    保存会话聊天历史
    """
    with open(f"history_{session_id}.json", "w", encoding="utf-8") as f:
        json.dump(chat_history, f, ensure_ascii=False, indent=2)

# 聊天历史加载
def load_history(session_id):
    """
    加载会话聊天历史
    """
    try:
        with open(f"history_{session_id}.json", "r", encoding="utf-8") as f:
            chat_history = json.load(f)
    except FileNotFoundError:
        chat_history = []
    return chat_history

if __name__ == "__main__":
    print(f"当前工作目录: {os.getcwd()}")
    # 加载文件名为book_info.csv 的书籍数据
    books = load_books("D:\\interij\\pyProject\\AiPremiumClass\\余贵飞\\week14\\book_info.csv")
    session_id = input("请输入session_id（用于区分不同会话）：").strip()
    # 加载对话历史
    chat_history = load_history(session_id)
    print("欢迎来到图书馆咨询系统，输入'退出'结束。")
    while True:
        user_input = input("你想咨询什么？")
        if user_input.strip() == "q":
            break
        answer = consult_book(books, user_input, chat_history)
        print("助手：", answer)
        chat_history.append({"role": "user", "content": user_input})
        chat_history.append({"role": "assistant", "content": answer})
        save_history(session_id, chat_history)