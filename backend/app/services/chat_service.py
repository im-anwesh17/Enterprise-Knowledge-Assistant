"""
Chat Service Module.
Why this file exists: Adds Conversational Memory to our Enterprise RAG pipeline.
Why this design was chosen: We reconstruct LangChain history directly from PostgreSQL records on every request. This makes the API completely stateless horizontally, meaning any backend server node can handle any chat request securely.
"""
import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.vectorstores import Chroma

from app.core.config import settings
from app.schemas.search import Citation
from app.repositories import chat as crud_chat
from app.models.chat import ChatMessage, ChatSession

logger = logging.getLogger(__name__)

embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=settings.OPENAI_API_KEY)

vector_store = Chroma(
    collection_name="enterprise_documents",
    embedding_function=embeddings,
    persist_directory=settings.CHROMA_PERSIST_DIR
)

# Phase 5 System Prompt with Memory support
CONVERSATIONAL_RAG_PROMPT = """
You are a helpful Enterprise Knowledge Assistant.
Answer the user's question using ONLY the provided context from internal documents.
If the answer is not contained in the context, say "I cannot find the answer in the provided documents." DO NOT guess or use outside knowledge.

Context:
{context}
"""

def conversational_rag(db: Session, user_id: int, session_id: int, query: str) -> Dict[str, Any]:
    """
    Executes a RAG query with conversational memory injected from the database.
    """
    db_messages = crud_chat.chat_message.get_by_session(db=db, session_id=session_id)
    
    langchain_history = []
    for msg in db_messages:
        if msg.role == "user":
            langchain_history.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            langchain_history.append(AIMessage(content=msg.content))

    retriever = vector_store.as_retriever(search_kwargs={"k": 5, "filter": {"user_id": user_id}})
    retrieved_docs = retriever.invoke(query)
    
    context_text = ""
    citations = []
    
    for doc in retrieved_docs:
        context_text += f"\n--- Document: {doc.metadata['filename']} (Page {doc.metadata['page_number']}) ---\n"
        context_text += doc.page_content + "\n"
        citations.append(Citation(
            document_id=doc.metadata["document_id"],
            filename=doc.metadata["filename"],
            page_number=doc.metadata["page_number"],
            text_snippet=doc.page_content[:200] + "..."
        ))

    if not retrieved_docs:
        context_text = "No relevant context found in documents."

    prompt = ChatPromptTemplate.from_messages([
        ("system", CONVERSATIONAL_RAG_PROMPT),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}")
    ])
    
    chain = prompt | llm
    
    response = chain.invoke({
        "context": context_text,
        "history": langchain_history,
        "question": query
    })

    answer = response.content

    user_msg = ChatMessage(session_id=session_id, role="user", content=query)
    db.add(user_msg)
    
    ai_msg = ChatMessage(session_id=session_id, role="assistant", content=answer)
    db.add(ai_msg)
    
    db.commit()

    return {

        "answer": answer,
        "citations": citations
    }
