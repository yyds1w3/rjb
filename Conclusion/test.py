# 完整示例：基于Streamlit + LangChain + DeepSeek实现多格式文档RAG聊天

import os
import time
import uuid
import getpass
import streamlit as st
from dotenv import load_dotenv
from typing import List
from fastapi import UploadFile
from langchain.schema import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_deepseek import ChatDeepSeek
from langchain_ollama import OllamaEmbeddings

# 导入不同格式文档加载器
from langchain_community.document_loaders import (
    PyPDFLoader, Docx2txtLoader, TextLoader,
    UnstructuredPowerPointLoader, UnstructuredHTMLLoader,
    UnstructuredCSVLoader, UnstructuredMarkdownLoader,
    UnstructuredImageLoader
)

# ========== 环境和目录初始化 ==========
st.set_page_config(page_title="📚 RAG Agent", layout="wide")
st.title("📚 RAG Agent (支持 PDF / DOCX / TXT / PPT 等上传与问答)")

DATA_DIR = "./data"
VECTOR_DB_PATH = "./vector_db"
TEMP_UPLOAD_DIR = "./temp_uploads"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)

# 加载环境变量，DEEPSEEK_API_KEY
load_dotenv()
if not os.getenv("DEEPSEEK_API_KEY"):
    os.environ["DEEPSEEK_API_KEY"] = getpass.getpass("请输入你的 DeepSeek API Key: ")

# ========== 全局组件初始化 ==========
embedder = OllamaEmbeddings(model="nomic-embed-text")
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

llm = ChatDeepSeek(
    model="deepseek-chat",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    streaming=True
)
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

# 用于保存不同会话的聊天历史
if "session_store" not in st.session_state:
    st.session_state.session_store = {}

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

# ========== 向量数据库管理 ==========
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
                print("✅ 已加载现有向量数据库")
            except Exception as e:
                st.warning(f"⚠️ 向量数据库加载失败: {e}")
                print(f"⚠️ 向量数据库加载失败: {e}")
                self.vector_db = None

    def process_uploaded_file(self, file: UploadFile) -> List[Document]:
        try:
            file_path = os.path.join(TEMP_UPLOAD_DIR, file.name)
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
                '.jpg': UnstructuredImageLoader,
                '.jpeg': UnstructuredImageLoader,
                '.png': UnstructuredImageLoader
            }

            if ext not in loaders:
                raise ValueError(f"不支持的文件类型: {ext}")

            loader = loaders[ext](file_path)
            docs = loader.load()
            splits = text_splitter.split_documents(docs)
            os.remove(file_path)
            return splits

        except Exception as e:
            st.error(f"文件处理错误: {e}")
            print(f"文件处理错误: {e}")
            return []

    def add_documents(self, documents: List[Document]):
        if not documents:
            st.warning("⚠️ 没有可添加的文档")
            return
        try:
            if self.vector_db is None:
                self.vector_db = FAISS.from_documents(documents, embedder)
            else:
                self.vector_db.add_documents(documents)
            self.save_db()
        except Exception as e:
            st.error(f"添加文档到向量数据库出错: {e}")
            print(f"添加文档出错: {e}")

    def save_db(self):
        if self.vector_db:
            self.vector_db.save_local(self.db_path)
            st.info(f"✅ 向量数据库已保存到 {self.db_path}")
            print(f"✅ 向量数据库已保存到 {self.db_path}")

    def similarity_search(self, query: str, k: int = 3):
        if self.vector_db:
            return self.vector_db.similarity_search(query, k)
        return []
    def doc_count(self) -> int:
        if self.vector_db:
            # FAISS的index.ntotal表示存储的向量数量
            return self.vector_db.index.ntotal
        return 0

vector_db_manager = VectorDBManager()

# ========== Streamlit 界面 ==========
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

with st.sidebar:
    st.header("📄 上传文档(支持多格式)")
    uploaded_files = st.file_uploader(
        "选择文件",
        type=["pdf", "docx", "doc", "txt", "pptx", "ppt", "html", "htm", "csv", "md", "jpg", "jpeg", "png"],
        accept_multiple_files=True
    )

    if st.button("📥 上传并重建向量库"):
        if uploaded_files:
            documents = []
            for file in uploaded_files:
                save_path = os.path.join(DATA_DIR, file.name)
                with open(save_path, "wb") as f:
                    f.write(file.getbuffer())
                st.info(f"{file.name} 已保存至 {save_path}")

                docs = vector_db_manager.process_uploaded_file(file)
                documents.extend(docs)

            if documents:
                vector_db_manager.add_documents(documents)
                st.success("向量库已更新")
            else:
                st.warning("未成功解析任何文档")
        else:
            st.warning("请先上传至少一个文档文件")

    if st.button("🧹 清空聊天历史"):
        st.session_state.messages = []
        st.session_state.session_store = {}
        st.rerun()
    st.markdown(f"**向量数据库中文档块数量:** {vector_db_manager.doc_count()}")

# 显示聊天历史
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 用户输入框
if prompt := st.chat_input("请输入你的问题..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 搜索相关文档上下文
    docs = vector_db_manager.similarity_search(prompt, k=3)
    context = "\n\n".join([doc.page_content for doc in docs])

    # 构建输入给模型
    inputs = {
        "job": "RAG Assistant",
        "skills": "文档理解与综合回答",
        "input": f"Context:\n{context}\n\nQuestion: {prompt}"
    }

    response = chat_chain.stream(
        input=inputs,
        config={"configurable": {"session_id": st.session_state.session_id}}
    )

    with st.chat_message("assistant"):
        placeholder = st.empty()
        response_text = ""
        for chunk in response:
            response_text += chunk
            placeholder.markdown(response_text + "▌")
            time.sleep(0.02)
        placeholder.markdown(response_text)

    st.session_state.messages.append({"role": "assistant", "content": response_text})
