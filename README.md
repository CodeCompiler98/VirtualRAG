# VirtualRAG

Real-time chatbot with document-based question answering using Retrieval-Augmented Generation (RAG). The server runs on your desktop for LLM inference and vector search, while the client provides a lightweight command-line interface from any device on your network.

## What It Does

VirtualRAG allows you to chat with an AI assistant that can answer questions based on documents you upload. The system:

- Runs a local LLM (via Ollama) on your desktop for private, offline AI responses
- Stores uploaded documents in a vector database (ChromaDB) for semantic search
- Retrieves relevant document chunks to provide context-aware answers
- Streams responses in real-time over WebSocket connections
- Supports multiple simultaneous client connections
- Detects and skips duplicate documents automatically

All compute happens on the server (desktop). The client (laptop) is just a terminal interface that sends queries and displays responses.

## Architecture

**Server Components:**
- FastAPI with WebSocket endpoint for real-time bidirectional communication
- ChromaDB vector store for document embeddings and semantic search
- Ollama integration for local LLM inference
- Document processing pipeline (PDF/TXT to chunks to embeddings)
- Password authentication for secure access

**Client:**
- Lightweight Python WebSocket client
- Command-line interface with chat and document upload commands
- Async I/O for responsive streaming output

**Network:**
- Server binds to 0.0.0.0:8765 (accessible from LAN)
- WebSocket protocol for persistent connections
- JSON message format with type-based routing

## Prerequisites

**Server (Desktop):**
- Python 3.8 or later
- NVIDIA GPU recommended (3080 or better) or CPU
- Ollama installed from https://ollama.ai
- Windows, Linux, or macOS

**Client (Laptop/Remote):**
- Python 3.8 or later
- Network access to server (same WiFi/LAN)

## Server Setup

### 1. Install Ollama

Download and install Ollama from https://ollama.ai

Pull an LLM model (choose based on your hardware):

```bash
ollama pull llama3.2        # 2GB model, fast on RTX 3080
ollama pull llama2          # 7GB model, better quality
ollama pull mistral         # 7GB model, fast and capable
```

Verify it works:
```bash
ollama run llama3.2
```

Type a test question, then type `/bye` to exit.

### 2. Install Python Dependencies

Navigate to the project directory:
```powershell
cd C:\path\to\VirtualRAG
pip install -r requirements.txt
```

If installation fails, install packages individually:
```powershell
pip install fastapi uvicorn websockets python-dotenv
pip install chromadb langchain-text-splitters langchain-community
pip install pypdf requests pydantic
```

### 3. Download Embedding Model

ChromaDB needs to download an embedding model (80MB) on first use. Pre-download it to avoid timeouts:

```powershell
python setup\vector_download.py
```

This downloads the model to your cache and only needs to be done once.

### 4. Configure the Server

Copy the example configuration file:
```powershell
cp .env.example .env
```

Edit `.env` and set your password and model:
```env
PASSWORD=changeme123
LLM_MODEL=llama3.2:latest
LLM_BASE_URL=http://localhost:11434
```

Use the exact model name from `ollama list` including the tag.

### 5. Find Server IP Address

You'll need this for client connections:

**Windows:**
```powershell
ipconfig
```

**Linux/Mac:**
```bash
ip addr
```

Look for the IPv4 address of your active network adapter (e.g., 192.168.1.50).

### 6. Start the Server

Start Ollama (if not already running):
```powershell
ollama serve
```

In a separate terminal, start the VirtualRAG server:
```powershell
cd Server
python fastAPI_server.py
```

Wait for the message "Server ready!" before connecting clients.

The server will:
- Initialize the vector database
- Download embedding model on first run (80MB, cached permanently)
- Verify LLM availability
- Start listening on port 8765

**Note:** If clients can't connect from other devices, you may need to allow the port through Windows Firewall:

```powershell
New-NetFirewallRule -DisplayName "VirtualRAG" -Direction Inbound -LocalPort 8765 -Protocol TCP -Action Allow
```

Run this in PowerShell as Administrator.

## Client Setup

### 1. Install Dependencies

On your laptop or remote machine:
```bash
pip install websockets
```

### 2. Copy Client File

Transfer `Client/fastAPI_client.py` to your laptop.

### 3. Run the Client

**Windows:**
```powershell
cd Client
python fastAPI_client.py
```

**Mac/Linux:**
```bash
cd Client
python3 fastAPI_client.py
```

### 4. Connect to Server

When prompted, enter:

- Server IP address: Your desktop's IP from server setup step 4 (e.g., 192.168.1.50)
- Server port: 8765 (press Enter for default)
- Password: The password from your .env file
- Name: Your username for the session

If connecting from the same machine as the server, use `127.0.0.1` as the IP address.

## Usage

### Basic Chat

Simply type your question and press Enter:
```
[14:23:45] John> What is machine learning?
Assistant: Machine learning is a subset of artificial intelligence...
```

### Upload Documents

Use the /upload command with the full file path:
```
[14:24:10] John> /upload C:\Users\John\notes.txt
Document: Added 'notes.txt' (5 chunks)
```

Supported formats: PDF, TXT

### Query with Documents

After uploading, ask questions about the content:
```
[14:24:30] John> What are the key points in my notes?

Found 3 relevant document(s): notes.txt

Assistant: The key points from your notes are...
```

### Attach Document with Query

Upload and query in one command:
```
[14:25:00] John> /attach C:\report.pdf Summarize the findings
Document: Added 'report.pdf' (12 chunks)

Found 5 relevant document(s): report.pdf

Assistant: The report findings include...
```

### Available Commands

- Type your question normally to chat with the AI
- `/upload <file_path>` - Upload a document to the database
- `/attach <file_path> <query>` - Upload document and ask question
- `q` or `quit` - Exit the client

## Project Structure

```
VirtualRAG/
├── Server/                      # Desktop server (all compute)
│   ├── fastAPI_server.py       # FastAPI + WebSocket server
│   ├── chat.py                 # RAG + LLM orchestration
│   ├── authentication.py       # Password verification
│   ├── config.py               # Configuration settings
│   ├── LLM/
│   │   └── llm_handler.py      # Ollama integration
│   └── RAG_Database/
│       └── vector_store.py     # ChromaDB vector store
├── Client/                      # Laptop client (lightweight)
│   └── fastAPI_client.py       # CLI chat interface
├── requirements.txt            # Python dependencies
└── .env.example               # Configuration template
```

## Configuration

Edit `Server/.env`:

```env
PASSWORD=your_secure_password
LLM_MODEL=llama3.2:latest
LLM_BASE_URL=http://localhost:11434
```

## Advanced Configuration

Edit `Server/config.py` to customize:

- `CHUNK_SIZE` / `CHUNK_OVERLAP`: Document chunking settings
- `TOP_K_RESULTS`: Number of similar docs to retrieve
- `MAX_FILE_SIZE_MB`: Maximum upload size
- `LLM_TEMPERATURE`: LLM creativity (0.0-1.0)
- `LLM_MAX_TOKENS`: Maximum response length

## Troubleshooting

### Server won't start
- Check Ollama is running: `ollama list`
- Verify port 8765 is not in use
- Check firewall allows incoming connections on 8765

### Client can't connect
- Verify you can ping server: `ping <server-ip>`
- Ensure both devices on same network/VLAN
- Try connecting from server first: `127.0.0.1` or `localhost`
- Check server logs for connection attempts

### LLM not responding
- Verify Ollama is running: `ollama list`
- Check model is downloaded: `ollama pull <model-name>`
- Test Ollama directly: `ollama run llama2`

### Document upload fails
- Check file extension (.pdf or .txt)
- Verify file size < 50MB (default limit)
- Ensure PDF is not corrupted or password-protected

## Security Notes

- This is designed for trusted LAN use only
- Password is sent in plaintext over WebSocket (use VPN for internet access)
- For production: add TLS/SSL encryption
- Change default password immediately

## Recommended Models for RTX 3080

| Model | Size | Speed | Quality | Command |
|-------|------|-------|---------|---------|  
| Llama 3.2 | 2GB | Very Fast | Good | `ollama pull llama3.2` |
| Llama 2 | 7GB | Good | Good | `ollama pull llama2` |
| Mistral | 7GB | Fast | Excellent | `ollama pull mistral` |
| Phi 2 | 2.7GB | Very Fast | Decent | `ollama pull phi` |## Example Session

```
[10:23:15] John> /upload research_paper.pdf
Document: Added 'research_paper.pdf' (45 chunks)

[10:23:20] John> What methodology did the authors use?

Found 3 relevant document(s): research_paper.pdf

Assistant: Based on the research paper, the authors employed a mixed-methods 
approach combining quantitative surveys with qualitative interviews...

[10:24:10] John> What were the key findings?

Assistant: The study revealed three major findings: 1) ...
```

## License

MIT License - Use freely for personal or academic projects
