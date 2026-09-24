---
title: "AI Security and RAG Architecture Guide"
author: "Liav Dahari"
topic: "Generative AI Security"
tags: [security, rag, langchain, vertex-ai]
date: "2026-09-23"
---
# Security Principles in Retrieval-Augmented Generation (RAG)

Retrieval-Augmented Generation (RAG) combines dense semantic vector retrieval with generative foundation models.
Key security and engineering principles include:
1. **Context Grounding & Prompt Injection Resistance**: System prompts must instruct models to restrict answers strictly to retrieved context to mitigate prompt injection and hallucinations.
2. **Access Control & Source Segregation**: Vector stores must isolate document spaces by tenant or user role to prevent unauthorized data exfiltration.
3. **Throttled Batch Ingestion**: Ingesting large document collections should use batch chunking (e.g. 20 chunks per batch) to avoid API token exhaustion.
4. **Hybrid Retrieval**: Combining dense vector embeddings (e.g., text-embedding-004) with sparse keyword search (BM25) provides robust retrieval accuracy.
