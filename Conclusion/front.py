import os
import uuid
import time
import asyncio
import tempfile
from typing import List

import streamlit as st
from fastapi import UploadFile
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_deepseek import ChatDeepSeek

# --- 常量 ---
DATA_DIR = "./data"
VECTOR_DB_PATH = "./vector_db"

# --- 初始化目录 ---
os.makedirs(DATA_DIR, exist_ok=True)

# --- 初始化 Embedding 和 Text Splitter ---
embedder = OllamaEmbeddings(model="nomic-embed-text")
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

# --- 初始化 LLM ---
llm = ChatDeepSeek(model="deepseek-chat", temperature=0, streaming=True)
parser = StrOutputParser()

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

# --- 会话上下文存储 ---
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

# --- 向量库管理 ---
class VectorDBManager:
    def __init__(self):
        self.vector_db = None
        self.load_db()

    def load_db(self):
        if os.path.exists(VECTOR_DB_PATH):
            self.vector_db = FAISS.load_local(
                VECTOR_DB_PATH,
                embedder,
                allow_dangerous_deserialization=True
            )

    def save_db(self):
        if self.vector_db:
            self.vector_db.save_local(VECTOR_DB_PATH)

    def rebuild_from_data_dir(self):
        files = [os.path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR)
                 if os.path.isfile(os.path.join(DATA_DIR, f)) and os.path.splitext(f)[1].lower() in ['.pdf', '.docx', '.txt']]
        all_docs = []
        for file_path in files:
            ext = os.path.splitext(file_path)[1].lower()
            loaders = {
                '.pdf': PyPDFLoader,
                '.docx': Docx2txtLoader,
                '.txt': TextLoader
            }
            loader = loaders.get(ext)
            if not loader:
                continue
            try:
                docs = loader(file_path).load()
                splits = text_splitter.split_documents(docs)
                all_docs.extend(splits)
            except Exception as e:
                st.warning(f"加载文件失败 {file_path}: {e}")

        if all_docs:
            self.vector_db = FAISS.from_documents(all_docs, embedder)
            self.save_db()
            st.success(f"向量库已更新，包含文档数量: {len(all_docs)}")
        else:
            st.info("没有找到支持的文档文件，向量库未更新。")

    def similarity_search(self, query: str, k: int = 3):
        if self.vector_db:
            return self.vector_db.similarity_search(query, k)
        return []

vector_db_manager = VectorDBManager()

# --- Streamlit UI ---
st.set_page_config(page_title="RAG Agent with Docx Support", layout="wide")
st.title("📚 RAG Agent（支持 PDF / DOCX / TXT 上传与问答）")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

with st.sidebar:
    st.header("📄 上传文档（支持 pdf/docx/txt）")
    uploaded_files = st.file_uploader("上传文件", type=["pdf", "docx", "txt"], accept_multiple_files=True)

    if st.button("📥 上传并重建向量库"):
        if uploaded_files:
            for file in uploaded_files:
                save_path = os.path.join(DATA_DIR, file.name)
                with open(save_path, "wb") as f:
                    f.write(file.getbuffer())
            vector_db_manager.rebuild_from_data_dir()
        else:
            st.warning("请先上传至少一个文档文件")

    if st.button("🧹 清空聊天历史"):
        st.session_state.messages = []
        st.experimental_rerun()

# 展示聊天记录
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 用户输入问题
if prompt := st.chat_input("请输入你的问题..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 从向量库搜索相关文档
    docs = vector_db_manager.similarity_search(prompt, k=3)
    context = "\n\n".join([doc.page_content for doc in docs])

    # 生成回答
    response = chat_chain.stream({
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
