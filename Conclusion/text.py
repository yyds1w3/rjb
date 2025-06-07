# -*- coding: utf-8 -*-

from dotenv import load_dotenv
import os
from pathlib import Path
import getpass
import time
import uuid

import streamlit as st
from fastapi import UploadFile

from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_deepseek import ChatDeepSeek
from langchain_core.documents import Document

from PIL import Image
import pytesseract

from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredPowerPointLoader,
    UnstructuredHTMLLoader,
    UnstructuredCSVLoader,
    UnstructuredMarkdownLoader
)

# -------------------- 初始化 --------------------
st.set_page_config(page_title="RAG Agent", layout="wide")
st.title("📚 RAG Agent(支持 PDF / DOCX / TXT / 图片上传与问答)")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "session_store" not in st.session_state:
    st.session_state.session_store = {}

load_dotenv()
if not os.getenv("DEEPSEEK_API_KEY"):
    os.environ["DEEPSEEK_API_KEY"] = getpass.getpass("Enter your DeepSeek API key: ")

DATA_DIR = "./data"
VECTOR_DB_PATH = "./vector_db"
os.makedirs(DATA_DIR, exist_ok=True)

embedder = OllamaEmbeddings(model="nomic-embed-text")
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

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

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in st.session_state.session_store:
        st.session_state.session_store[session_id] = ChatMessageHistory()
    return st.session_state.session_store[session_id]

chat_chain = RunnableWithMessageHistory(
    base_chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history"
)

class SimpleImageLoader:
    def __init__(self, path):
        self.path = path

    def load(self):
        text = pytesseract.image_to_string(Image.open(self.path))
        return [Document(page_content=text)]

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
                st.info("✅ 已加载现有向量数据库")
            except Exception as e:
                st.warning(f"⚠️ 向量数据库为空: {e}")
                self.vector_db = None

    def process_uploaded_file(self, file: UploadFile):
        try:
            temp_dir = "./temp_uploads"
            os.makedirs(temp_dir, exist_ok=True)
            file_path = os.path.join(temp_dir, file.name)
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())

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
                '.jpg': SimpleImageLoader,
                '.jpeg': SimpleImageLoader,
                '.png': SimpleImageLoader
            }

            if ext not in loaders:
                raise ValueError(f"不支持的文件类型: {ext}")

            loader = loaders[ext](file_path)
            docs = loader.load()
            splits = text_splitter.split_documents(docs)

            os.remove(file_path)
            return splits

        except Exception as e:
            import traceback
            traceback.print_exc()
            st.error(f"❌ 文件处理错误: {e}")
            raise

    def add_documents(self, documents):
        if self.vector_db is None:
            self.vector_db = FAISS.from_documents(documents=documents, embedding=embedder)
        else:
            self.vector_db.add_documents(documents)
        self.save_db()

    def save_db(self):
        if self.vector_db:
            self.vector_db.save_local(self.db_path)
            st.info(f"✅ 向量数据库已保存至 {self.db_path}")

    def similarity_search(self, query, k=3):
        if self.vector_db:
            return self.vector_db.similarity_search(query, k)
        return []

vector_db_manager = VectorDBManager()

with st.sidebar:
    st.header("📄 上传文档")
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
                st.info(f"{file.name} 已保存至 {save_path}")
            if documents:
                vector_db_manager.add_documents(documents)
        else:
            st.warning("请先上传至少一个文档文件")

    if st.button("🧹 清空聊天历史"):
        st.session_state.messages = []
        st.session_state.session_store = {}
        st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("请输入你的问题..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    docs = vector_db_manager.similarity_search(prompt, k=3)
    context = "\n\n".join([doc.page_content for doc in docs])

    response = chat_chain.stream(
        input={
            "job": "RAG Assistant",
            "skills": "文档理解与综合回答",
            "input": f"Context:\n{context}\n\nQuestion: {prompt}"
        },
        config={"configurable": {"session_id": st.session_state.session_id}}
    )

    with st.chat_message("assistant"):
        placeholder = st.empty()
        response_text = ""
        for chunk in response:
            response_text += chunk
            placeholder.markdown(response_text + "▌")
            time.sleep(0.005)
        placeholder.markdown(response_text)

    st.session_state.messages.append({"role": "assistant", "content": response_text})
