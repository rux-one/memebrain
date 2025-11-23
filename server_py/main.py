import os
import uuid
import shutil
import string
from contextlib import asynccontextmanager
from typing import Optional
from dotenv import load_dotenv
import chromadb
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

# Configuration
PORT = int(os.getenv("PORT", 3000))
MOONDREAM_REVISION = os.getenv("MOONDREAM_REVISION", "2025-06-21")
DATA_PATH_ENV = os.getenv("DATA_PATH", "../data")
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", 8000))

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

# Global model state
model = None
tokenizer = None
embedding_model = None
chroma_client = None
chroma_collection = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, tokenizer, embedding_model, chroma_client, chroma_collection
    print("Initializing models...")
    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {device}")
        
        # Initialize Moondream2
        print("Initializing Moondream2...")
        model = AutoModelForCausalLM.from_pretrained(
            "vikhyatk/moondream2",
            trust_remote_code=True,
            # revision=MOONDREAM_REVISION,
            dtype=torch.float32 if device == "cpu" else torch.float16,
            device_map=device
        )
        print("Moondream2 initialized.")

        # Initialize Embedding Model
        print("Initializing Embedding Model (all-MiniLM-L6-v2)...")
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Embedding Model initialized.")

        # Initialize ChromaDB
        print(f"Connecting to ChromaDB at {CHROMA_HOST}:{CHROMA_PORT}...")
        chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        chroma_collection = chroma_client.get_or_create_collection(name="memes")
        print("ChromaDB connected.")

    except Exception as e:
        print(f"Error initializing: {e}")
    
    yield
    
    # Cleanup if needed
    print("Shutting down...")

app = FastAPI(lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/meme/search")
async def search_memes(query: str = ""):
    return {
        "message": "Search is unimplemented in this iteration (Python backend)",
        "results": [],
        "query": query
    }

@app.post("/api/meme/upload")
async def upload_meme(image: UploadFile = File(...)):
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Generate filename
    filename = f"{uuid.uuid4()}.jpg"
    filepath = os.path.join(DATA_DIR, filename)

    try:
        # Save and convert to jpg
        with Image.open(image.file) as img:
            # Convert to RGB to avoid issues with RGBA saving as JPEG
            rgb_img = img.convert("RGB")
            rgb_img.save(filepath, "JPEG", quality=80)
            
            # Generate caption
            if model:
                print(f"Generating caption for {filename}...")
                settings = {"temperature": 0.25, "max_tokens": 768, "top_p": 0.3}
                
                # Run in thread pool if blocking? model.caption is blocking.
                # For simple app, blocking main thread momentarily is okay, 
                # but strictly we should use run_in_executor.
                # Since we are in async function, let's just call it.
                try:
                    # Generate caption
                    caption = model.caption(rgb_img, length="short", settings=settings)
                    caption = { 'caption': 'A child in a maroon jacket holds a burger in a fast food restaurant, with a white background and black logo.' }
                    print(f"Generated Caption for {filename}: {caption['caption']}")

                    # Generate filename
                    print("Generating filename...")
                    fn_query = "Return a short, single-line, descriptive caption for the following picture. Use minimum words, like it's a filename. Avoid using special characters."
                    fn_result = model.query(rgb_img, fn_query)
                    fn_result = { 'answer': 'a_young_child_holds_and_eats_a_burger' }
                    
                    # Check if result is dict or direct string (handling potential variations)
                    fn_answer = fn_result["answer"] if isinstance(fn_result, dict) and "answer" in fn_result else str(fn_result)
                    
                    generated_filename = cleanup_filename(fn_answer) + ".jpg"
                    print(f"Generated Filename: {generated_filename}")
                    
                    # Rename file
                    new_filepath = os.path.join(DATA_DIR, generated_filename)
                    # Collision avoidance
                    counter = 1
                    base_name = cleanup_filename(fn_answer)
                    while os.path.exists(new_filepath):
                        generated_filename = f"{base_name}_{counter}.jpg"
                        new_filepath = os.path.join(DATA_DIR, generated_filename)
                        counter += 1
                        
                    os.rename(filepath, new_filepath)
                    filename = generated_filename

                    # Generate Embedding and Save to ChromaDB
                    if embedding_model and chroma_collection:
                        print(f"Generating embedding for {filename}...")
                        caption_text = caption['caption']
                        embedding = embedding_model.encode(caption_text).tolist()
                        
                        chroma_collection.add(
                            ids=[filename],
                            embeddings=[embedding],
                            metadatas=[{"filename": filename, "caption": caption_text}],
                            documents=[caption_text]
                        )
                        print("Saved to ChromaDB.")

                except Exception as e:
                    print(f"Error generating metadata: {e}")
            else:
                print("Model not loaded, skipping caption.")

        return {"success": True, "filename": filename}

    except Exception as e:
        print(f"Upload failed: {e}")
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
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
