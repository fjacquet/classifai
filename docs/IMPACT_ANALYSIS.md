# Impact Analysis: Architectural Decisions

**Date:** 10 juillet 2025
**Status:** Analysis in Progress

## 1. Introduction

This document analyzes the impact of key architectural decisions and discrepancies found across the project's documentation (`DESIGN_PRINCIPLES.md`, `EMBEDDINGS.md`, `TODO.md`). The primary focus is to evaluate the current classification strategy against a proposed embedding-based model and to synchronize our documentation.

## 2. Key Findings

1. **Architectural Discrepancy (Completion vs. Embeddings):**
    * The current implementation (`ollama_classification_module.py`) uses a **completion-based model**. We send the document's content in a prompt and ask the LLM to return a category name.
    * The `docs/EMBEDDINGS.md` document proposes a future enhancement using an **embedding-based model**. This involves converting document content and category descriptions into numerical vectors (embeddings) and finding the closest match using cosine similarity.

2. **Outdated Documentation:**
    * `docs/EMBEDDINGS.md` is outdated. It references `Click` (we use `Typer`), the standard `logging` library (we use `Loguru`), and `requirements.txt` (we use `pyproject.toml`). Its title is also misleading.
    * `TODO.md` does not accurately reflect the testing progress. The core modules have been tested, but the checklist is not updated.

## 3. Impact Analysis: Classification Strategy

### 3.1. Current Approach: Completion-Based Classification

* **Pros:**
  * Simple to implement and understand.
  * Leverages the language understanding and reasoning capabilities of the LLM.
  * Works well for a small, well-defined set of categories.
* **Cons:**
  * **Performance:** Can be slow as it requires a full LLM inference for every file.
  * **Cost/Resource Intensive:** Each classification is a full API call to the LLM.
  * **Consistency:** The LLM might return slightly different or unexpected category names, requiring robust parsing and validation logic.
  * **Scalability:** Does not scale well to a large number of categories or files.

### 3.2. Proposed Approach: Embedding-Based Classification

* **Pros:**
  * **Performance:** Extremely fast. After an initial one-time computation of category embeddings, classification only requires a fast vector similarity calculation.
  * **Efficiency:** Only requires one LLM call per document to generate its embedding.
  * **Scalability:** Scales effortlessly to thousands of categories without a performance hit.
  * **Finds "Best Fit":** Can find the most semantically similar category even if the document content doesn't explicitly mention keywords.
* **Cons:**
  * **More Complex Implementation:** Requires logic to generate and store embeddings for categories, and to calculate cosine similarity.
  * **Less "Reasoning":** Relies purely on semantic similarity, not on the complex reasoning a completion model might perform. May be less effective for categories that require understanding nuanced context.
  * **Requires an Embedding Model:** Needs a dedicated text-embedding model from Ollama (e.g., `nomic-embed-text`, `mxbai-embed-large`).

## 4. Recommendations & Proposed Actions

1. **Adopt a Hybrid Approach:** For the best of both worlds, we should plan to implement embedding-based classification as the primary, high-speed method and keep the completion-based method as an optional, more "in-depth" analysis mode.
2. **Update Documentation:**
    * Rename `docs/EMBEDDINGS.md` to `docs/ARCHITECTURE.md`.
    * Update `docs/ARCHITECTURE.md` to reflect the current technology stack (`Typer`, `Loguru`, `pyproject.toml`).
    * Incorporate the decision for a hybrid classification strategy into the architecture document.
3. **Update `TODO.md`:**
    * Mark completed testing tasks.
    * Add new tasks for implementing the embedding-based classification module.
    * Add a task for refactoring the CLI and core logic to support switching between classification modes.

This approach allows us to deliver a functional MVP based on the current implementation while paving a clear path for a more powerful and scalable solution.
