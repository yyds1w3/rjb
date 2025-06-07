"""For basic init and call"""
from langchain_community.chat_models import ChatSparkLLM
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import os
load_dotenv()
app_id = os.getenv("app_id")
api_key = os.getenv("api_key")
api_secret = os.getenv("api_secret")

chat = ChatSparkLLM(
    spark_app_id=app_id, spark_api_key=api_key, spark_api_secret=api_secret
)
message = HumanMessage(content="Hello")
chat([message])