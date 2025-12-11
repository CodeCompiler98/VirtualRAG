import asyncio
import json
import base64
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

import websockets
from websockets.exceptions import ConnectionClosed


class VirtualRAGClient:
    """
    WebSocket client for VirtualRAG server
    Provides command-line chat interface + document upload
    """
    
    def __init__(self, server_host: str, server_port: int):
        """Initialize client with server connection details"""
        self.server_url = f"ws://{server_host}:{server_port}/ws"
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.running = True
        self.authenticated = False
        self.llm_responding = False  
        self.ready_for_input = asyncio.Event()  
        self.ready_for_input.set()  
    
    async def connect(self):
        """Establish WebSocket connection to server"""
        try:
            print(f"Connecting to {self.server_url}...")
            self.websocket = await websockets.connect(self.server_url)
            print("Connected!")
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    async def authenticate(self, password: str):
        """Send authentication message"""
        await self.send_message({
            "type": "auth",
            "password": password
        })
    
    async def send_message(self, message: dict):
        """Send JSON message to server"""
        if self.websocket:
            try:
                await self.websocket.send(json.dumps(message))
            except Exception as e:
                print(f"Error sending message: {e}")
    
    async def receive_messages(self):
        """Background task to receive and display messages from server"""
        try:
            while self.running and self.websocket:
                try:
                    message_str = await self.websocket.recv()
                    message = json.loads(message_str)
                    await self.handle_server_message(message)
                except ConnectionClosed:
                    print("\nConnection closed by server")
                    self.running = False
                    break
                except json.JSONDecodeError:
                    print(f"\nInvalid message format: {message_str}")
                except Exception as e:
                    print(f"\nError receiving message: {e}")
                    break
        except Exception as e:
            print(f"\nReceive loop error: {e}")
            self.running = False
    
    async def handle_server_message(self, message: dict):
        """Handle different message types from server"""
        msg_type = message.get("type")
        
        if msg_type == "auth_success":
            self.authenticated = True
            print(f"{message.get('message', 'Authenticated')}")
            
        elif msg_type == "auth_failed":
            print(f"{message.get('message', 'Authentication failed')}")
            self.running = False
            
        elif msg_type == "document_status":
            data = message.get("data", {})
            status = data.get("status")
            msg = data.get("message", "")
            
            if status == "success":
                print(f"Document: {msg}")
            elif status == "duplicate":
                print(f"{msg}")
            else:
                print(f"Document error: {msg}")
                
        elif msg_type == "rag_results":
            data = message.get("data", {})
            num_results = data.get("num_results", 0)
            sources = data.get("sources", [])
            if num_results > 0:
                print(f"\nFound {num_results} relevant document(s): {', '.join(sources)}")
            
        elif msg_type == "llm_start":
            self.llm_responding = True
            self.ready_for_input.clear()  # Block input while LLM responds
            print("\nAssistant: ", end="", flush=True)
            
        elif msg_type == "llm_chunk":
            chunk = message.get("data", "")
            print(chunk, end="", flush=True)
            
        elif msg_type == "llm_end":
            self.llm_responding = False  # LLM finished responding
            print()  # End the assistant's response with newline
            self.ready_for_input.set()  # Signal ready for next input
            
        elif msg_type == "error":
            print(f"\nError: {message.get('message', 'Unknown error')}")
            
        elif msg_type == "disconnect_ack":
            print(f"\n{message.get('message', 'Disconnected')}")
            self.running = False
    
    def encode_file(self, file_path: str) -> Optional[dict]:
        """
        Read and base64 encode a file
        
        Returns:
            Dict with filename and encoded content, or None on error
        """
        try:
            path = Path(file_path)
            if not path.exists():
                print(f"File not found: {file_path}")
                return None
            
            # Check file extension
            if path.suffix.lower() not in ['.pdf', '.txt']:
                print(f"Unsupported file type: {path.suffix}")
                return None
            
            # Read and encode
            with open(path, 'rb') as f:
                content = f.read()
            
            content_b64 = base64.b64encode(content).decode('utf-8')
            
            return {
                "filename": path.name,
                "content": content_b64
            }
            
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None
    
    async def send_query(self, query: str, file_paths: list = None):
        """
        Send a query with optional document attachments
        
        Args:
            query: User's question
            file_paths: Optional list of file paths to attach
        """
        # Prepare message
        message = {
            "type": "query",
            "query": query
        }
        
        # Attach documents if provided
        if file_paths:
            documents = []
            for file_path in file_paths:
                encoded = self.encode_file(file_path)
                if encoded:
                    documents.append(encoded)
            
            if documents:
                message["documents"] = documents
        
        # Send to server
        await self.send_message(message)
    
    async def run(self):
        """Main client loop"""
        # Connect to server
        if not await self.connect():
            return
        
        # Start receiving messages in background
        receive_task = asyncio.create_task(self.receive_messages())
        
        # Authenticate
        password = input("Enter server password: ")
        await self.authenticate(password)
        
        # Wait a moment for auth response
        await asyncio.sleep(0.5)
        
        if not self.authenticated:
            print("Authentication failed. Exiting.")
            return
        
        # Get username
        username = input("Enter your name: ")
        print(f"\nWelcome to VirtualRAG, {username}!")
        print("\nCommands:")
        print("  - Type your question to chat with the AI")
        print("  - Type '/upload <file_path>' to upload a document")
        print("  - Type '/attach <file_path> <query>' to attach doc with query")
        print("  - Type '/stats' to view server statistics")
        print("  - Type 'q' or 'quit' to exit")
        print()
        
        # Main input loop
        while self.running:
            try:

                await self.ready_for_input.wait()
                
                # Small delay to ensure all output is rendered
                await asyncio.sleep(0.05)
                
                # Get user input (only called after LLM is done)
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None, input, f"[{datetime.now().strftime('%H:%M:%S')}] {username}> "
                )
                
                if not user_input.strip():
                    continue
                
                # Handle quit
                if user_input.lower() in ['q', 'quit', 'exit']:
                    await self.send_message({"type": "disconnect"})
                    await asyncio.sleep(0.2)
                    break
                
                # Handle upload command
                if user_input.startswith('/upload '):
                    file_path = user_input[8:].strip()
                    # Send empty query for upload-only (no LLM response)
                    await self.send_query("", [file_path])
                    continue
                
                # Handle attach command
                if user_input.startswith('/attach '):
                    parts = user_input[8:].strip().split(' ', 1)
                    if len(parts) == 2:
                        file_path, query = parts
                        await self.send_query(query, [file_path])
                    else:
                        print("Usage: /attach <file_path> <query>")
                    continue
                
                # Handle stats command
                if user_input.lower() == '/stats':
                    print("(Stats endpoint is HTTP-only, use browser or curl)")
                    continue
                
                # Regular query
                await self.send_query(user_input)
                
            except KeyboardInterrupt:
                print("\n\nInterrupted. Disconnecting...")
                await self.send_message({"type": "disconnect"})
                await asyncio.sleep(0.2)
                break
            except Exception as e:
                print(f"Error: {e}")
        
        # Cleanup
        receive_task.cancel()
        if self.websocket:
            await self.websocket.close()
        print("Disconnected.")


async def main():
    """Entry point for client"""
    print("=" * 60)
    print("VirtualRAG Client - Real-time AI Chat with Document Upload")
    print("=" * 60)
    print()
    
    # Get server details
    default_host = "127.0.0.1"
    default_port = "8765"
    
    server_host = input(f"Server IP address (default: {default_host}): ").strip() or default_host
    server_port = input(f"Server port (default: {default_port}): ").strip() or default_port
    
    try:
        server_port = int(server_port)
    except ValueError:
        print("Invalid port number. Using default 8765.")
        server_port = 8765
    
    print()
    
    # Create and run client
    client = VirtualRAGClient(server_host, server_port)
    await client.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
