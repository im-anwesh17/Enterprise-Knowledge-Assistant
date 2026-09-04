"""
RAG Integrity Tests.
Why this file exists: Automated verification of the five RAG service gaps fixed in rag_service.py.
  - Gap 4 (metadata validation): asserts malformed call-sites are rejected before reaching ChromaDB.
  - Gap 4/17 (cross-tenant isolation): asserts zero leakage between users at the retrieval layer.
  - Gap 5 (deduplication): asserts identical content is not re-indexed.
  - Gap 5 (lifecycle): asserts stale chunks are replaced, not accumulated, on re-upload.

Design note on isolation strategy:
  rag_service.py creates module-level singletons (vector_store, llm, embeddings) at import time.
  We patch these AFTER normal import using patch.object on the already-imported module, so we
  don't need to block or intercept the import itself. The singletons are replaced per-test via
  a session-scoped import + function-scoped attribute patching.
"""
import hashlib
from unittest.mock import MagicMock, patch, call
import pytest

# Import once at session scope. The module-level Chroma/OpenAI init runs here
# but succeeds because chromadb and openai packages are installed. We then
# replace the resulting singletons in each test.
import app.services.rag_service as rag_service  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_singletons():
    """
    Replace module-level singletons with MagicMocks before each test,
    restore originals after. This prevents any real network / disk calls.
    """
    orig_vs = rag_service.vector_store
    orig_llm = rag_service.llm
    orig_embeddings = rag_service.embeddings
    orig_ce = rag_service._citation_extractor

    rag_service.vector_store = MagicMock()
    rag_service.llm = MagicMock()
    rag_service.embeddings = MagicMock()
    rag_service._citation_extractor = MagicMock()

    yield

    rag_service.vector_store = orig_vs
    rag_service.llm = orig_llm
    rag_service.embeddings = orig_embeddings
    rag_service._citation_extractor = orig_ce


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pages(text: str) -> list[dict]:
    return [{"page_number": 1, "text": text}]


# ---------------------------------------------------------------------------
# Gap 4 — Metadata validation
# ---------------------------------------------------------------------------

class TestMetadataValidation:
    """process_and_index_document must raise ValueError for bad inputs."""

    def test_rejects_none_user_id(self):
        with pytest.raises(ValueError, match="user_id"):
            rag_service.process_and_index_document(
                user_id=None,  # type: ignore[arg-type]
                document_id=1,
                filename="test.pdf",
                pages_data=_make_pages("hello"),
            )

    def test_rejects_zero_user_id(self):
        with pytest.raises(ValueError, match="user_id"):
            rag_service.process_and_index_document(
                user_id=0,
                document_id=1,
                filename="test.pdf",
                pages_data=_make_pages("hello"),
            )

    def test_rejects_negative_user_id(self):
        with pytest.raises(ValueError, match="user_id"):
            rag_service.process_and_index_document(
                user_id=-5,
                document_id=1,
                filename="test.pdf",
                pages_data=_make_pages("hello"),
            )

    def test_rejects_none_document_id(self):
        with pytest.raises(ValueError, match="document_id"):
            rag_service.process_and_index_document(
                user_id=1,
                document_id=None,  # type: ignore[arg-type]
                filename="test.pdf",
                pages_data=_make_pages("hello"),
            )

    def test_rejects_empty_filename(self):
        with pytest.raises(ValueError, match="filename"):
            rag_service.process_and_index_document(
                user_id=1,
                document_id=1,
                filename="",
                pages_data=_make_pages("hello"),
            )


# ---------------------------------------------------------------------------
# Gap 4/17 — Cross-tenant isolation (retrieval layer)
# ---------------------------------------------------------------------------

class TestCrossTenantIsolation:
    """The retriever filter must be scoped to exactly the requesting user's ID."""

    def test_retriever_filter_scoped_to_user(self):
        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = []

        with patch.object(rag_service.vector_store, "as_retriever", return_value=mock_retriever) as mock_as_retriever:
            result = rag_service.query_documents(user_id=42, query="some query")

        mock_as_retriever.assert_called_once()
        call_kwargs = mock_as_retriever.call_args.kwargs
        assert call_kwargs["search_kwargs"]["filter"]["user_id"] == 42
        assert result["citations"] == []
        assert "cannot find" in result["answer"].lower()

    def test_different_user_id_produces_different_filter(self):
        captured_filters = []

        def capture_retriever(**kwargs):
            captured_filters.append(kwargs.get("search_kwargs", {}).get("filter", {}))
            mock = MagicMock()
            mock.invoke.return_value = []
            return mock

        with patch.object(rag_service.vector_store, "as_retriever", side_effect=capture_retriever):
            rag_service.query_documents(user_id=1, query="q")
            rag_service.query_documents(user_id=99, query="q")

        assert captured_filters[0]["user_id"] == 1
        assert captured_filters[1]["user_id"] == 99
        assert captured_filters[0] != captured_filters[1]


# ---------------------------------------------------------------------------
# Gap 5 — Deduplication
# ---------------------------------------------------------------------------

class TestDeduplication:
    """Re-uploading identical document content must not call add_documents."""

    def test_skips_ingestion_for_identical_content(self):
        pages = _make_pages("Identical content for dedup test.")

        with (
            patch.object(rag_service, "_chunks_already_indexed", return_value=True),
            patch.object(rag_service.vector_store, "get", return_value={"ids": ["a", "b", "c"]}),
            patch.object(rag_service.vector_store, "add_documents") as mock_add,
            patch.object(rag_service, "_delete_document_chunks") as mock_delete,
        ):
            count = rag_service.process_and_index_document(
                user_id=1, document_id=7, filename="report.pdf", pages_data=pages
            )

        mock_add.assert_not_called()
        mock_delete.assert_not_called()
        assert count == 3


# ---------------------------------------------------------------------------
# Gap 5 — Document lifecycle
# ---------------------------------------------------------------------------

class TestDocumentLifecycle:
    """Re-uploading changed content must delete old chunks before adding new ones."""

    def test_deletes_old_chunks_before_reindexing(self):
        pages_v2 = _make_pages("Updated content for version 2.")
        call_order = []

        def record_delete(doc_id):
            call_order.append(("delete", doc_id))

        def record_add(documents):
            call_order.append(("add", len(documents)))

        with (
            patch.object(rag_service, "_chunks_already_indexed", return_value=False),
            patch.object(rag_service, "_delete_document_chunks", side_effect=record_delete),
            patch.object(rag_service.vector_store, "add_documents", side_effect=record_add),
        ):
            count = rag_service.process_and_index_document(
                user_id=1, document_id=7, filename="report.pdf", pages_data=pages_v2
            )

        assert len(call_order) >= 2, "Expected at least delete + add calls"
        assert call_order[0] == ("delete", 7), "delete must come before add"
        assert call_order[1][0] == "add", "add_documents must follow delete"
        assert count > 0

    def test_new_content_chunk_metadata_is_correct(self):
        added_chunks = []

        with (
            patch.object(rag_service, "_chunks_already_indexed", return_value=False),
            patch.object(rag_service, "_delete_document_chunks"),
            patch.object(
                rag_service.vector_store,
                "add_documents",
                side_effect=lambda documents: added_chunks.extend(documents),
            ),
        ):
            rag_service.process_and_index_document(
                user_id=1,
                document_id=7,
                filename="report.pdf",
                pages_data=_make_pages("Brand new v2 content here."),
            )

        assert len(added_chunks) > 0
        for doc in added_chunks:
            assert doc.metadata["document_id"] == 7
            assert doc.metadata["user_id"] == 1
            assert "content_hash" in doc.metadata


# ---------------------------------------------------------------------------
# Gap 1 — Score threshold wired into retriever
# ---------------------------------------------------------------------------

class TestScoreThreshold:
    """The retriever must use similarity_score_threshold with a numeric threshold."""

    def test_retriever_uses_score_threshold_search_type(self):
        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = []

        with patch.object(rag_service.vector_store, "as_retriever", return_value=mock_retriever) as mock_as_retriever:
            rag_service.query_documents(user_id=1, query="anything")

        call_kwargs = mock_as_retriever.call_args.kwargs
        assert call_kwargs.get("search_type") == "similarity_score_threshold", (
            "Retriever must use similarity_score_threshold search type"
        )
        search_kwargs = call_kwargs.get("search_kwargs", {})
        assert "score_threshold" in search_kwargs, "search_kwargs must include score_threshold"
        threshold = search_kwargs["score_threshold"]
        assert 0 < threshold <= 1, f"score_threshold must be in (0, 1], got {threshold}"
