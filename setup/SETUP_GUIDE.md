# VirtualRAG Setup Guide

## Step-by-Step Installation

### Part 1: Desktop Server Setup

#### 1. Install Ollama
1. Go to https://ollama.ai/
2. Download and install Ollama for your OS
3. Open a terminal and verify: `ollama --version`

#### 2. Download an LLM Model
```bash
# Choose one based on your needs:
ollama pull llama2        # Recommended: 7B parameters, good all-rounder
ollama pull mistral       # Alternative: 7B, often better quality
ollama pull phi           # Lightweight: 2.7B, very fast on 3080
```

Test the model works:
```bash
ollama run llama2
# Type a test question, then /bye to exit
```

#### 3. Install Python Dependencies
```powershell
# Navigate to project
cd C:\Users\Jonah\VirtualRAG

# Install all requirements
pip install -r requirements.txt
```

If you get errors, install individually:
```powershell
pip install fastapi uvicorn websockets python-dotenv
pip install chromadb langchain-text-splitters langchain-community pypdf
pip install requests pydantic
```

**Important:** The first time ChromaDB runs, it will download an embedding model (~80MB). To do this upfront and avoid timeouts:

```powershell
# Pre-download the embedding model (one-time, takes 1-2 minutes)
python
```

Then in Python:
```python
import chromadb
from chromadb.config import Settings

client = chromadb.PersistentClient(
    path="Server/RAG_Database/chroma_db",
    settings=Settings(anonymized_telemetry=False)
)
collection = client.get_or_create_collection("documents")
collection.add(documents=["test"], ids=["init"])
collection.delete(ids=["init"])
print("✓ Embedding model downloaded and cached!")
exit()
```

This downloads the model to `C:\Users\<YourName>\.cache\chroma\` and caches it permanently.

#### 4. Configure Server
```powershell
# Copy example config
cp .env.example .env

# Edit .env with notepad or VS Code
notepad .env
```

Change these values in `.env`:
```env
SERVER_PASSWORD=MySecurePassword123!
LLM_MODEL=llama2
```

#### 5. Find Your Desktop's IP Address
```powershell
ipconfig
```
Look for "IPv4 Address" under your active network adapter.
Example: `192.168.1.100`

**Write this down - you'll need it for the laptop client!**

#### 6. Start Ollama Service

Ollama must be running before starting the VirtualRAG server:

```powershell
# Check if Ollama is running
ollama list
```

If you get an error, start Ollama:
- **Windows**: Open Ollama from Start Menu (runs in system tray)
- **Or in terminal**: `ollama serve` (leave this running in background)

Verify it's working:
```powershell
curl http://localhost:11434/api/tags
```

Should return JSON with your models.

#### 7. Start the Server
```powershell
cd Server
python fastAPI_server.py
```

You should see:
```
Starting VirtualRAG Server on 0.0.0.0:8765
WebSocket endpoint: ws://0.0.0.0:8765/ws
...
Initializing RAG database...
(First time: downloading embedding model, may take 1-2 minutes...)
✓ Vector store ready: 0 documents loaded
✓ LLM available: True

Server ready! Press Ctrl+C to stop
```

**Important:** Wait for "Server ready!" before connecting clients.

Leave this running!

---

### Part 2: Laptop Client Setup

#### 1. Install Python Dependencies
```powershell
# On your laptop, navigate to project
cd C:\path\to\VirtualRAG

# Install requirements
pip install websockets
```

#### 2. Connect to Server
```powershell
cd Client
python fastAPI_client.py
```

#### 3. Enter Connection Details
When prompted:
```
Server IP address: 192.168.1.100    # Your desktop's IP from Part 1, Step 5
Server port: 8765                    # Default port
Enter server password: MySecurePassword123!   # From .env file
Enter your name: Jonah
```

---

### Part 3: Testing the System

#### Test 1: Basic Chat
```
You> Hello, can you introduce yourself?
🤖 Assistant: Hello! I'm an AI assistant...
```

#### Test 2: Upload a Document
Create a test file `test.txt`:
```powershell
@"
Machine learning is a subset of artificial intelligence.
It involves training algorithms on data to make predictions.
"@ | Out-File -FilePath test.txt -Encoding utf8
```

Then upload it:
```
You> /upload C:\Users\Jonah\VirtualRAG\test.txt
✓ Document: Added 'test.txt' (1 chunks)
```

**Note:** Use full absolute paths with backslashes on Windows.

#### Test 3: Query the Document
```
You> What is machine learning according to the document?
📚 Found 1 relevant document(s): test.txt
🤖 Assistant: According to the document, machine learning is a subset of artificial intelligence...
```

---

## Common Issues & Solutions

### Issue: "Connection refused" or "Connection closed by server"
**Solution**: 
- Verify server is running on desktop and shows "Server ready!"
- Check firewall isn't blocking port 8765
- Try disabling Windows Firewall temporarily to test
- Ensure both devices are on the same WiFi network
- Wait for server initialization to complete before connecting client

### Issue: "Ollama not responding" or LLM errors
**Solution**:
```powershell
# Check Ollama is running
ollama list

# Verify Ollama service is accessible
curl http://localhost:11434/api/tags

# If not running, start it:
ollama serve
# Or open Ollama from Start Menu (Windows)

# Test directly
ollama run llama3.2
```

### Issue: Client times out during document upload
**Cause**: ChromaDB downloading embedding model (~80MB) on first use.

**Solution**: Pre-download the model before first use (see Step 3 above), or wait 1-2 minutes for the download to complete. The model is cached permanently after first download.

### Issue: "Import chromadb could not be resolved" or langchain errors
**Solution**:
```powershell
# Reinstall with correct packages
pip install chromadb --upgrade
pip install langchain-text-splitters langchain-community --upgrade

# If still errors, try:
pip uninstall langchain langchain-community langchain-text-splitters
pip install langchain-text-splitters langchain-community
```

### Issue: "Authentication failed"
**Solution**:
- Check the password in `Server/.env` matches what you're typing
- Password is case-sensitive
- Ensure `.env` file is in `Server/` directory

### Issue: "School WiFi blocks connections"
**Solution**:
- Some school networks isolate devices
- Try using your phone as a hotspot for both devices
- Or connect both to same ethernet network
- Ask IT if devices can communicate on network

---

## Advanced: Changing Models

To try a different model:

1. Check available models:
```powershell
ollama list
```

2. Pull new model:
```powershell
ollama pull mistral
# or
ollama pull llama3.2:3b
```

3. Update `Server/.env`:
```env
LLM_MODEL=mistral:latest
# or
LLM_MODEL=llama3.2:3b
```

**Important:** Use the exact name from `ollama list` including the tag (e.g., `:latest`, `:3b`)

4. Restart server (Ctrl+C, then run again)

---

## Performance Tips

### For RTX 3080:
- **Llama3.2** (2B): ~30 tokens/sec, very fast, decent quality
- **Llama3.2** (3B): ~20 tokens/sec, good balance
- **Mistral** (7B): ~10 tokens/sec, excellent quality
- **Phi** (2.7B): ~30 tokens/sec, fast but lower quality

### If responses are slow:
1. Use a smaller model: `ollama pull llama3.2:latest` (2B version)
2. Ensure Ollama is using GPU (check GPU usage in Task Manager)
3. Reduce `LLM_MAX_TOKENS` in `Server/config.py`
4. Close other GPU-intensive applications
5. Lower `TOP_K_RESULTS` in `config.py` (fewer docs retrieved)

### First-time delays:
- **Embedding model download**: 1-2 minutes (one-time only)
- **Ollama model load**: 5-10 seconds first query (then cached in VRAM)

---

## Next Steps

1. **Test with real documents**: Upload your course notes, papers, etc.
2. **Customize prompts**: Edit system message in `Server/chat.py`
3. **Adjust RAG settings**: Tune `CHUNK_SIZE` and `TOP_K_RESULTS` in `config.py`
4. **Try different models**: Experiment with model performance

---

## Need Help?

Check the main README.md for full documentation and troubleshooting guide.
