import os
import hashlib
from typing import List, Dict, Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader

import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import VECTOR_DB_PATH, CHUNK_SIZE, CHUNK_OVERLAP, TOP_K_RESULTS


class VectorStore:
    """
    RAG Database module using ChromaDB for vector storage
    Handles document ingestion, embedding, and retrieval
    """
    
    def __init__(self):
        """Initialize ChromaDB client and collection"""
        os.makedirs(VECTOR_DB_PATH, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=VECTOR_DB_PATH,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Text splitter for chunking documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
        )
        
        # Store document hashes to prevent duplicates
        self.document_hashes = self._load_document_hashes()
    
    def _load_document_hashes(self):
        """Load existing document hashes from metadata"""
        hashes = set()
        try:
            results = self.collection.get(include=["metadatas"])
            for metadata in results.get("metadatas", []):
                if metadata and "doc_hash" in metadata:
                    hashes.add(metadata["doc_hash"])
        except Exception as e:
            print(f"Error loading document hashes: {e}")
        return hashes
    
    def _hash_content(self, content: str):
        """Generate SHA-256 hash of content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def is_duplicate(self, content: str) -> bool:
        """Check if document content already exists in database"""
        doc_hash = self._hash_content(content)
        return doc_hash in self.document_hashes
    
    def add_document(self, file_path: str, filename: str):
        """
        Add a document to the vector store (with the file path and original filename)
        """
        try:
            # Load document based on file type
            file_extension = Path(file_path).suffix.lower()
            
            if file_extension == ".pdf":
                loader = PyPDFLoader(file_path)
            elif file_extension == ".txt":
                loader = TextLoader(file_path, encoding='utf-8')
            else:
                return {"status": "error", "message": f"Unsupported file type: {file_extension}"}
            
            # Load and extract text
            documents = loader.load()
            full_content = "\n".join([doc.page_content for doc in documents])
            
            # Check for duplicates
            doc_hash = self._hash_content(full_content)
            if doc_hash in self.document_hashes:
                return {"status": "duplicate", "message": f"Document '{filename}' already exists in database"}
            
            # Split into chunks
            chunks = self.text_splitter.split_text(full_content)
            
            if not chunks:
                return {"status": "error", "message": "No content extracted from document"}
            
            # Prepare data for ChromaDB
            chunk_ids = [f"{doc_hash}_{i}" for i in range(len(chunks))]
            metadatas = [
                {
                    "filename": filename,
                    "doc_hash": doc_hash,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
                for i in range(len(chunks))
            ]
            
            # Add to collection
            self.collection.add(
                documents=chunks,
                ids=chunk_ids,
                metadatas=metadatas
            )
            
            # Update hash set
            self.document_hashes.add(doc_hash)
            
            return {
                "status": "success",
                "message": f"Added '{filename}' ({len(chunks)} chunks)",
                "chunks": len(chunks)
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Error processing document: {str(e)}"}
    
    def query(self, query_text: str, n_results: int = TOP_K_RESULTS):
        """
        Query the vector store for relevant documents (taking in the query and number of results and returning chunks)
        """
        try:
            # Check if collection is empty
            if self.collection.count() == 0:
                return []
            
            # Query ChromaDB
            results = self.collection.query(
                query_texts=[query_text],
                n_results=min(n_results, self.collection.count()),
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            if results["documents"] and results["documents"][0]:
                for doc, metadata, distance in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0]
                ):
                    formatted_results.append({
                        "content": doc,
                        "filename": metadata.get("filename", "unknown"),
                        "relevance_score": 1 - distance  # Convert distance to similarity
                    })
            
            return formatted_results
            
        except Exception as e:
            print(f"Error querying vector store: {e}")
            return []
    
    def get_stats(self):
        """Get statistics about the vector store"""
        try:
            count = self.collection.count()
            unique_docs = len(self.document_hashes)
            
            return {
                "total_chunks": count,
                "unique_documents": unique_docs,
                "status": "initialized"
            }
        except Exception as e:
            return {"error": str(e)}
