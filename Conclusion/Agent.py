# API-reading
from dotenv import load_dotenv
import os
from pathlib import Path
import getpass
import asyncio
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import AsyncGenerator, List, Union, Tuple
import uuid
# front-ending
import streamlit as st
import tempfile
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler
# RAG components
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.agents import create_react_agent, AgentExecutor
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler
from langchain_core import prompts
from langchain_core.runnables import Runnable
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory, RedisChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader, UnstructuredPowerPointLoader, UnstructuredHTMLLoader, UnstructuredCSVLoader,UnstructuredMarkdownLoader, UnstructuredImageLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import docx2txt
import time
from langchain.schema import Document
st.set_page_config(page_title="Agent ", layout="wide")
st.title("📚 RAG Agent(支持 PDF / DOCX / TXT / DOC上传与问答)")
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "session_store" not in st.session_state:
    st.session_state.session_store = {}
# Load environment variables
load_dotenv()
if not os.getenv("DEEPSEEK_API_KEY"):
    os.environ["DEEPSEEK_API_KEY"] = getpass.getpass("Enter your DeepSeek API key: ")
# --- 常量 ---
DATA_DIR = "./data"
VECTOR_DB_PATH = "./vector_db"
# --- 初始化目录 ---
os.makedirs(DATA_DIR, exist_ok=True)

# --- 初始化 Embedding 和 Text Splitter ---
embedder = OllamaEmbeddings(model="nomic-embed-text")
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

# --- 初始化 LLM ---
llm = ChatDeepSeek(
    model="deepseek-chat",
    temperature=0,      # Lower temperature for more deterministic responses
    max_tokens=None,    # No limit on response length
    timeout=None,       # No timeout
    max_retries=2,      # Retry failed requests twice
    streaming=True      # Enable streaming for real-time responses
)
parser = StrOutputParser()

# System prompt template defining the AI's role and capabilities
SYSTEM_PROMPT = """
You are a {job}, specialized in {skills}.
When answering questions:
1. First consult the provided context fro.m the knowledge base
2. Then consider the conversation history
3. Finally provide a comprehensive answer
"""

# Main chat prompt combining system instructions, history and user input
prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="history"),  # Dynamic history insertion
    ("human", "{input}")                          # User input placeholder
])

# Basic chain without history
base_chain = prompt | llm | parser

# Session store for maintaining conversation history

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """Retrieve or create chat history for a given session ID"""
    if session_id not in st.session_state.session_store:
        st.session_state.session_store[session_id] = ChatMessageHistory()
    return st.session_state.session_store[session_id]

# Chain enhanced with message history capability
chat_chain = RunnableWithMessageHistory(
    base_chain,
    get_session_history,
    input_messages_key="input",      # Key for user input in the prompt
    history_messages_key="history"   # Key for history in the prompt
)
class VectorDBManager:
    def __init__(self, db_path="./vector_db"):
        self.db_path = db_path
        self.vector_db = None
        self.load_db()

    def load_db(self):
        """加载现有的向量数据库"""
        if os.path.exists(self.db_path):
            try:
                # 向量库加载到内存中
                self.vector_db = FAISS.load_local(
                    self.db_path,
                    embedder,
                    allow_dangerous_deserialization=True
                )
                st.info("✅ 已加载现有向量数据库")
                print("✅ 已加载现有向量数据库")
                # 向量库保存到文件里
                self.save_db()
            except Exception as e:
                st.warning(f"⚠️ 向量数据库为空: {e}")
                print(f"⚠️ 向量数据库为空: {e}")
                self.vector_db = None

    def process_uploaded_file(self, file: UploadFile) -> Document:
        """加载上传的文件到并返回文档块"""
        try:
            # 创建临时文件(不选择存入data)
            temp_dir = "./temp_uploads"
            os.makedirs(temp_dir, exist_ok=True)
            file_path = f"{temp_dir}/{file.name}"
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())

            # 根据文件类型选择加载器
            ext = os.path.splitext(file.name)[1].lower()
            loaders = {
                '.pdf': PyPDFLoader,
                '.docx': Docx2txtLoader,
                '.doc': Docx2txtLoader,
                '.txt': TextLoader,
                '.pptx': UnstructuredPowerPointLoader,
                '.ppt': UnstructuredPowerPointLoader,
                '.html': UnstructuredHTMLLoader,
                '.htm': UnstructuredHTMLLoader,
                '.csv': UnstructuredCSVLoader,
                '.md': UnstructuredMarkdownLoader,
                '.jpg': UnstructuredImageLoader,
                '.jpeg': UnstructuredImageLoader,
                '.png': UnstructuredImageLoader
            }

            if ext not in loaders:
                raise ValueError(f"不支持的文件类型: {ext}")

            loader = loaders[ext](file_path)
            docs = loader.load()
            splits = text_splitter.split_documents(docs)

            # 清理临时文件(用完就弃掉)
            os.remove(file_path)
            return splits

        except Exception as e:
            print(f"文件处理错误: {e}")
            raise

    def add_documents(self, documents: List[Document]):
        """向向量数据库添加新文档"""
        if self.vector_db is None:
            self.vector_db = FAISS.from_documents(
                documents=documents,
                embedding=embedder
            )
        else:
            self.vector_db.add_documents(documents)
        self.save_db()

    def save_db(self):
        """保存向量数据库"""
        if self.vector_db:
            self.vector_db.save_local(VECTOR_DB_PATH)
            st.info(f"✅ 向量数据库已保存{VECTOR_DB_PATH}")
            print(f"✅ 向量数据库已保存{VECTOR_DB_PATH}")
    def similarity_search(self, query: str, k: int = 3):
        if self.vector_db:
            return self.vector_db.similarity_search(query, k)
        return []
    def doc_count(self) -> int:
        if self.vector_db:
            # FAISS的index.ntotal表示存储的向量数量
            return self.vector_db.index.ntotal
        return 0
# 初始化向量数据库管理器,加载现有的向量库
vector_db_manager = VectorDBManager()
class RagRequest(BaseModel):
    """Pydantic model for RAG API request"""
    question: str
    session_id: str = "default"  # Default session ID if not provided
# --- Streamlit UI ---

with st.sidebar:
    st.header("📄 上传文档(支持 pdf/docx/txt)")
    uploaded_files = st.file_uploader(
    "上传文件",
    type=["pdf", "docx", "doc", "txt", "pptx", "ppt", "html", "htm", "csv", "md", "jpg", "jpeg", "png"],
    accept_multiple_files=True
)

    if st.button("📥 上传并重建向量库"):
        if uploaded_files:
            documents = []
            for file in uploaded_files:
                save_path = os.path.join(DATA_DIR, file.name)
                documents += vector_db_manager.process_uploaded_file(file)
                with open(save_path, "wb") as f:
                    f.write(file.getbuffer())
                st.info(f"{file.name} 已经保存至 {save_path}")
            if documents:
                vector_db_manager.add_documents(documents)
                vector_db_manager.load_db()
        else:
            st.warning("请先上传至少一个文档文件")

    if st.button("🧹 清空聊天历史"):
        st.session_state.messages = []
        st.session_state.session_store = {}
        st.rerun()
    st.markdown(f"**向量数据库中文档块数量:** {vector_db_manager.doc_count()}")

# 展示聊天记录
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 用户输入问题(input -> markdown处理 -> message)
if prompt := st.chat_input("请输入你的问题..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 从向量库搜索相关文档
    docs = vector_db_manager.similarity_search(prompt, k=3)
    context = "\n\n".join([doc.page_content for doc in docs])
    # 生成回答
    response = chat_chain.stream(
        input = {
        "job": "RAG Assistant",
        "skills": "文档理解与综合回答",
        "input": f"Context:\n{context}\n\nQuestion: {prompt}"
    }, config={"configurable": {"session_id": st.session_state.session_id}})

    with st.chat_message("assistant"):
        placeholder = st.empty()
        response_text = ""
        for chunk in response:
            response_text += chunk
            placeholder.markdown(response_text + "▌")
            time.sleep(0.02)
        placeholder.markdown(response_text)

    st.session_state.messages.append({"role": "assistant", "content": response_text})
