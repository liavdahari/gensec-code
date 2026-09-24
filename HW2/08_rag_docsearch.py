import os
import readline
try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma
from langchain_google_vertexai import VertexAIEmbeddings

# Configure Google Cloud Project and location from environment variables
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "gensec-liav-dahari")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

# Open the persisted RAG database with the same embedding function used to build it.
vectorstore = Chroma(
    embedding_function=VertexAIEmbeddings(
        model_name="text-embedding-004",
        project=PROJECT_ID,
        location=LOCATION
    ),
    persist_directory="./rag_data/.chromadb"
)

def search_db(query: str):
    """Search the vector database and print the closest matching source.
    
    Args:
        query: Search text to match against the vector store.
    """
    docs = vectorstore.similarity_search(query)
    print(f"Query database for: {query}")
    if docs:
        print(f"Closest document match in database: {docs[0].metadata.get('source', 'Unknown')}, count={len(docs)}")
        print(f"Sample content snippet: {docs[0].page_content[:200]}...")
    else:
        print("No matching documents found")

print("RAG database initialized.")
retriever = vectorstore.as_retriever()

# List indexed sources before accepting search queries.
document_data_sources = set()
try:
    metadatas = retriever.vectorstore.get().get('metadatas', [])
    for doc_metadata in metadatas:
        if doc_metadata and 'source' in doc_metadata:
            document_data_sources.add(doc_metadata['source'])
    for doc in sorted(document_data_sources):
        print(f"  {doc}")
except Exception as e:
    print(f"Note: Vector database not loaded yet or empty: {e}")

print("\nThis program queries documents in the RAG database that are similar to whatever is entered.")
while True:
    try:
        line = input(">> ").strip()
        if line:
            search_db(line)
        else:
            break
    except (EOFError, KeyboardInterrupt):
        break
