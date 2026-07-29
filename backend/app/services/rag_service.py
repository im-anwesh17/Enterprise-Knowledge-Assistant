"""
RAG Service Module.
Why this file exists: Orchestrates the core AI Retrieval-Augmented Generation pipeline.
Why this design was chosen: We use LangChain's abstractions for chunking and ChromaDB for storage. We filter vector searches by `user_id` to ensure strict tenant data isolation.
"""
import logging
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document as LangchainDocument
from langchain_core.prompts import PromptTemplate
from app.core.config import settings
from app.schemas.search import Citation

logger = logging.getLogger(__name__)

# Initialize OpenAI Embeddings and LLM
embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=settings.OPENAI_API_KEY)

# Initialize ChromaDB client using a persistent directory
vector_store = Chroma(
    collection_name="enterprise_documents",
    embedding_function=embeddings,
    persist_directory=settings.CHROMA_PERSIST_DIR
)

def process_and_index_document(user_id: int, document_id: int, filename: str, pages_data: List[Dict[str, str]]) -> int:
    """
    Chunks extracted PDF text and stores it in ChromaDB with metadata.
    Returns the number of chunks created.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=["\n\n", "\n", " ", ""]
    )

    langchain_docs = []
    
    for page in pages_data:

        # Create a document for each page to preserve page metadata
        chunks = text_splitter.split_text(page["text"])
        for chunk in chunks:
            doc = LangchainDocument(
                page_content=chunk,
                metadata={
                    "user_id": user_id,
                    "document_id": document_id,
                    "filename": filename,
                    "page_number": page["page_number"]
                }
            )
            langchain_docs.append(doc)

    if not langchain_docs:
        logger.warning(f"No text chunks generated for document {document_id}")
        return 0

    vector_store.add_documents(documents=langchain_docs)
    return len(langchain_docs)


RAG_PROMPT_TEMPLATE = """
You are a helpful Enterprise Knowledge Assistant.
Answer the user's question using ONLY the provided context from internal documents.
If the answer is not contained in the context, say "I cannot find the answer in the provided documents." DO NOT guess or use outside knowledge.

Context:
{context}

Question:
{question}

Answer:
"""

def query_documents(user_id: int, query: str) -> Dict[str, Any]:
    """
    Retrieves relevant chunks for a user and generates a grounded answer with citations.
    """
    retriever = vector_store.as_retriever(
        search_kwargs={
            "k": 5, 
            "filter": {"user_id": user_id}
        }
    )
    
    retrieved_docs = retriever.invoke(query)
    
    if not retrieved_docs:
        return {
            "answer": "I cannot find the answer in the provided documents.",
            "citations": []
        }

    context_text = ""
    citations = []

    
    for doc in retrieved_docs:
        context_text += f"\n--- Document: {doc.metadata['filename']} (Page {doc.metadata['page_number']}) ---\n"
        context_text += doc.page_content + "\n"
        
        citations.append(Citation(
            document_id=doc.metadata["document_id"],
            filename=doc.metadata["filename"],
            page_number=doc.metadata["page_number"],
            text_snippet=doc.page_content[:200] + "..." # Snippet for the UI
        ))

    prompt = PromptTemplate.from_template(RAG_PROMPT_TEMPLATE)
    formatted_prompt = prompt.format(context=context_text, question=query)
    
    response = llm.invoke(formatted_prompt)

    return {
        "answer": response.content,
        "citations": citations
    }

