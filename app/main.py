import os
import shutil
import uuid
from pathlib import Path
from typing import List, Optional
import httpx
import chromadb
from chromadb.config import Settings
from fastapi import FastAPI, File, UploadFile, Form, Request, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pdfplumber
import docx
from PIL import Image
import io
import json
import asyncio

app = FastAPI()

# Setup directories
BASE_DIR = Path(__file__).parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
STATIC_DIR = BASE_DIR / "app" / "static"
TEMPLATES_DIR = BASE_DIR / "app" / "templates"

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Jinja2 templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# ChromaDB setup
chroma_client = chromadb.PersistentClient(
    path=str(BASE_DIR / "chroma_db"),
    settings=Settings(anonymized_telemetry=False)
)
collection = chroma_client.get_or_create_collection(name="utas_documents")

# Ollama configuration - using smallest models for lower resource usage
OLLAMA_BASE_URL = "http://localhost:11434"
EMBEDDING_MODEL = "nomic-embed-text"  # Smaller embedding model (~137MB)
CHAT_MODEL = "tinyllama"  # Smallest chat model (~637MB) - alternative: "llama3.2:1b" (~1.3GB)
VISION_MODEL = "llava:7b"  # Smaller vision model - if needed, can use smallest available

# Chunking configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        if end >= len(text):
            break
        start = end - overlap
    return chunks


async def get_embeddings(text: str, model: str = EMBEDDING_MODEL) -> List[float]:
    """Get embeddings from Ollama."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/embeddings",
                json={"model": model, "prompt": text}
            )
            response.raise_for_status()
            result = response.json()
            embedding = result.get("embedding", [])
            if not embedding:
                raise ValueError("Empty embedding returned from Ollama")
            return embedding
        except httpx.ConnectError:
            print(f"ERROR: Cannot connect to Ollama at {OLLAMA_BASE_URL}. Make sure Ollama is running.")
            raise
        except httpx.HTTPStatusError as e:
            print(f"ERROR: Ollama API error ({e.response.status_code}): {e.response.text}")
            raise
        except Exception as e:
            print(f"ERROR: Error getting embeddings: {e}")
            # Fallback: return zero vector (nomic-embed-text uses 768 dimensions)
            # This won't work well for retrieval, but prevents crashes
            return [0.0] * 768


async def describe_image(image_bytes: bytes) -> str:
    """Use Ollama vision model to describe an image."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            # Convert image to base64
            import base64
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": VISION_MODEL,
                    "prompt": "Describe this image in detail, focusing on any text, diagrams, or important visual elements. Be thorough and specific.",
                    "images": [image_b64],
                    "stream": False
                }
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "Image description unavailable")
        except Exception as e:
            print(f"Error describing image: {e}")
            return f"Error processing image: {str(e)}"


async def process_text_file(content: bytes, filename: str) -> str:
    """Extract text from various text file formats."""
    if filename.endswith('.pdf'):
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            text = "\n".join([page.extract_text() or "" for page in pdf.pages])
            return text
    elif filename.endswith('.docx'):
        doc = docx.Document(io.BytesIO(content))
        return "\n".join([para.text for para in doc.paragraphs])
    elif filename.endswith(('.txt', '.md')):
        return content.decode('utf-8', errors='ignore')
    else:
        return content.decode('utf-8', errors='ignore')


async def process_image_file(content: bytes) -> str:
    """Process image and get description from Ollama vision model."""
    return await describe_image(content)


async def ingest_document(file_id: str, text: str, filename: str):
    """Ingest document into ChromaDB with embeddings."""
    chunks = chunk_text(text)
    
    if not chunks:
        return
    
    # Generate embeddings for all chunks
    embeddings = []
    ids = []
    metadatas = []
    documents = []
    
    for i, chunk in enumerate(chunks):
        chunk_id = f"{file_id}_{i}"
        embedding = await get_embeddings(chunk)
        
        ids.append(chunk_id)
        embeddings.append(embedding)
        metadatas.append({"filename": filename, "chunk_index": i})
        documents.append(chunk)
    
    # Add to ChromaDB
    if embeddings:
        collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Handle file uploads and trigger ingestion."""
    # Validate file type
    allowed_extensions = {'.pdf', '.txt', '.md', '.docx', '.png', '.jpg', '.jpeg'}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"File type {file_ext} not supported")
    
    # Generate unique file ID
    file_id = str(uuid.uuid4())
    
    # Save file
    content = await file.read()
    file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Process file
    try:
        if file_ext in {'.png', '.jpg', '.jpeg'}:
            text = await process_image_file(content)
        else:
            text = await process_text_file(content, file.filename)
        
        if not text.strip():
            return {"status": "error", "message": "No text content extracted from file"}
        
        # Ingest into vector store (async, but we'll wait for it)
        await ingest_document(file_id, text, file.filename)
        
        return {
            "status": "success",
            "file_id": file_id,
            "filename": file.filename,
            "message": "File uploaded and processed successfully"
        }
    except Exception as e:
        # Clean up on error
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


async def retrieve_relevant_chunks(query: str, top_k: int = 5) -> List[str]:
    """Retrieve relevant chunks from ChromaDB."""
    try:
        # Check if collection has any data
        count = collection.count()
        if count == 0:
            return []
        
        # Get query embedding
        query_embedding = await get_embeddings(query)
        
        # Query ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        if results['documents'] and len(results['documents'][0]) > 0:
            return results['documents'][0]
        return []
    except Exception as e:
        print(f"Error retrieving chunks: {e}")
        return []


def build_prompt(query: str, context_chunks: List[str], action_type: Optional[str] = None, use_rag: bool = True) -> str:
    """Build the final prompt with context and query. Supports both RAG and direct modes."""
    
    if use_rag and context_chunks:
        # RAG Mode: Use context from uploaded documents
        context = "\n\n".join(context_chunks)
        system_prompt = """You are a helpful AI assistant for engineering students. You help them understand their academic materials, answer questions, and provide insights based on the documents they have uploaded.

Use the following context from their uploaded documents to answer their questions accurately and helpfully. If the context doesn't contain relevant information, you can supplement with your general knowledge."""
        
        if action_type == "summarize":
            user_prompt = f"""Based on the following context from the uploaded documents, provide a comprehensive summary.

Context:
{context}

Please provide a clear, well-structured summary of the key points and main ideas."""
        
        elif action_type == "suggest_projects":
            user_prompt = f"""Based on the following context from the uploaded documents, suggest practical project ideas that would help the student apply and deepen their understanding of these concepts.

Context:
{context}

Provide creative, actionable project suggestions that relate to the material."""
        
        elif action_type == "explain":
            user_prompt = f"""Based on the following context from the uploaded documents, explain the concepts mentioned in the user's query in a clear and educational way.

Context:
{context}

User Query: {query}

Provide a detailed explanation that helps the student understand the concept."""
        
        else:
            user_prompt = f"""Context from uploaded documents:
{context}

User Question: {query}

Please answer the user's question based on the provided context. If the context is insufficient, use your general knowledge to provide a helpful answer."""
        
        return f"{system_prompt}\n\n{user_prompt}"
    else:
        # Direct Mode: No context, just answer with general knowledge
        system_prompt = """You are a helpful AI assistant for engineering students. You help them understand concepts, answer questions, and provide insights. Be thorough, accurate, and educational in your responses."""
        
        if action_type == "summarize":
            user_prompt = f"""The user is asking for a summary. Please provide a helpful response to: {query}"""
        elif action_type == "suggest_projects":
            user_prompt = f"""Suggest practical project ideas related to: {query}. Provide creative, actionable project suggestions."""
        elif action_type == "explain":
            user_prompt = f"""Explain the following concept in a clear and educational way: {query}. Provide a detailed explanation that helps the student understand."""
        else:
            user_prompt = f"""User Question: {query}

Please answer the user's question. Be thorough, accurate, and helpful."""
        
        return f"{system_prompt}\n\n{user_prompt}"


async def stream_ollama_response(prompt: str):
    """Stream response from Ollama."""
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            async with client.stream(
                "POST",
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": CHAT_MODEL,
                    "prompt": prompt,
                    "stream": True
                }
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                yield f"data: {json.dumps({'chunk': data['response']})}\n\n"
                            if data.get("done", False):
                                yield f"data: {json.dumps({'done': True})}\n\n"
                                break
                        except json.JSONDecodeError:
                            continue
        except httpx.ConnectError:
            error_msg = f"Cannot connect to Ollama at {OLLAMA_BASE_URL}. Make sure Ollama is running and the model '{CHAT_MODEL}' is installed."
            yield f"data: {json.dumps({'error': error_msg})}\n\n"
        except httpx.HTTPStatusError as e:
            error_msg = f"Ollama API error ({e.response.status_code}): {e.response.text}"
            yield f"data: {json.dumps({'error': error_msg})}\n\n"
        except Exception as e:
            error_msg = f"Error communicating with Ollama: {str(e)}"
            yield f"data: {json.dumps({'error': error_msg})}\n\n"


@app.post("/chat")
async def chat(message: str = Form(...), action: Optional[str] = Form(None)):
    """Handle chat messages and stream responses. Supports both RAG and direct modes."""
    # Check if we have any documents in the collection
    try:
        doc_count = collection.count()
        has_documents = doc_count > 0
    except:
        has_documents = False
    
    # Retrieve relevant chunks if documents exist
    context_chunks = []
    use_rag = False
    
    if has_documents:
        context_chunks = await retrieve_relevant_chunks(message, top_k=5)
        use_rag = len(context_chunks) > 0
    
    # Build prompt (will use RAG if context available, otherwise direct mode)
    prompt = build_prompt(message, context_chunks, action_type=action, use_rag=use_rag)
    
    # Stream response
    return StreamingResponse(
        stream_ollama_response(prompt),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.get("/files")
async def list_files():
    """List all uploaded files."""
    files = []
    if UPLOAD_DIR.exists():
        for file_path in UPLOAD_DIR.iterdir():
            if file_path.is_file():
                files.append({
                    "filename": "_".join(file_path.name.split("_")[1:]),  # Remove UUID prefix
                    "id": file_path.name.split("_")[0]
                })
    return {"files": files}


if __name__ == "__main__":
    import uvicorn
    import sys
    
    # Check if port argument provided
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port number: {sys.argv[1]}. Using default port 8000.")
    
    print(f"Starting UTAS-AI server on http://localhost:{port}")
    print(f"Make sure Ollama is running at http://localhost:11434")
    print(f"Using models: Chat={CHAT_MODEL}, Embedding={EMBEDDING_MODEL}, Vision={VISION_MODEL}")
    print(f"If models are not installed, run:")
    print(f"  ollama pull {CHAT_MODEL}")
    print(f"  ollama pull {EMBEDDING_MODEL}")
    print(f"  ollama pull {VISION_MODEL}")
    uvicorn.run(app, host="127.0.0.1", port=port)

