from fastapi import FastAPI
from pydantic import BaseModel
from langchain_community.vectorstores import FAISS
import os
from fastapi.responses import StreamingResponse  # 关键导入
from langchain_ollama import OllamaEmbeddings
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
import getpass
from langchain_core.prompts import ChatPromptTemplate
import httpx
from typing import AsyncGenerator
import asyncio
load_dotenv()
app = FastAPI()
if not os.getenv("DEEPSEEK_API_KEY"):
    os.environ["DEEPSEEK_API_KEY"] = getpass.getpass("Enter your DeepSeek API key: ")
llm = ChatDeepSeek(
    model="deepseek-chat",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    streaming=True
)

# 加载预存向量库
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
