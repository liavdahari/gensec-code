"""SmartNotebook RAG: A LangChain-Powered NotebookLM-like Research Assistant.

This application augments standard LangChain RAG with two core features:
1. Feature 1 - Custom Document Loader:
   A custom loader (ResearchNoteLoader) extending LangChain's BaseLoader that parses
   both structured JSON datasets (tabular records, airports, economic data) and
   Markdown research notes with YAML frontmatter.
2. Feature 2 - Grounded Q&A with Strict In-Line Citations:
   A NotebookLM-style question-answering system strictly grounded in retrieved
   context that appends in-line bracketed citations ([Source: filename]) to every claim
   and displays a verified list of cited sources.

Course: COT4930 - Generative AI Security
Student: Liav Dahari
FAU ID: Z23815316
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import readline

try:
    from langchain_chroma import Chroma
except ImportError:
    try:
        from langchain_community.vectorstores import Chroma
    except ImportError:
        raise ImportError(
            "Chroma vectorstore is not installed. Please install it using:\n"
            "  pip install langchain-chroma\n"
            "or run: pip install -r requirements.txt"
        )

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Load local environment variables from .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Feature 1: Custom Document Loader extending LangChain BaseLoader
from notebook_loader import ResearchNoteLoader

# Environment configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "gensec-liav-dahari")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
MODEL_NAME = os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")
VECTORSTORE_DIR = os.getenv("CHROMA_PERSIST_DIR", "./rag_data/.chromadb")


class NotebookRAGService:
    """Core RAG engine implementing the two primary homework features.

    Feature 1: Custom document loading for JSON datasets and structured notes.
    Feature 2: Grounded retrieval with in-line source citations.
    """

    def __init__(
        self,
        persist_directory: str = VECTORSTORE_DIR,
        project_id: str = PROJECT_ID,
        location: str = LOCATION,
        model_name: str = MODEL_NAME,
    ) -> None:
        """Initialize the NotebookRAGService with models and vector database.

        Args:
            persist_directory: Filesystem path to the Chroma database directory.
            project_id: Google Cloud / Vertex AI Project ID.
            location: Google Cloud region for Vertex AI endpoints.
            model_name: Gemini model name for question-answering.
        """
        self.persist_directory = persist_directory
        self.project_id = project_id
        self.location = location
        self.model_name = model_name

        # Configure embedding function
        if os.getenv("GOOGLE_API_KEY"):
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            self.embedding_function = GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004"
            )
        else:
            self.embedding_function = VertexAIEmbeddings(
                model_name="text-embedding-004",
                project=self.project_id,
                location=self.location,
            )

        # Configure Gemini chat model
        llm_kwargs: Dict[str, Any] = {
            "model": self.model_name,
            "temperature": 0.2,
        }
        if not os.getenv("GOOGLE_API_KEY"):
            llm_kwargs["project"] = self.project_id
            llm_kwargs["location"] = self.location

        self.llm = ChatGoogleGenerativeAI(**llm_kwargs)

        # Connect to Chroma vectorstore
        self.vectorstore = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embedding_function,
        )
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 4})

        # Feature 2: Strict grounding and citation prompt template
        self.qa_prompt = ChatPromptTemplate.from_template(
            """You are SmartNotebook, an expert AI research assistant inspired by NotebookLM.
Answer the user's question STRICTLY based on the provided context passages below.
For every claim or factual point you make, cite the corresponding source in brackets (e.g. [Source: filename or title]).
If the provided context does not contain enough information to answer, state clearly: "I cannot find this information in your notebook sources."
Do not make assumptions or extrapolate beyond what is documented.

Question: {question}

Context Passages:
{context}

Answer with in-line citations:"""
        )

    def get_indexed_sources(self) -> List[str]:
        """Retrieve a sorted list of unique source identifiers indexed in Chroma.

        Returns:
            List of unique document source paths or URLs.
        """
        try:
            metadatas = self.vectorstore.get().get("metadatas", [])
            sources = set()
            for meta in metadatas:
                if meta and "source" in meta:
                    sources.add(str(meta["source"]))
            return sorted(list(sources))
        except Exception:
            return []

    def answer_query(self, question: str) -> Dict[str, Any]:
        """Answer a query with strictly grounded in-line citations (Feature 2).

        Args:
            question: The user query string.

        Returns:
            Dictionary containing:
                - 'answer': Generated answer string with in-line citations.
                - 'sources': List of unique source names cited.
                - 'docs': List of matched Document objects.
        """
        matched_docs = self.retriever.invoke(question)
        if not matched_docs:
            return {
                "answer": "No relevant documents found in the database. Please load documents first.",
                "sources": [],
                "docs": [],
            }

        # Format context with numbered source citations
        context_blocks = []
        for i, doc in enumerate(matched_docs, start=1):
            src = doc.metadata.get("source", f"Document-{i}")
            title = doc.metadata.get("title", "")
            header = f"[Source {i}: {title or src}]"
            context_blocks.append(f"{header}\n{doc.page_content}")

        context_str = "\n\n".join(context_blocks)

        chain = self.qa_prompt | self.llm | StrOutputParser()
        answer = chain.invoke({"question": question, "context": context_str})

        sources = [doc.metadata.get("source", "Unknown") for doc in matched_docs]
        unique_sources = sorted(list(set(sources)))

        return {
            "answer": answer,
            "sources": unique_sources,
            "docs": matched_docs,
        }

    def ingest_custom_data(self, path: str) -> int:
        """Ingest documents or datasets using the custom loader (Feature 1).

        Args:
            path: Directory or file path to ingest.

        Returns:
            Number of chunks added to the vector store.
        """
        loader = ResearchNoteLoader(path)
        docs = loader.load()
        if not docs:
            return 0

        splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150)
        splits = splitter.split_documents(docs)

        # Safe batching to respect API token quotas
        batch_size = 20
        for i in range(0, len(splits), batch_size):
            self.vectorstore.add_documents(splits[i : i + batch_size])

        return len(splits)


# =====================================================================
# Interactive Command Line Interface (CLI)
# =====================================================================
def run_cli() -> None:
    """Run the interactive NotebookLM-style CLI interface."""
    service = NotebookRAGService()

    banner = """
========================================================================
       📓 SmartNotebook RAG: NotebookLM-like Research Assistant
========================================================================
  Features:
    [Feature 1] Custom Document Loader (BaseLoader for JSON & Notes)
    [Feature 2] Grounded Q&A with Strict In-Line Citations
------------------------------------------------------------------------
  Commands:
    /help         - Show this command reference
    /sources      - List all indexed documents and datasets
    /load-json    - Ingest structured JSON datasets via custom loader
    /load-notes   - Ingest custom research notes via custom loader
    /exit         - Quit the application
------------------------------------------------------------------------
  Type any research question below to query with strict in-line citations.
========================================================================
"""
    print(banner)

    sources = service.get_indexed_sources()
    if sources:
        print(f"Loaded {len(sources)} unique document sources:")
        for s in sources[:6]:
            print(f"  • {s}")
        if len(sources) > 6:
            print(f"  ... and {len(sources) - 6} more")
    else:
        print("Note: Vector database is currently empty. Run 07_rag_loaddb.py, /load-json, or /load-notes to populate.")

    while True:
        try:
            line = input("\nnotebook>> ").strip()
            if not line:
                continue

            if line.lower() in ("/exit", "exit", "quit"):
                print("Goodbye!")
                break

            elif line.lower() == "/help":
                print(banner)

            elif line.lower() == "/sources":
                sources = service.get_indexed_sources()
                print(f"\nIndexed Sources ({len(sources)} total):")
                for s in sources:
                    print(f"  • {s}")

            elif line.lower() == "/load-json":
                json_dir = "rag_data/JSON"
                print(f"[Feature 1] Ingesting structured JSON datasets from: {json_dir}...")
                count = service.ingest_custom_data(json_dir)
                print(f"✅ Successfully ingested and indexed {count} dataset chunks!")

            elif line.lower() == "/load-notes":
                notes_dir = "rag_data/notes"
                print(f"[Feature 1] Ingesting structured notes from: {notes_dir}...")
                count = service.ingest_custom_data(notes_dir)
                print(f"✅ Successfully ingested and indexed {count} note chunks!")

            else:
                # Feature 2: Question-Answering with in-line citations
                print("\n[Feature 2] Retrieving grounded context and generating cited answer...")
                result = service.answer_query(line)
                print("\n" + result["answer"])
                print("\n--- Sources Cited ---")
                for s in result["sources"]:
                    print(f"  [{s}]")

        except (KeyboardInterrupt, EOFError):
            print("\nExiting SmartNotebook.")
            break


# =====================================================================
# Chainlit Web UI Mode
# =====================================================================
try:
    import chainlit as cl

    @cl.on_chat_start
    async def on_chat_start() -> None:
        """Initialize Chainlit session with welcoming message and source summary."""
        service = NotebookRAGService()
        cl.user_session.set("service", service)

        sources = service.get_indexed_sources()
        source_list_str = "\n".join([f"- `{s}`" for s in sources[:8]])
        if len(sources) > 8:
            source_list_str += f"\n- *...and {len(sources) - 8} more*"

        welcome_md = f"""# 📓 Welcome to SmartNotebook RAG!
*A NotebookLM-like research assistant with two core custom features:*

1. **Feature 1: Custom Document Loader** (`ResearchNoteLoader` extending `BaseLoader`) for JSON datasets and Markdown research notes.
2. **Feature 2: Grounded Q&A with Strict In-Line Citations** (`[Source: filename]`).

### **Indexed Sources ({len(sources)})**:
{source_list_str or '*(Database empty. Run 07_rag_loaddb.py to index documents)*'}

### **Commands**:
- Ask any question to get grounded answers with in-line citations.
- `/sources` - List all indexed document paths.
- `/load-json` - Index JSON datasets from `rag_data/JSON`.
- `/load-notes` - Index research notes from `rag_data/notes`.
"""
        await cl.Message(content=welcome_md).send()

    @cl.on_message
    async def on_message(message: cl.Message) -> None:
        """Handle incoming messages in Chainlit."""
        service: NotebookRAGService = cl.user_session.get("service")
        user_text = message.content.strip()

        if user_text.lower() == "/sources":
            sources = service.get_indexed_sources()
            resp = "**Indexed Sources:**\n" + "\n".join([f"- `{s}`" for s in sources])
            await cl.Message(content=resp).send()

        elif user_text.lower() == "/load-json":
            count = service.ingest_custom_data("rag_data/JSON")
            await cl.Message(content=f"✅ Ingested {count} dataset chunks from `rag_data/JSON` using custom loader.").send()

        elif user_text.lower() == "/load-notes":
            count = service.ingest_custom_data("rag_data/notes")
            await cl.Message(content=f"✅ Ingested {count} chunks from `rag_data/notes` using custom loader.").send()

        else:
            result = service.answer_query(user_text)
            answer_text = result["answer"]
            if result["sources"]:
                answer_text += "\n\n**Sources Cited:**\n" + "\n".join([f"- `{s}`" for s in result["sources"]])
            await cl.Message(content=answer_text).send()

except ImportError:
    pass


if __name__ == "__main__":
    run_cli()
