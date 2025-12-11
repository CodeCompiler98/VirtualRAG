"""
Chat orchestration module
Coordinates RAG retrieval and LLM generation
"""

import os
from typing import Dict, List, Optional, AsyncGenerator
from datetime import datetime

from RAG_Database.vector_store import VectorStore
from LLM.llm_handler import LLMHandler
from config import TOP_K_RESULTS


class ChatOrchestrator:
    """
    Orchestrates the RAG + LLM pipeline for chat functionality
    """
    
    def __init__(self):
        """Initialize vector store and LLM handler"""
        self.vector_store = VectorStore()
        self.llm = LLMHandler()
        self.chat_history: List[Dict[str, str]] = []
        
    def add_message_to_history(self, role: str, content: str):
        """Add message to chat history"""
        self.chat_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().strftime('%H:%M:%S')
        })
    
    def get_chat_history(self, last_n: int = 5):
        """
        Get recent chat history formatted for context wiht last_n: Number of recent messages to include
        and returning the chat history as a string
        """
        if not self.chat_history:
            return ""
        
        recent = self.chat_history[-last_n:]
        history_str = "\nRecent conversation:\n"
        for msg in recent:
            history_str += f"{msg['role']}: {msg['content']}\n"
        return history_str
    
    async def process_query(
        self,
        query: str,
        document_paths: Optional[List[str]] = None,
        document_filenames: Optional[List[str]] = None,
        use_rag: bool = True
    ):
        """
        Process a user query through the RAG + LLM pipeline
        
        Arguement of function:
            query: User's question
            document_paths: Optional list of document paths to add to RAG
            document_filenames: Optional list of original filenames
            use_rag: Whether to use RAG for context retrieval
            
        Rerturns to me:
            Dictionaries with response chunks and metadata
        """
        # Step 1: Process any attached documents
        if document_paths:
            for i, doc_path in enumerate(document_paths):
                # Use original filename if provided, otherwise extract from path
                filename = document_filenames[i] if document_filenames and i < len(document_filenames) else os.path.basename(doc_path)
                result = self.vector_store.add_document(doc_path, filename)
                yield {
                    "type": "document_status",
                    "data": result
                }
        
        # Step 2: Retrieve context from RAG if enabled
        context = ""
        retrieved_docs = []
        
        if use_rag:
            retrieved_docs = self.vector_store.query(query, n_results=TOP_K_RESULTS)
            
            if retrieved_docs:
                # Format context from retrieved documents
                context_parts = []
                for i, doc in enumerate(retrieved_docs, 1):
                    context_parts.append(
                        f"[Source {i}: {doc['filename']}]\n{doc['content']}"
                    )
                context = "\n\n".join(context_parts)
                
                # Send retrieval info to client
                yield {
                    "type": "rag_results",
                    "data": {
                        "num_results": len(retrieved_docs),
                        "sources": [doc["filename"] for doc in retrieved_docs]
                    }
                }
        
        # Step 3: Only query LLM if there's an actual query
        if query and query.strip():
            # Build system message
            system_message = (
                "You are a helpful AI record keeper. "
                "Use the provided context from documents to answer questions accurately. "
                "If the context doesn't contain relevant information, say so and do not make up answers."
            )
            
            # Add chat history for context
            history_context = self.get_chat_history(last_n=3)
            if history_context:
                context = history_context + "\n\n" + context
            
            # Step 4: Generate response from LLM (streaming)
            yield {"type": "llm_start"}
            
            full_response = ""
            async for chunk in self.llm.generate(query, context, system_message):
                full_response += chunk
                yield {
                    "type": "llm_chunk",
                    "data": chunk
                }
            
            # Step 5: Add to chat history
            self.add_message_to_history("User", query)
            self.add_message_to_history("Assistant", full_response)
            
            yield {"type": "llm_end"}
    
    def get_stats(self):
        """Get statistics about the chat system"""
        return {
            "vector_store": self.vector_store.get_stats(),
            "llm_available": self.llm.is_available(),
            "llm_model": self.llm.model,
            "chat_messages": len(self.chat_history)
        }
