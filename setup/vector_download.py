
import chromadb
from chromadb.config import Settings

# Initialize ChromaDB (this will download the model)
print("Initializing ChromaDB and downloading embedding model...")
client = chromadb.PersistentClient(
    path="Server/RAG_Database/chroma_db",
    settings=Settings(anonymized_telemetry=False)
)

# Create/get collection
collection = client.get_or_create_collection(
    name="documents",
    metadata={"hnsw:space": "cosine"}
)

# Trigger embedding model download by adding a test document
print("Triggering embedding model download...")
collection.add(
    documents=["This is a test document to download the embedding model."],
    ids=["test_init"],
    metadatas=[{"source": "initialization"}]
)

print("✓ Embedding model downloaded and cached!")
print(f"Model location: C:\\Users\\Jonah\\.cache\\chroma\\onnx_models\\")

# Clean up test document
collection.delete(ids=["test_init"])
print("✓ Test document removed")
print("\nNow your server should start instantly without timeouts!")