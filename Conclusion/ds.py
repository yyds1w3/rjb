# API-reading
from dotenv import load_dotenv
import os
import getpass
# front-ending
import streamlit as st
import tempfile
from langchain.chat_message_histories import StreamlitChatMessageHistory
from langchain_community.document_loaders import TextLoader
# RAG
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.agents import create_react_agent, AgentExecutor
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler
from langchain_core import prompts
from langchain_core.runnables import Runnable
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_deepseek import ChatDeepSeek
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
load_dotenv()
if not os.getenv("DEEPSEEK_API_KEY"):
    os.environ["DEEPSEEK_API_KEY"] = getpass.getpass("Enter your DeepSeek API key: ")

parser = StrOutputParser();
llm = ChatDeepSeek(
    model="deepseek-chat",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    streaming=True
)
prompt = ChatPromptTemplate.from_messages([
    ("system","You are a {job},You are good at {skills} .",),
    ("ai", "ok"),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])
runnable = prompt | llm | parser
store = {}
embedder = OllamaEmbeddings(model="nomic-embed-text")
vector_db = FAISS.load_local("./vector_db", embedder, allow_dangerous_deserialization=True) # 仅仅加载自己的数据库，不然可能恶意代码植入
class RagRequest(BaseModel):
    question: str
@app.post("/ask")
async def rag_answer(request: RagRequest):
    docs = vector_db.similarity_search(request.question, k=3)
    context = "\n\n".join([doc.page_content for doc in docs])
    async def generate_stream() -> AsyncGenerator[str, None]:  # 异步生成器
        prompt = ChatPromptTemplate.from_template(
            "基于以下上下文回答问题：\n{context}\n\n问题: {question}"
        )
        chain = prompt | llm

        # 使用异步流式调用 (关键修改！)
        async for chunk in chain.astream({"context": context, "question": request.question}):
            yield str(chunk.content)  # 确保返回字符串
            await asyncio.sleep(0.02)  # 控制流速

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream"
    )
# 根据session的id来得到历史记录
def get_session_history(session_id:str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]
# 创建一个有历史记录的runnable
with_message_history = RunnableWithMessageHistory(
        runnable,
        get_session_history,
        input_messages_key="input",
        history_messages_key="history"
        )
def loop():
    while ((text:=input("User: \n"))!= "q"):
        response = with_message_history.stream(
            {"job": "professional interviwer",
            "skills": "Multimodal Data Analysis Evaluation: Integrating multimodal data such as speech (language logic, emotional tone), video (micro-expressions, body language), and text (response content, resume), to construct a dynamic and quantitative evaluation system. It includes at least five core competency indicators (such as professional knowledge level, skill matching, language expression ability, logical thinking ability, innovation ability, adaptability and stress resistance, etc.).",
            "input": text
            },
            config={"configurable": {"session_id": "abc123"}}
        )
        print("Bot:")
        for chunk in response:
            print(chunk, end="")
    else: print("bye")

def main():
    loop()
main()



