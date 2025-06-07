# stream astream 
# invoke ainvoke
# batch abatch
# astream_event(input:"hello", version="v2")没看懂
# 输入 输出
# 事件 char_model -> llm -> chain -> tool -> retriever -> prompt
from langchain_openai import ChatOpenAI
import asyncio # 子函数的主函数都是async await asyncio.gather(task1(), task2())
model = ChatOpenAI()

chunks =[]
for chunk in model.stream("Question ? "):
    chunks.append(chunk)
    print(chunk.content, end="|", flush=True)