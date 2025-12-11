"""
FastAPI Server with WebSocket for VirtualRAG
Provides real-time chat interface with RAG + LLM
"""

import asyncio
import json
import os
import tempfile
import base64
from typing import Dict, Optional
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

from authentication import verify_password, AuthenticationError
from chat import ChatOrchestrator
from config import SERVER_HOST, SERVER_PORT, SUPPORTED_EXTENSIONS, MAX_FILE_SIZE_MB


# Initialize FastAPI app
app = FastAPI(
    title="VirtualRAG Server",
    description="Real-time RAG-powered chatbot with document upload",
    version="1.0.0"
)

# Global chat orchestrator (one per server instance)
chat_orchestrator = ChatOrchestrator()


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept and store WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, client_id: str):
        """Remove WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            print(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_message(self, websocket: WebSocket, message: dict):
        """Send JSON message to client"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            print(f"Error sending message: {e}")


manager = ConnectionManager()


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "message": "VirtualRAG Server is running"
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint for real-time chat
    
    Message format from client:
    {
        "type": "auth|query|disconnect",
        "password": ".." (for auth),
        "query": ".." (for query),
        "documents": [{"filename": "..", "content": "base64.."}, ..] (optional)
    }
    """
    client_id = f"{websocket.client.host}:{websocket.client.port}"
    authenticated = False
    
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await manager.send_message(websocket, {
                    "type": "error",
                    "message": "Invalid JSON format"
                })
                continue
            
            msg_type = message.get("type")
            
            # Handle authentication
            if msg_type == "auth":
                password = message.get("password", "")
                if verify_password(password):
                    await manager.send_message(websocket, {
                        "type": "auth_success",
                        "message": "Authentication successful"
                    })
                    authenticated = True
                else:
                    await manager.send_message(websocket, {
                        "type": "auth_failed",
                        "message": "Invalid password"
                    })
                continue
            
            # Check if authenticated for other operations
            if not authenticated:
                await manager.send_message(websocket, {
                    "type": "error",
                    "message": "Not authenticated. Send auth message first."
                })
                continue
            
            # Handle disconnect
            if msg_type == "disconnect":
                await manager.send_message(websocket, {
                    "type": "disconnect_ack",
                    "message": "Goodbye!"
                })
                break
            
            # Handle query with/without document upload
            if msg_type == "query":
                query = message.get("query", "")
                documents = message.get("documents", [])
                
                # Allow empty query if documents are being uploaded
                if not query and not documents:
                    await manager.send_message(websocket, {
                        "type": "error",
                        "message": "Empty query"
                    })
                    continue
                
                # Process documents if attached
                document_paths = []
                document_filenames = []
                
                for doc in documents:
                    filename = doc.get("filename", "")
                    content_b64 = doc.get("content", "")
                    
                    if not filename or not content_b64:
                        continue
                    
                    # Validate file extension
                    file_ext = Path(filename).suffix.lower()
                    if file_ext not in SUPPORTED_EXTENSIONS:
                        await manager.send_message(websocket, {
                            "type": "error",
                            "message": f"Unsupported file type: {file_ext}"
                        })
                        continue
                    
                    # Decode and save to temp file
                    try:
                        content_bytes = base64.b64decode(content_b64)
                        
                        # Check file size
                        size_mb = len(content_bytes) / (1024 * 1024)
                        if size_mb > MAX_FILE_SIZE_MB:
                            await manager.send_message(websocket, {
                                "type": "error",
                                "message": f"File too large: {filename} ({size_mb:.1f}MB > {MAX_FILE_SIZE_MB}MB)"
                            })
                            continue
                        
                        # Save to temp file
                        temp_file = tempfile.NamedTemporaryFile(
                            delete=False,
                            suffix=file_ext
                        )
                        temp_file.write(content_bytes)
                        temp_file.close()
                        
                        document_paths.append(temp_file.name)
                        document_filenames.append(filename)
                        
                    except Exception as e:
                        await manager.send_message(websocket, {
                            "type": "error",
                            "message": f"Error processing document {filename}: {str(e)}"
                        })
                        continue
                
                # Process query through RAG + LLM pipeline
                try:
                    async for response in chat_orchestrator.process_query(
                        query=query,
                        document_paths=document_paths if document_paths else None,
                        document_filenames=document_filenames if document_filenames else None,
                        use_rag=True
                    ):
                        await manager.send_message(websocket, response)
                    
                except Exception as e:
                    await manager.send_message(websocket, {
                        "type": "error",
                        "message": f"Error processing query: {str(e)}"
                    })
                
                # Clean up temp files
                for temp_path in document_paths:
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
    
    except WebSocketDisconnect:
        print(f"Client {client_id} disconnected (WebSocket closed)")
    except Exception as e:
        print(f"Error in WebSocket for {client_id}: {e}")
    finally:
        manager.disconnect(client_id)


def main():
    """Start the FastAPI server"""
    print(f"Starting VirtualRAG Server on {SERVER_HOST}:{SERVER_PORT}")
    print(f"WebSocket endpoint: ws://{SERVER_HOST}:{SERVER_PORT}/ws")
    print(f"Health check: http://{SERVER_HOST}:{SERVER_PORT}/")
    
    # Pre-initialize ChromaDB to download embedding model if needed
    print("\nInitializing RAG database...")
    try:
        chat_orchestrator.vector_store.query("test initialization", n_results=1)
        
        stats = chat_orchestrator.get_stats()
        print(f" Vector store ready: {stats['vector_store']['unique_documents']} documents loaded")
        print(f" LLM available: {stats['llm_available']}")
    except Exception as e:
        print(f" Warning during initialization: {e}")
    
    print("\nServer ready! Press Ctrl+C to stop\n")
    
    uvicorn.run(
        app,
        host=SERVER_HOST,
        port=SERVER_PORT,
        log_level="info",
        timeout_keep_alive=120 
    )


if __name__ == "__main__":
    main()
