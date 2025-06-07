from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader, Docx2txtLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from typing import List, Union
import os

def loader_documents(folder_path: str) -> List[Union[str, Exception]]:
    """
    Load documents from a directory with support for multiple file formats (PDF, DOCX, TXT).

    Args:
        folder_path (str): Path to the directory containing documents

    Returns:
        List of loaded documents or error messages
    """
    # Define loaders for different file extensions
    loaders = {
        '.pdf': PyPDFLoader,    # Handles PDF files
        '.docx': Docx2txtLoader, # Handles Word documents
        '.txt': TextLoader      # Handles plain text files
    }

    documents = []

    # Recursively walk through the directory
    for root, _, files in os.walk(folder_path):
        for file in files:
            ext = os.path.splitext(file)[1].lower()  # Get file extension

            if ext in loaders:
                file_path = os.path.join(root, file)
                try:
                    # Initialize appropriate loader for the file type
                    loader = loaders[ext](file_path)
                    # Load and add documents to the list
                    documents.extend(loader.load())
                    print(f"Successfully loaded: {file_path}")  # Log successful loads
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")
                    continue  # Skip to next file if error occurs

    return documents

# Load documents from directory
docs = loader_documents("./data/")  # Replace with your actual path

# Initialize text splitter with optimal parameters for semantic search
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,      # Size of each text chunk (in characters)
    chunk_overlap=50,    # Overlap between chunks for context preservation
    length_function=len, # Function to calculate text length
    is_separator_regex=False  # Whether separators are regular expressions
)

# Split documents into chunks
splits = text_splitter.split_documents(docs)
print(f"Split documents into {len(splits)} chunks")

# Initialize Ollama Embedding model
embedder = OllamaEmbeddings(
    model="nomic-embed-text",  # Alternative: "deepseek-r1"
    temperature=0.1,           # Control randomness (0-1)
)

# Generate and save vector database
vector_db = FAISS.from_documents(
    documents=splits,          # Our chunked documents
    embedding=embedder,        # Embedding model
    normalize_L2=True          # Normalize vectors for better similarity comparison
)

# Save vector store locally
vector_db.save_local(
    folder_path="./vector_db",  # Directory to save index
    index_name="my_faiss_index" # Name of the index file
)

# Test the vector store
query = "产品型号是什么"
similar_docs = vector_db.similarity_search(
    query=query,       # Search query
    k=3,               # Number of results to return
    filter=None        # Optional metadata filter
)

# Print results
print("\nTop 3 most similar documents:")
for i, doc in enumerate(similar_docs, 1):
    print(f"\nDocument {i}:")
    print(doc.page_content)
    print(f"Metadata: {doc.metadata}")  # Show associated metadata