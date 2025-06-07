from dotenv import load_dotenv
import os
import asyncio
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import AsyncGenerator, List, Union
import uuid

# RAG components
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader

# Load environment variables
load_dotenv()

# Initialize embedding model
embedder = OllamaEmbeddings(model="nomic-embed-text")
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)

class VectorDBManager:
    """管理向量数据库的类"""
    def __init__(self, db_path="./vector_db"):
        self.db_path = db_path
        self.vector_db = None
        self.load_db()

    def load_db(self):
        """加载现有的向量数据库"""
        if os.path.exists(self.db_path):
            try:
                self.vector_db = FAISS.load_local(
                    self.db_path,
                    embedder,
                    allow_dangerous_deserialization=True
                )
                print("✅ 已加载现有向量数据库")
            except Exception as e:
                print(f"⚠️ 加载向量数据库失败: {e}")
                self.vector_db = None

    def process_uploaded_file(self, file: UploadFile) -> List[str]:
        """处理上传的文件并返回文档块"""
        try:
            # 创建临时文件
            temp_dir = "./temp_uploads"
            os.makedirs(temp_dir, exist_ok=True)
            file_path = f"{temp_dir}/{file.filename}"

            with open(file_path, "wb") as f:
                f.write(file.file.read())

            # 根据文件类型选择加载器
            ext = os.path.splitext(file.filename)[1].lower()
            loaders = {
                '.pdf': PyPDFLoader,
                '.docx': Docx2txtLoader,
                '.txt': TextLoader
            }

            if ext not in loaders:
                raise ValueError(f"不支持的文件类型: {ext}")

            loader = loaders[ext](file_path)
            docs = loader.load()
            splits = text_splitter.split_documents(docs)

            # 清理临时文件
            os.remove(file_path)

            return splits

        except Exception as e:
            print(f"文件处理错误: {e}")
            raise

    def add_documents(self, documents: List[str]):
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
            self.vector_db.save_local(self.db_path)
            print("✅ 向量数据库已更新")

# 初始化向量数据库管理器
vector_db_manager = VectorDBManager()

app = FastAPI()

class ChatRequest(BaseModel):
    input: str
    session_id: str = "default"

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """处理普通聊天请求"""
    # ... (原有的聊天逻辑)
    pass

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """处理文件上传并嵌入到向量数据库"""
    try:
        documents = vector_db_manager.process_uploaded_file(file)
        vector_db_manager.add_documents(documents)

        return {
            "status": "success",
            "message": f"文件 '{file.filename}' 已成功处理并添加到 知识库",
            "document_count": len(documents)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

def interactive_chat():
    """交互式聊天界面，支持@file命令"""
    session_id = str(uuid.uuid4())
    print("智能助手已启动 (输入 '@file 文件路径' 上传文件，或输入 'exit' 退出)")

    while True:
        user_input = input("你: ").strip()

        if user_input.lower() == 'exit':
            break

        # 处理@file命令
        if user_input.startswith("@file"):
            file_path = user_input[5:].strip()
            if not file_path:
                print("⚠️ 请指定文件路径，例如: @file /path/to/document.pdf")
                continue

            try:
                # 模拟文件上传
                with open(file_path, "rb") as f:
                    fake_file = UploadFile(
                        filename=os.path.basename(file_path),
                        file=f
                    )
                    result = asyncio.run(upload_file(fake_file))
                    print(result["message"])
            except Exception as e:
                print(f"❌ 文件处理失败: {e}")
            continue

        # 普通聊天处理
        # ... (原有的聊天逻辑)

if __name__ == "__main__":
    interactive_chat()