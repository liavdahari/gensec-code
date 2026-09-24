# Generative Security (COT4930) - Coursework Repository

**Student:** Liav Dahari (FAU ID: Z23815316)  
**Institution:** Florida Atlantic University  
**Course:** COT4930 - Security (System) Engineering with Generative AI  

---

## Repository Structure

```text
gensec-code/
├── README.md
├── .gitignore
└── HW2/                          # Homework 2: LangChain RAG Application
    ├── app.py                    # SmartNotebook RAG Application (CLI & Chainlit)
    ├── notebook_loader.py        # Feature 1: Custom Document Loader (BaseLoader)
    ├── test_notebook_loader.py   # Automated unit tests for Feature 1
    ├── 07_rag_loaddb.py          # Vector DB loader with Vertex AI batching & custom loader
    ├── 08_rag_docsearch.py       # Document similarity search script
    ├── 09_rag_query.py           # Grounded CLI query script
    ├── 10_chainlit_rag_query.py  # Chainlit web chat interface
    ├── wikipedia_loader.py       # Rate-limited Wikipedia loader
    ├── test_wikipedia_loader.py  # Wikipedia loader unit tests
    ├── requirements.txt          # Python dependencies
    ├── screencast_url.txt        # YouTube screencast URL placeholder
    ├── hw2-Z23815316.docx        # Assignment submission document
    └── rag_data/                 # Multimodal datasets
        ├── JSON/                 # Tabular datasets (airports, S&P 500, inflation, crops)
        ├── notes/                # Markdown research notes with YAML frontmatter
        ├── txt/                  # Plain text documents
        ├── pdf/                  # PDF documents
        ├── docx/                 # Word documents
        ├── csv/                  # CSV spreadsheets
        └── md/                   # Markdown guides
```

---

## Homework 2: SmartNotebook RAG Application

SmartNotebook RAG augments a LangChain retrieval-augmented generation pipeline with two core features:

1. **Feature 1 - Custom Document Loader (`ResearchNoteLoader`)**:
   - Subclasses LangChain's `BaseLoader` in `notebook_loader.py`.
   - Ingests structured JSON datasets (records, tables, stats) and Markdown research notes with YAML frontmatter metadata.
   - Tested by `test_notebook_loader.py`.

2. **Feature 2 - Grounded Q&A with Strict In-Line Citations**:
   - Implemented in `app.py`.
   - Restricts LLM responses strictly to retrieved document context.
   - Attaches verified in-line citations `[Source: filename]` to every claim and displays a verified sources list.

---

## Setup and Execution

### 1. Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv env
source env/bin/activate

# Install required packages
pip install -r HW2/requirements.txt
```

### 2. Run the Application
```bash
cd HW2

# Run interactive CLI
python3 app.py

# Or launch Chainlit web UI
chainlit run app.py
```
