# VirtualRAG

Real-time RAG-powered chatbot with document upload over LAN. Chat with your documents using a local LLM - all the compute stays on your desktop server while your laptop provides a lightweight command-line interface.

## 🎯 Features

- **Real-time WebSocket Chat**: Bidirectional streaming communication
- **RAG (Retrieval-Augmented Generation)**: Ground LLM responses in your documents
- **Document Upload**: Attach PDF/TXT files with queries or upload separately
- **ChromaDB Vector Store**: Efficient semantic search over your documents
- **Ollama LLM Integration**: Run powerful models locally on your GPU
- **Password Authentication**: Secure access to your server
- **Chat History**: Maintains conversation context
- **Duplicate Detection**: Automatically skips documents already in database

## 📋 Prerequisites

### Desktop (Server)
- Python 3.8+
- NVIDIA GPU (3080 recommended) or CPU
- [Ollama](https://ollama.ai/) installed
- Windows/Linux/macOS

### Laptop (Client)
- Python 3.8+
- Access to same LAN as server

## 🚀 Quick Start

### 1. Install Ollama on Desktop

```bash
# Download from https://ollama.ai/
# Then pull a model (examples):
ollama pull llama2        # 7B model, good balance
ollama pull mistral       # 7B, fast and capable
ollama pull phi           # 2.7B, very fast, lower quality
```

### 2. Setup Server (Desktop)

```powershell
# Clone/navigate to project
cd VirtualRAG

# Install dependencies
pip install -r requirements.txt

# Configure server
cp .env.example .env
# Edit .env and set your password and preferred LLM model

# Run server
cd Server
python fastAPI_server.py
```

Server will start on `0.0.0.0:8765` (accessible from LAN).

### 3. Setup Client (Laptop)

```powershell
# On your laptop, install dependencies
pip install -r requirements.txt

# Run client
cd Client
python fastAPI_client.py

# When prompted:
# - Enter your desktop's IP address (e.g., 192.168.1.100)
# - Enter port: 8765
# - Enter the password you set in server's .env file
```

## 💬 Usage

### Basic Chat
```
You> What is machine learning?
🤖 Assistant: [AI response streams here...]
```

### Upload Documents
```
You> /upload C:\path\to\document.pdf
✓ Document: Added 'document.pdf' (23 chunks)

You> What does the document say about neural networks?
📚 Found 3 relevant document(s): document.pdf
🤖 Assistant: [Response based on document context...]
```

### Attach Documents with Query
```
You> /attach C:\notes.txt Summarize the key points
✓ Document: Added 'notes.txt' (8 chunks)
🤖 Assistant: [Summary...]
```

### Commands
- Type your question normally to chat
- `/upload <file_path>` - Upload document to RAG database
- `/attach <file_path> <query>` - Attach doc and ask question
- `/stats` - View server stats (use browser: http://server-ip:8765/stats)
- `q` or `quit` - Exit client

## 📁 Project Structure

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

## ⚙️ Configuration

Edit `Server/.env`:

```env
# Change this password!
SERVER_PASSWORD=your_secure_password_here

# LLM model name (must be pulled with ollama)
LLM_MODEL=llama2

# Ollama server URL (default is fine for local)
LLM_BASE_URL=http://localhost:11434
```

## 🔧 Advanced Configuration

Edit `Server/config.py` to customize:

- `CHUNK_SIZE` / `CHUNK_OVERLAP`: Document chunking settings
- `TOP_K_RESULTS`: Number of similar docs to retrieve
- `MAX_FILE_SIZE_MB`: Maximum upload size
- `LLM_TEMPERATURE`: LLM creativity (0.0-1.0)
- `LLM_MAX_TOKENS`: Maximum response length

## 🌐 Finding Your Desktop's IP

### Windows (PowerShell)
```powershell
ipconfig
# Look for IPv4 Address under your active network adapter
# Example: 192.168.1.100
```

### Linux/Mac
```bash
ip addr show  # or: ifconfig
# Look for inet address
```

## 🐛 Troubleshooting

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

## 🔒 Security Notes

- This is designed for **trusted LAN use only**
- Password is sent in plaintext over WebSocket (use VPN for internet)
- For production: add TLS/SSL encryption
- Change default password immediately

## 📊 Recommended Models for RTX 3080 (10GB VRAM)

| Model | Size | Speed | Quality | Command |
|-------|------|-------|---------|---------|
| Llama 2 | 7B | Good | Good | `ollama pull llama2` |
| Mistral | 7B | Fast | Excellent | `ollama pull mistral` |
| Phi 2 | 2.7B | Very Fast | Decent | `ollama pull phi` |
| CodeLlama | 7B | Good | Code-focused | `ollama pull codellama` |

## 📝 Example Session

```
[10:23:15] You> /upload research_paper.pdf
✓ Document: Added 'research_paper.pdf' (45 chunks)

[10:23:20] You> What methodology did the authors use?
📚 Found 3 relevant document(s): research_paper.pdf
🤖 Assistant: Based on the research paper, the authors employed a mixed-methods 
approach combining quantitative surveys with qualitative interviews...

[10:24:10] You> What were the key findings?
🤖 Assistant: The study revealed three major findings: 1) ...
```

## 🤝 Contributing

This is a personal project, but feel free to fork and adapt for your needs!

## 📄 License

MIT License - Use freely for personal or academic projects
