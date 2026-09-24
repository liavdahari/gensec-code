"""Unit tests for the custom ResearchNoteLoader class."""

import tempfile
from pathlib import Path
from notebook_loader import ResearchNoteLoader


def test_research_note_loader_markdown_frontmatter() -> None:
    """Verify that frontmatter metadata is extracted properly from Markdown files."""
    sample_content = """---
title: "Introduction to RAG Security"
author: "Liav Dahari"
topic: "Generative AI Security"
tags: [rag, security, langchain]
date: "2026-09-23"
---
# Retrieval Augmented Generation (RAG) Security

RAG architectures augment foundation models by grounding queries in external document stores.
Security concerns include prompt injection, vector database poisoning, and unauthorized document access.
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        note_file = Path(tmpdir) / "rag_security_note.md"
        note_file.write_text(sample_content, encoding="utf-8")

        loader = ResearchNoteLoader(note_file)
        docs = loader.load()

        assert len(docs) == 1
        doc = docs[0]
        assert "Retrieval Augmented Generation" in doc.page_content
        assert doc.metadata["title"] == "Introduction to RAG Security"
        assert doc.metadata["author"] == "Liav Dahari"
        assert doc.metadata["topic"] == "Generative AI Security"
        assert doc.metadata["tags"] == ["rag", "security", "langchain"]
        assert doc.metadata["date"] == "2026-09-23"
        assert doc.metadata["loader"] == "ResearchNoteLoader"


def test_research_note_loader_directory_loading() -> None:
    """Verify loading multiple notes from a directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dir_path = Path(tmpdir)
        (dir_path / "note1.md").write_text("---\ntitle: Note 1\n---\nFirst note content.", encoding="utf-8")
        (dir_path / "note2.md").write_text("---\ntitle: Note 2\n---\nSecond note content.", encoding="utf-8")

        loader = ResearchNoteLoader(dir_path)
        docs = loader.load()

        assert len(docs) == 2
        titles = {d.metadata["title"] for d in docs}
        assert "Note 1" in titles
        assert "Note 2" in titles


def test_research_note_loader_json_format() -> None:
    """Verify loading structured JSON notebook exports."""
    json_content = """[
        {"title": "Lesson 1", "content": "Embedding models convert text to vectors.", "topic": "Embeddings"},
        {"title": "Lesson 2", "content": "Vector databases index embeddings for nearest neighbor search.", "topic": "Vector Stores"}
    ]"""
    with tempfile.TemporaryDirectory() as tmpdir:
        json_file = Path(tmpdir) / "notes.json"
        json_file.write_text(json_content, encoding="utf-8")

        loader = ResearchNoteLoader(json_file)
        docs = loader.load()

        assert len(docs) == 2
        assert docs[0].metadata["title"] == "Lesson 1"
        assert docs[1].metadata["title"] == "Lesson 2"
        assert docs[0].metadata["topic"] == "Embeddings"


if __name__ == "__main__":
    test_research_note_loader_markdown_frontmatter()
    test_research_note_loader_directory_loading()
    test_research_note_loader_json_format()
    print("All ResearchNoteLoader tests passed successfully!")
