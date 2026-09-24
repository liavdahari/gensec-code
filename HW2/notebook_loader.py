"""Custom document loader for research and study notes extending LangChain BaseLoader.

This module implements ResearchNoteLoader, a specialized LangChain document loader
designed for NotebookLM-style applications. It loads and parses structured markdown,
text, and JSON research notes containing metadata headers (YAML-style frontmatter or
JSON key-value pairs) alongside unstructured body text.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document


class ResearchNoteLoader(BaseLoader):
    """Loader for structured research notes and markdown study documents.

    Extends LangChain's BaseLoader to parse note files containing frontmatter
    metadata (e.g. title, author, topics, tags, date, source URL) and body text.
    Also supports JSON-formatted research notebooks.

    Attributes:
        file_path: Path to a specific note file or directory containing note files.
        glob_pattern: File matching pattern when loading from a directory (default: "**/*.md").
        encoding: File character encoding (default: "utf-8").
    """

    def __init__(
        self,
        file_path: Union[str, Path],
        glob_pattern: str = "**/*.[mM][dD]",
        encoding: str = "utf-8",
    ) -> None:
        """Initialize the ResearchNoteLoader.

        Args:
            file_path: File or directory path to load research notes from.
            glob_pattern: Glob pattern to filter files if file_path is a directory.
            encoding: Text encoding to use when reading files.
        """
        self.file_path = Path(file_path)
        self.glob_pattern = glob_pattern
        self.encoding = encoding

    def _parse_frontmatter(self, text: str) -> tuple[Dict[str, Any], str]:
        """Extract YAML-like frontmatter key-values and separate from body content.

        Args:
            text: Raw file string content.

        Returns:
            Tuple of (metadata_dict, body_content_str).
        """
        metadata: Dict[str, Any] = {}
        content = text

        # Check for YAML frontmatter enclosed by '---'
        frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
        if frontmatter_match:
            header_text, content = frontmatter_match.groups()
            for line in header_text.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip().lower()
                    value = value.strip().strip("\"'")

                    # Parse comma-separated list for tags/topics
                    if key in ("tags", "topics", "keywords") and ("," in value or value.startswith("[")):
                        cleaned = value.strip("[]")
                        metadata[key] = [item.strip().strip("\"'") for item in cleaned.split(",") if item.strip()]
                    else:
                        metadata[key] = value

        return metadata, content.strip()

    def _parse_json_note(self, text: str, source_path: Path) -> List[Document]:
        """Parse JSON documents, including research notes and structured tabular datasets.

        Args:
            text: JSON text content.
            source_path: Path to the JSON source file.

        Returns:
            List of LangChain Document instances.
        """
        docs: List[Document] = []
        try:
            data = json.loads(text)

            # Check if this is a structured dataset table (e.g. {title, data: [...]}, {airports: [...]})
            is_dataset_dict = False
            dataset_key = None
            if isinstance(data, dict):
                for k in ("data", "airports", "items", "records", "results"):
                    if k in data and isinstance(data[k], list) and len(data[k]) > 0:
                        is_dataset_dict = True
                        dataset_key = k
                        break

            if is_dataset_dict and dataset_key:
                title = data.get("title", source_path.stem.replace("_", " ").title())
                subtitle = data.get("subtitle", "")
                header = f"{title}" + (f" - {subtitle}" if subtitle else "")
                records = data[dataset_key]
                batch_size = 5

                for i in range(0, len(records), batch_size):
                    batch = records[i : i + batch_size]
                    lines = [header]
                    for item in batch:
                        if isinstance(item, dict):
                            item_str = " | ".join(f"{k}: {v}" for k, v in item.items() if v != "-")
                            lines.append(f"• {item_str}")
                        else:
                            lines.append(f"• {item}")
                    chunk_text = "\n".join(lines)
                    meta = {
                        "source": str(source_path),
                        "title": title,
                        "topic": "Structured Dataset",
                        "loader": "ResearchNoteLoader",
                    }
                    docs.append(Document(page_content=chunk_text, metadata=meta))
                return docs

            # Otherwise, parse as research notebook notes
            items = data if isinstance(data, list) else [data]
            for idx, item in enumerate(items):
                if isinstance(item, dict):
                    content = (
                        item.get("content")
                        or item.get("body")
                        or item.get("text")
                        or item.get("notes")
                    )
                    if not content:
                        # Format arbitrary JSON dict as key-value pairs
                        content = "\n".join(f"{k}: {v}" for k, v in item.items())

                    meta = {
                        "source": str(source_path),
                        "note_id": item.get("id", idx),
                        "title": item.get("title", source_path.stem.replace("_", " ").title()),
                        "author": item.get("author", "Researcher"),
                        "topic": item.get("topic", "General"),
                        "tags": item.get("tags", []),
                        "created_at": item.get("date", item.get("created_at", "Unknown")),
                        "loader": "ResearchNoteLoader",
                    }
                    docs.append(Document(page_content=content, metadata=meta))
        except Exception:
            # Fall back to plain document if JSON parsing fails
            docs.append(
                Document(
                    page_content=text,
                    metadata={"source": str(source_path), "loader": "ResearchNoteLoader"},
                )
            )
        return docs

    def _process_file(self, path: Path) -> Iterator[Document]:
        """Read and yield Documents from a single file path.

        Args:
            path: Path to the target file.

        Yields:
            Document objects.
        """
        try:
            with open(path, "r", encoding=self.encoding, errors="replace") as f:
                raw_text = f.read()
        except Exception as e:
            # If reading fails, skip or log error
            return

        if path.suffix.lower() == ".json":
            for doc in self._parse_json_note(raw_text, path):
                yield doc
            return

        metadata, body = self._parse_frontmatter(raw_text)
        metadata.setdefault("source", str(path))
        metadata.setdefault("title", path.stem.replace("_", " ").title())
        metadata.setdefault("author", "NotebookLM User")
        metadata.setdefault("loader", "ResearchNoteLoader")

        yield Document(page_content=body, metadata=metadata)

    def lazy_load(self) -> Iterator[Document]:
        """Lazy load research notes, yielding Documents one by one.

        Yields:
            Document: LangChain document instance with note content and metadata.
        """
        if self.file_path.is_file():
            yield from self._process_file(self.file_path)
        elif self.file_path.is_dir():
            files: List[Path] = []
            if self.glob_pattern and self.glob_pattern != "**/*.[mM][dD]":
                files.extend(self.file_path.glob(self.glob_pattern))
            else:
                for pattern in ("**/*.[mM][dD]", "**/*.[jJ][sS][oO][nN]", "**/*.markdown"):
                    for p in self.file_path.glob(pattern):
                        if p not in files:
                            files.append(p)
            for p in sorted(files):
                if p.is_file():
                    yield from self._process_file(p)
        else:
            raise FileNotFoundError(f"Path does not exist: {self.file_path}")

    def load(self) -> List[Document]:
        """Load all research notes into memory as a list of Documents.

        Returns:
            List[Document]: List of all parsed research note documents.
        """
        return list(self.lazy_load())
