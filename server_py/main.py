import os
import uuid
import shutil
import string
import asyncio
from contextlib import asynccontextmanager
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer

# Load .env from current working directory (better for run-time flexibility)
load_dotenv(os.path.join(os.getcwd(), ".env"))

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from PIL import Image
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from file_monitor import FileMonitor

# Configuration
PORT = int(os.getenv("PORT", 3000))
MOONDREAM_REVISION = os.getenv("MOONDREAM_REVISION", "2025-06-21")
DATA_PATH_ENV = os.getenv("DATA_PATH", "../data")
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
ENABLE_FILE_MONITOR = os.getenv("ENABLE_FILE_MONITOR", "true").lower() == "true"
USE_POLLING_OBSERVER = os.getenv("USE_POLLING_OBSERVER", "false").lower() == "true"
MAX_WORKER_THREADS = int(os.getenv("MAX_WORKER_THREADS", 4))
MAX_QUEUE_SIZE = int(os.getenv("MAX_QUEUE_SIZE", 100))

# Handle relative paths correctly depending on run context
if os.path.isabs(DATA_PATH_ENV):
    DATA_DIR = DATA_PATH_ENV
else:
    # If relative, assume relative to this file (or CWD)
    # Using CWD is better for Docker/Env flexibility
    DATA_DIR = os.path.abspath(DATA_PATH_ENV)

os.makedirs(DATA_DIR, exist_ok=True)
print(f"Data directory: {DATA_DIR}")

# Frontend Dist Path (configurable or default)
STATIC_DIR = os.getenv("STATIC_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "../client/dist")))

def cleanup_filename(filename):
    allowed_chars = string.ascii_letters + string.digits + "_"
    sanitized = ''.join(c if c in allowed_chars else '_' for c in filename)
    
    return sanitized.strip('_').lower()

async def process_image_file(filepath: str, original_filename: str = None) -> dict:
    """
    Shared image processing logic for both upload and file monitoring.
    
    Args:
        filepath: Full path to the image file
        original_filename: Optional original filename (for uploads)
    
    Returns:
        dict with success status, filename, and caption
    """
    try:
        filename = os.path.basename(filepath)
        
        # Open and convert image
        with Image.open(filepath) as img:
            rgb_img = img.convert("RGB")
            
            # Ensure it's saved as JPEG with consistent quality
            if not filepath.lower().endswith('.jpg') and not filepath.lower().endswith('.jpeg'):
                temp_filepath = filepath.rsplit('.', 1)[0] + '.jpg'
                rgb_img.save(temp_filepath, "JPEG", quality=80)
                if temp_filepath != filepath:
                    try:
                        os.remove(filepath)
                    except:
                        pass
                    filepath = temp_filepath
                    filename = os.path.basename(filepath)
            
            # Generate caption and metadata if model is available
            if model:
                print(f"Generating caption for {filename}...")
                settings = {"temperature": 0.25, "max_tokens": 768, "top_p": 0.3}
                
                # Run model inference in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                caption = await loop.run_in_executor(
                    executor,
                    lambda: model.caption(rgb_img, length="short", settings=settings)
                )
                print(f"Generated Caption: {caption['caption']}")
                
                # Generate descriptive filename
                print("Generating filename...")
                fn_query = "Return a short, single-line, descriptive caption for the following picture. Use minimum words, like it's a filename. Avoid using special characters."
                fn_result = await loop.run_in_executor(
                    executor,
                    lambda: model.query(rgb_img, fn_query)
                )
                
                fn_answer = fn_result["answer"] if isinstance(fn_result, dict) and "answer" in fn_result else str(fn_result)
                generated_filename = cleanup_filename(fn_answer) + ".jpg"
                print(f"Generated Filename: {generated_filename}")
                
                # Rename file with collision avoidance
                new_filepath = os.path.join(DATA_DIR, generated_filename)
                counter = 1
                base_name = cleanup_filename(fn_answer)
                while os.path.exists(new_filepath) and new_filepath != filepath:
                    generated_filename = f"{base_name}_{counter}.jpg"
                    new_filepath = os.path.join(DATA_DIR, generated_filename)
                    counter += 1
                
                if filepath != new_filepath:
                    os.rename(filepath, new_filepath)
                    filename = generated_filename
                
                # Generate embedding and index in Qdrant
                if embedding_model and qdrant_client:
                    print(f"Generating embedding for {filename}...")
                    caption_text = caption['caption']
                    
                    # Run embedding in thread pool
                    embedding = await loop.run_in_executor(
                        executor,
                        lambda: embedding_model.encode(caption_text).tolist()
                    )
                    
                    # Check if already indexed (deduplication)
                    try:
                        existing = qdrant_client.scroll(
                            collection_name="memes",
                            scroll_filter=models.Filter(
                                must=[
                                    models.FieldCondition(
                                        key="filename",
                                        match=models.MatchValue(value=filename)
                                    )
                                ]
                            ),
                            limit=1
                        )
                        
                        if existing[0]:
                            print(f"File {filename} already indexed, skipping...")
                            return {"success": True, "filename": filename, "caption": caption_text, "already_indexed": True}
                    except Exception as e:
                        print(f"Error checking for existing entry: {e}")
                    
                    # Upsert to Qdrant
                    point_id = str(uuid.uuid4())
                    qdrant_client.upsert(
                        collection_name="memes",
                        points=[
                            models.PointStruct(
                                id=point_id,
                                vector=embedding,
                                payload={
                                    "filename": filename,
                                    "caption": caption_text
                                }
                            )
                        ]
                    )
                    print(f"Indexed {filename} in Qdrant")
                
                return {"success": True, "filename": filename, "caption": caption['caption']}
            else:
                print("Model not loaded, skipping caption generation")
                return {"success": True, "filename": filename, "caption": None}
                
    except Exception as e:
        print(f"Error processing image {filepath}: {e}")
        raise

# Global model state
model = None
tokenizer = None
embedding_model = None
qdrant_client = None
file_monitor = None
executor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, tokenizer, embedding_model, qdrant_client, file_monitor, executor
    print("Initializing models...")
    
    # Initialize thread pool executor for blocking operations
    executor = ThreadPoolExecutor(max_workers=MAX_WORKER_THREADS)
    print(f"Thread pool initialized with {MAX_WORKER_THREADS} workers")
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    # Initialize Moondream2
    try:
        print("Initializing Moondream2... [revision: {}]".format(MOONDREAM_REVISION), flush=True)
        model = AutoModelForCausalLM.from_pretrained(
            "vikhyatk/moondream2",
            trust_remote_code=True,
            revision=MOONDREAM_REVISION,
            dtype=torch.float32 if device == "cpu" else torch.float16,
        ).to(device=device)
        print("Moondream2 initialized.", flush=True)
    except Exception as e:
        print(f"Error initializing Moondream2: {e}", flush=True)

    # Initialize Embedding Model
    try:
        print("Initializing Embedding Model (all-MiniLM-L6-v2)...")
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Embedding Model initialized.")
    except Exception as e:
        print(f"Error initializing Embedding Model: {e}")

    # Initialize Qdrant
    try:
        print(f"Connecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}...")
        qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        
        # Check/Create collection
        collections = qdrant_client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        if "memes" not in collection_names:
            print("Creating 'memes' collection in Qdrant...")
            qdrant_client.create_collection(
                collection_name="memes",
                vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
            )
        print("Qdrant connected and collection verified.")
    except Exception as e:
        print(f"Error initializing Qdrant: {e}")
    
    # Initialize File Monitor
    if ENABLE_FILE_MONITOR:
        try:
            loop = asyncio.get_event_loop()
            file_monitor = FileMonitor(
                data_dir=DATA_DIR,
                process_callback=process_image_file,
                executor=executor,
                loop=loop,
                max_queue_size=MAX_QUEUE_SIZE,
                use_polling=USE_POLLING_OBSERVER
            )
            file_monitor.start()
        except Exception as e:
            print(f"Error starting file monitor: {e}")
    else:
        print("File monitor disabled (ENABLE_FILE_MONITOR=false)")
    
    yield
    
    # Cleanup
    print("Shutting down...")
    
    if file_monitor and file_monitor.is_running():
        file_monitor.stop()
    
    if executor:
        executor.shutdown(wait=True)
        print("Thread pool shut down")

app = FastAPI(lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/meme/image/{filename}")
async def get_meme_image(filename: str):
    """Serve meme images from the data directory"""
    filepath = os.path.join(DATA_DIR, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(filepath, media_type="image/jpeg")

@app.get("/api/meme/search")
async def search_memes(query: str = "", threshold: float = 0.5):
    if not query.strip():
        return {"message": "Empty query", "results": [], "query": query}
    
    if not embedding_model or not qdrant_client:
        return {"message": "Search models not initialized", "results": [], "query": query}
    
    try:
        # Generate embedding for the query
        query_embedding = embedding_model.encode(query).tolist()
        
        # Search in Qdrant
        try:
            # Try query_points (newer API)
            search_result = qdrant_client.query_points(
                collection_name="memes",
                query=query_embedding,
                limit=20,
                score_threshold=threshold,
                with_payload=True
            ).points
        except (AttributeError, TypeError):
            try:
                # Try query (alternative API)
                search_result = qdrant_client.query(
                    collection_name="memes",
                    query_vector=query_embedding,
                    limit=20,
                    score_threshold=threshold,
                    with_payload=True
                )
            except (AttributeError, TypeError):
                 # Fallback to what we saw in the list that looks most promising if the above fail
                 # But query_points is definitely in the list provided by the user
                search_result = qdrant_client.query_points(
                    collection_name="memes",
                    query=query_embedding,
                    limit=20,
                    score_threshold=threshold,
                    with_payload=True
                ).points

        # Format results
        
        # Format results
        results = []
        for point in search_result:
            results.append({
                "id": point.id,
                "score": point.score,
                "filename": point.payload.get("filename", ""),
                "caption": point.payload.get("caption", "")
            })
        
        return {
            "message": f"Found {len(results)} results",
            "results": results,
            "query": query
        }
        
    except Exception as e:
        print(f"Search error: {e}")
        return {"message": f"Search error: {str(e)}", "results": [], "query": query}

@app.post("/api/meme/upload")
async def upload_meme(image: UploadFile = File(...)):
    """Upload and process a meme image."""
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Generate temporary filename
    temp_filename = f"{uuid.uuid4()}.jpg"
    temp_filepath = os.path.join(DATA_DIR, temp_filename)

    try:
        # Save uploaded file temporarily
        with Image.open(image.file) as img:
            rgb_img = img.convert("RGB")
            rgb_img.save(temp_filepath, "JPEG", quality=80)
        
        # Process using shared function
        result = await process_image_file(temp_filepath, image.filename)
        
        return {
            "success": result["success"],
            "filename": result["filename"],
            "caption": result.get("caption")
        }

    except Exception as e:
        print(f"Upload failed: {e}")
        # Clean up temp file if it exists
        if os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
            except:
                pass
        raise HTTPException(status_code=500, detail="Internal server error")

# Serve Frontend if available
if os.path.exists(STATIC_DIR):
    print(f"Serving static files from: {STATIC_DIR}")
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Check if file exists in static dir (e.g. favicon.ico)
        file_path = os.path.join(STATIC_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        
        # Fallback to index.html
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False, reload_dirs=[os.path.dirname(__file__)])
