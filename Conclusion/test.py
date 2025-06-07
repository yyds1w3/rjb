from langchain_community.chat_models import ChatSparkLLM
import os
from dotenv import load_dotenv
load_dotenv()
app_id = os.getenv("app_id")
api_key = os.getenv("api_key")
api_secret = os.getenv("api_secret")
print(f"app_id: {app_id}")
print(f"api_key: {api_key}")
print(f"api_secret: {api_secret}")
chat = ChatSparkLLM(
    app_id=app_id, api_key=api_key, api_secret=api_secret,streaming=False
)
messages = [
    ("system", "你是一名专业的翻译家，可以将用户的中文翻译为英文。"),
    ("human", "我喜欢编程。"),
]
chat.invoke(messages)
