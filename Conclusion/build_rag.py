from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings

# 加载文档（PDF/TXT等）
loader = DirectoryLoader("./data/", glob="**/*.txt")
docs = loader.load()

# 分割文本
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
splits = text_splitter.split_documents(docs)

# 初始化Ollama Embedding模型
embedder = OllamaEmbeddings(model="nomic-embed-text")  # 或 "deepseek-r1"

# 生成向量库并保存
vector_db = FAISS.from_documents(splits, embedder)
vector_db.save_local("./vector_db")  # 本地存储
# 检验
'''
query = "产品型号是什么"
similar_docs = vector_db.similarity_search(query, k=3)
print([doc.page_content for doc in similar_docs])

'''
