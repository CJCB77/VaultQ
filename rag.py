"""
This file is for creating RAG using llama and Open Source Embeddings
"""
from pathlib import Path
from dotenv import load_dotenv
import os

from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_huggingface import HuggingFaceEmbeddings # offline - open source
from langchain_ollama.llms import OllamaLLM
# from langchain_openai import ChatOpenAI

load_dotenv(override=True)

MODEL = 'qwen3:1.7b'
OPENAI_MODEL = 'o4-mini'
# Set our paths
ROOT = Path(__file__).parent
DOCS_DIR = ROOT / "knowledge-base/projects"
CHROMA_DB = ROOT / "chroma_db" 

os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', 'your-key-if-not-using-env')

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

# Instantiate llama chat
llm = OllamaLLM(model=MODEL)
# openai_llm = ChatOpenAI(model=OPENAI_MODEL)

# Set up the conversation memory for the chat
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# The retiever is an abstraction over the VectorStore that will be used during RAG
retriever = vector_store.as_retriever()

conversation_chain = ConversationalRetrievalChain.from_llm(
    llm=llm, 
    retriever=retriever, 
    memory=memory
)

query = "What is the difference between a truthfulness error and a instruction following error in the Cypher project?"
result = conversation_chain.invoke({'question': query})
print(result["answer"])