"""
RAG Service Module.
Why this file exists: Orchestrates the core AI Retrieval-Augmented Generation pipeline.
Why this design was chosen: We use LangChain's abstractions for chunking and ChromaDB for
storage. We filter vector searches by `user_id` to ensure strict tenant data isolation.

Gap fixes applied:
  Gap 1 — Similarity score threshold (search_type="similarity_score_threshold", threshold=0.75)
           prevents semantically unrelated chunks from polluting context.
  Gap 2 — Structured-output citation filtering: a second LLM call extracts which document_ids
           were actually used in the answer; only those appear as citations.
  Gap 3 — Token-aware chunking via tiktoken (cl100k_base) so chunk_size=1000 means ~1 000
           tokens, matching LLM context window constraints.
  Gap 4 — Explicit metadata validation (user_id, document_id) at ingestion entry-point to
           fail fast on malformed call-sites before any data reaches ChromaDB.
  Gap 5 — Content-hash deduplication + document lifecycle: re-uploading the same document
           replaces old chunks instead of accumulating duplicates; identical content is
           detected early and skipped without touching ChromaDB.
"""
import hashlib
import logging
from typing import List, Dict, Any

import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_core.documents import Document as LangchainDocument
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel

from app.core.config import settings
from app.schemas.search import Citation

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level singletons
# ---------------------------------------------------------------------------

# Gap 3: token-aware encoder initialised once at import time.
_tokenizer = tiktoken.get_encoding("cl100k_base")

embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=settings.OPENAI_API_KEY)

vector_store = Chroma(
    collection_name="enterprise_documents",
    embedding_function=embeddings,
    persist_directory=settings.CHROMA_PERSIST_DIR,
)

# ---------------------------------------------------------------------------
# Gap 2: Structured output schema — model tells us which doc IDs it used.
# ---------------------------------------------------------------------------

class _CitedSources(BaseModel):
    """Pydantic schema for the structured citation-extraction call."""
    document_ids: List[int]


_citation_extractor = llm.with_structured_output(_CitedSources)

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

RAG_PROMPT_TEMPLATE = """\
You are a helpful Enterprise Knowledge Assistant.
Answer the user's question using ONLY the provided context from internal documents.
If the answer is not contained in the context, say "I cannot find the answer in the \
provided documents." DO NOT guess or use outside knowledge.

Each context block is prefixed with its document_id so you can track sources.

Context:
{context}

Question:
{question}

Answer:
"""

_CITATION_EXTRACTION_TEMPLATE = """\
You were given the following context blocks (each labelled with its document_id) and \
produced the answer below.

Context:
{context}

Answer:
{answer}

Return ONLY the document_ids of the context blocks you actually drew on to write the answer.
If you used no context blocks (e.g., you answered "I cannot find…"), return an empty list.
"""

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _compute_content_hash(pages_data: List[Dict[str, str]]) -> str:
    """
    Gap 5: Deterministic SHA-256 hash of all page text concatenated in page order.
    Used to detect re-uploads of identical document content.
    """
    hasher = hashlib.sha256()
    for page in sorted(pages_data, key=lambda p: p["page_number"]):
        hasher.update(page["text"].encode("utf-8"))
    return hasher.hexdigest()


def _delete_document_chunks(document_id: int) -> None:
    """
    Gap 5: Remove all ChromaDB chunks that belong to a specific document_id.
    Called before re-indexing to prevent stale/conflicting chunk versions.
    """
    try:
        vector_store.delete(where={"document_id": document_id})
        logger.info("Deleted existing chunks for document_id=%d", document_id)
    except Exception:
        # Chroma raises if no documents match the filter — safe to ignore.
        logger.debug("No existing chunks found for document_id=%d (nothing to delete)", document_id)


def _chunks_already_indexed(document_id: int, content_hash: str) -> bool:
    """
    Gap 5: Returns True when ChromaDB already holds chunks for this document_id
    with the exact same content hash — skipping re-ingestion of identical content.
    """
    try:
        results = vector_store.get(
            where={"document_id": document_id, "content_hash": content_hash},
            limit=1,
        )
        return bool(results and results.get("ids"))
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def process_and_index_document(
    user_id: int,
    document_id: int,
    filename: str,
    pages_data: List[Dict[str, str]],
) -> int:
    """
    Chunks extracted PDF text and stores it in ChromaDB with metadata.
    Returns the number of chunks created (0 if content was already indexed).

    Gaps addressed: 3 (token chunking), 4 (metadata validation), 5 (dedup + lifecycle).
    """
    # ------------------------------------------------------------------
    # Gap 4: Explicit metadata validation — fail fast before touching ChromaDB.
    # ------------------------------------------------------------------
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError(
            f"process_and_index_document requires a positive integer user_id; got {user_id!r}"
        )
    if not isinstance(document_id, int) or document_id <= 0:
        raise ValueError(
            f"process_and_index_document requires a positive integer document_id; got {document_id!r}"
        )
    if not filename:
        raise ValueError("process_and_index_document requires a non-empty filename.")

    # ------------------------------------------------------------------
    # Gap 5a: Content-hash deduplication — skip if identical content already stored.
    # ------------------------------------------------------------------
    content_hash = _compute_content_hash(pages_data)

    if _chunks_already_indexed(document_id, content_hash):
        logger.info(
            "document_id=%d already indexed with identical content (hash=%s). Skipping ingestion.",
            document_id,
            content_hash[:12],
        )
        # Return the existing chunk count by querying Chroma.
        try:
            existing = vector_store.get(where={"document_id": document_id})
            return len(existing.get("ids", []))
        except Exception:
            return 0

    # ------------------------------------------------------------------
    # Gap 5b: Document lifecycle — delete any stale chunks before re-indexing.
    # ------------------------------------------------------------------
    _delete_document_chunks(document_id)

    # ------------------------------------------------------------------
    # Gap 3: Token-aware text splitter.
    # ------------------------------------------------------------------
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        length_function=lambda text: len(_tokenizer.encode(text)),
        separators=["\n\n", "\n", " ", ""],
    )

    langchain_docs: List[LangchainDocument] = []

    for page in pages_data:
        chunks = text_splitter.split_text(page["text"])
        for chunk in chunks:
            # Gap 4: Validate each chunk's metadata inline.
            metadata = {
                "user_id": user_id,
                "document_id": document_id,
                "filename": filename,
                "page_number": page["page_number"],
                "content_hash": content_hash,  # Gap 5: stored for dedup lookups
            }
            assert all(v is not None for v in metadata.values()), (
                f"Chunk metadata contains None value(s): {metadata}"
            )
            langchain_docs.append(
                LangchainDocument(page_content=chunk, metadata=metadata)
            )

    if not langchain_docs:
        logger.warning("No text chunks generated for document_id=%d", document_id)
        return 0

    vector_store.add_documents(documents=langchain_docs)
    logger.info(
        "Indexed %d chunks for document_id=%d (user_id=%d, hash=%s)",
        len(langchain_docs),
        document_id,
        user_id,
        content_hash[:12],
    )
    return len(langchain_docs)


def query_documents(user_id: int, query: str) -> Dict[str, Any]:
    """
    Retrieves relevant chunks for a user and generates a grounded answer with citations.

    Gaps addressed: 1 (score threshold), 2 (structured citation filtering).
    """
    # ------------------------------------------------------------------
    # Gap 1: Score-threshold retriever — only chunks above 0.75 cosine
    # similarity are returned; semantically unrelated queries yield no docs.
    # ------------------------------------------------------------------
    retriever = vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={
            "k": 5,
            "score_threshold": 0.75,
            "filter": {"user_id": user_id},
        },
    )

    retrieved_docs = retriever.invoke(query)

    if not retrieved_docs:
        return {
            "answer": "I cannot find the answer in the provided documents.",
            "citations": [],
        }

    # Build context with document_id labels so the model can reference them.
    context_text = ""
    doc_map: Dict[int, LangchainDocument] = {}

    for doc in retrieved_docs:
        doc_id: int = doc.metadata["document_id"]
        doc_map[doc_id] = doc  # last page wins if same doc_id appears twice
        context_text += (
            f"\n--- [document_id={doc_id}] "
            f"{doc.metadata['filename']} (Page {doc.metadata['page_number']}) ---\n"
        )
        context_text += doc.page_content + "\n"

    # First LLM call: generate the free-text answer.
    prompt = PromptTemplate.from_template(RAG_PROMPT_TEMPLATE)
    formatted_prompt = prompt.format(context=context_text, question=query)
    answer_response = llm.invoke(formatted_prompt)
    answer_text: str = answer_response.content

    # ------------------------------------------------------------------
    # Gap 2: Second LLM call (structured output) — extract which document_ids
    # the model actually drew on, then filter citations to only those.
    # ------------------------------------------------------------------
    citation_prompt = PromptTemplate.from_template(_CITATION_EXTRACTION_TEMPLATE)
    formatted_citation_prompt = citation_prompt.format(
        context=context_text, answer=answer_text
    )
    try:
        cited: _CitedSources = _citation_extractor.invoke(formatted_citation_prompt)
        used_ids = set(cited.document_ids)
    except Exception as exc:
        # Graceful degradation: if structured extraction fails, surface all retrieved docs.
        logger.warning("Citation extraction failed (%s); falling back to all retrieved docs.", exc)
        used_ids = set(doc_map.keys())

    citations: List[Citation] = []
    for doc in retrieved_docs:
        doc_id = doc.metadata["document_id"]
        if doc_id in used_ids:
            citations.append(
                Citation(
                    document_id=doc_id,
                    filename=doc.metadata["filename"],
                    page_number=doc.metadata["page_number"],
                    text_snippet=doc.page_content[:200] + "...",
                )
            )
            # Avoid duplicate citations for the same document.
            used_ids.discard(doc_id)

    return {"answer": answer_text, "citations": citations}
