"""
This file is for creating RAG using llama and Open Source Embeddings
"""
import os
import ollama
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain.schema import Document
from langchain.memory import ConversationBufferMemory
from langchain.chains import RetrievalQA
from langchain_huggingface import HuggingFaceEmbeddings # offline - open source

MODEL = 'llama3.2:1b'

# Set our paths
ROOT = Path(__file__).parent
DOCS_DIR = ROOT / "knowledge-base/projects"
CHROMA_DB = ROOT / "chroma_db" 

# Instantiate our local embedder
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Instantia chroma vector store 
if CHROMA_DB.exists() and any(CHROMA_DB.iterdir()):
    vector_store = Chroma(persist_directory=str(CHROMA_DB), embedding_function=embeddings)
    print("Loaded existing Chroma DB")
else:
    print("Creating new Chroma DB")
    loader = DirectoryLoader(str(DOCS_DIR), glob="**/*.pdf")
    docs = loader.load()
    # Chunk the data
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)
    # Build the DB
    vector_store = Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=str(CHROMA_DB))
    print(f'Vector store created with {len(chunks)} chunks')

collection = vector_store._collection
count = collection.count()

# (b) Rough similarity test
query = "Reference Text"
results = vector_store.similarity_search(query, k=3)
print("\nTop 3 chunks for:", query)
for i, doc in enumerate(results, 1):
    # each doc is a langchain.schema.Document
    text_snip = doc.page_content[:200].replace("\n"," ")
    print(f"  [{i}] …{text_snip!r}…")