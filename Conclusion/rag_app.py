# rag_app.py
import os
import asyncio
import uuid
from pathlib import Path
from typing import List

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import uvicorn

import streamlit as st

# langchain相关库
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_deepseek import ChatDeepSeek

from dotenv import load_dotenv

# Load .env if exists
load_dotenv()

# 初始化 FastAPI
app = FastAPI()

# 初始化环境变量
if not os.getenv("DEEPSEEK_API_KEY"):
    import getpass
    os.environ["DEEPSEEK_API_KEY"] = getpass.getpass("Enter your DeepSeek API key: ")

# 初始化 LLM
llm = ChatDeepSeek(
    model="deepseek-chat",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    streaming=True
)

# 解析器
parser = StrOutputParser()

# Prompt模板
SYSTEM_PROMPT = """
You are a {job}, specialized in {skills}.
When answering questions:
1. First consult the provided context from the knowledge base
2. Then consider the conversation history
3. Finally provide a comprehensive answer
"""
prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])

base_chain = prompt | llm | parser

# 聊天历史存储（内存中）
session_store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in session_store:
        session_store[session_id] = ChatMessageHistory()
    return session_store[session_id]

chat_chain = RunnableWithMessageHistory(
    base_chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history"
)

# Embeddings 和 向量库
embedder = OllamaEmbeddings(model="nomic-embed-text")
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
VECTOR_DB_PATH = "./vector_db"
DATA_DIR = "./data"

class VectorDBManager:
    def __init__(self, db_path=VECTOR_DB_PATH):
        self.db_path = db_path
        self.vector_db = None
        self.load_db()

    def load_db(self):
        if os.path.exists(self.db_path):
            try:
                self.vector_db = FAISS.load_local(
                    self.db_path,
                    embedder,
                    allow_dangerous_deserialization=True
                )
                print("✅ 已加载向量数据库")
            except Exception as e:
                print(f"⚠️ 加载向量库失败: {e}")
                self.vector_db = None
        else:
            self.vector_db = None

    def save_db(self):
        if self.vector_db:
            self.vector_db.save_local(self.db_path)
            print("✅ 向量库已保存")

    def rebuild_from_data_dir(self):
        """从 data 目录扫描所有支持文档，重建向量库"""
        print("📂 从 data 目录重建向量库...")
        docs = []
        for root, _, files in os.walk(DATA_DIR):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                path = os.path.join(root, file)
                loader = None
                try:
                    if ext == ".pdf":
                        loader = PyPDFLoader(path)
                    elif ext == ".docx":
                        loader = Docx2txtLoader(path)
                    elif ext == ".txt":
                        loader = TextLoader(path)
                    else:
                        continue  # 忽略不支持的类型
                    loaded_docs = loader.load()
                    docs.extend(loaded_docs)
                except Exception as e:
                    print(f"⚠️ 加载文件失败: {path}, 错误: {e}")

        if not docs:
            print("⚠️ 没有有效文档，向量库未更新")
            return False

        split_docs = text_splitter.split_documents(docs)

        if self.vector_db is None:
            self.vector_db = FAISS.from_documents(
                documents=split_docs,
                embedding=embedder
            )
        else:
            self.vector_db = FAISS.from_documents(
                documents=split_docs,
                embedding=embedder
            )

        self.save_db()
        print(f"✅ 向量库重建完成，文档块数: {len(split_docs)}")
        return True

    def similarity_search(self, query: str, k=3):
        if self.vector_db is None:
            return []
        return self.vector_db.similarity_search(query, k=k)


vector_db_manager = VectorDBManager()

# FastAPI 请求模型
class RagRequest(BaseModel):
    question: str
    session_id: str = "default"

# FastAPI 路由 - 上传文件接口
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # 保存文件到 data 目录
        Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
        file_path = os.path.join(DATA_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

        # 重新构建向量库
        success = vector_db_manager.rebuild_from_data_dir()
        if not success:
            return {"status": "error", "message": "没有有效文档，向量库未更新"}

        return {"status": "success", "message": f"文件 {file.filename} 上传成功，向量库已更新"}

    except Exception as e:
        return {"status": "error", "message": str(e)}

# FastAPI 路由 - 问答接口，流式返回
@app.post("/chat")
async def rag_answer(request: RagRequest):
    # 检索相关文档
    docs = vector_db_manager.similarity_search(request.question, k=3)
    context = "\n\n".join([doc.page_content for doc in docs])

    async def generate_stream():
        rag_prompt = ChatPromptTemplate.from_template(
            "Context:\n{context}\n\nConversation History:\n{history}\n\nQuestion: {question}"
        )
        history = get_session_history(request.session_id)
        rag_chain = rag_prompt | llm

        async for chunk in rag_chain.astream({
            "context": context,
            "history": history.messages,
            "question": request.question
        }):
            yield str(chunk.content)
            await asyncio.sleep(0.02)

    return StreamingResponse(generate_stream(), media_type="text/event-stream")



# ==== Streamlit 前端 ====

def streamlit_app():
    st.title("RAG问答系统（FastAPI + Streamlit 集成示例）")

    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "messages" not in st.session_state:
        st.session_state.messages = []

    with st.sidebar:
        st.header("📂 上传文档 (PDF, DOCX, TXT)")
        uploaded_files = st.file_uploader("选择文件上传", type=["pdf", "docx", "txt"], accept_multiple_files=True)
        if st.button("上传并更新向量库"):
            if uploaded_files:
                for f in uploaded_files:
                    files = {"file": (f.name, f.getvalue())}
                    # 调用 FastAPI 上传接口
                    import requests
                    try:
                        response = requests.post("http://localhost:8000/upload", files=files)
                        if response.status_code == 200:
                            st.success(response.json().get("message"))
                        else:
                            st.error(f"上传失败: {response.text}")
                    except Exception as e:
                        st.error(f"请求上传接口失败: {e}")
            else:
                st.warning("请先选择文件")

        if st.button("清空聊天历史"):
            st.session_state.messages = []

    # 显示聊天记录
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"**用户:** {msg['content']}")
        else:
            st.markdown(f"**助手:** {msg['content']}")

    # 用户输入
    user_input = st.text_input("请输入你的问题：", key="input")
    if st.button("发送") and user_input.strip():
        st.session_state.messages.append({"role": "user", "content": user_input})

        # 调用后端 /chat 接口获取回答（同步版简化）
        import requests
        try:
            response = requests.post(
                "http://localhost:8000/chat",
                json={"question": user_input, "session_id": st.session_state.session_id},
                stream=True,
            )
            answer = ""
            if response.status_code == 200:
                for chunk in response.iter_lines(decode_unicode=True):
                    if chunk:
                        answer += chunk
                        # 实时显示（简单刷新）
                        st.session_state.messages[-1]["content"] = user_input
                        st.experimental_rerun()
                # 完整答案存入消息
                st.session_state.messages.append({"role": "assistant", "content": answer})
            else:
                st.error(f"接口调用失败: {response.text}")
        except Exception as e:
            st.error(f"调用后端接口失败: {e}")



if __name__ == "__main__":
    import sys

    # 你可以选择启动方式：
    # 1. 只启动 FastAPI: 运行 `python rag_app.py api`
    # 2. 只启动 Streamlit: 运行 `python rag_app.py ui`
    # 3. 同时启动两个（推荐分别用两个终端）

    if len(sys.argv) >= 2 and sys.argv[1] == "api":
        # 启动 FastAPI 服务
        uvicorn.run("rag_app:app", host="0.0.0.0", port=8000, reload=True)
    elif len(sys.argv) >= 2 and sys.argv[1] == "ui":
        # 启动 Streamlit
        streamlit_app()
    else:
        print("用法示例：")
        print("启动 API: python rag_app.py api")
        print("启动 UI: python rag_app.py ui")
