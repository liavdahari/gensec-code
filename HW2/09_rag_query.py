import os
import readline
from langchain_classic import hub
from langchain_text_splitters import RecursiveCharacterTextSplitter
try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_vertexai import VertexAIEmbeddings

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "gensec-liav-dahari")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
MODEL_NAME = os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")

# 1. Chat model configured with project and location
llm = ChatGoogleGenerativeAI(
    model=MODEL_NAME,
    project=PROJECT_ID, 
    location=LOCATION
)

# 2. Embedding model matching 07_rag_loaddb
vectorstore = Chroma(
     persist_directory="./rag_data/.chromadb",
     embedding_function=VertexAIEmbeddings(
         model_name="text-embedding-004", 
         project=PROJECT_ID,
         location=LOCATION
     )
)

retriever = vectorstore.as_retriever()

prompt = ChatPromptTemplate.from_template(
    """You are an assistant for question-answering tasks.
Use the following pieces of retrieved context to answer the question.
If you don't know the answer, just say that you don't know.
Use three sentences maximum and keep the answer concise.

Question: {question}

Context: {context}

Answer:"""
)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

print("Welcome to my RAG application. Ask me a question and I will answer it from the documents in my database shown below")

document_data_sources = set()
for doc_metadata in retriever.vectorstore.get()['metadatas']:
    document_data_sources.add(doc_metadata['source']) 
for doc in document_data_sources:
    print(f"  {doc}")

while True:
    line = input("llm>> ")
    if line:
        result = rag_chain.invoke(line)
        print(result)
    else:
        break
