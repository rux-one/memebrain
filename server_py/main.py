import os
import uuid
import shutil
import string
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Configuration
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data"))
os.makedirs(DATA_DIR, exist_ok=True)

def cleanup_filename(filename):
    allowed_chars = string.ascii_letters + string.digits + "_"
    sanitized = ''.join(c if c in allowed_chars else '_' for c in filename)
    
    return sanitized.strip('_').lower()

# Global model state
model = None
tokenizer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, tokenizer
    print("Initializing Moondream2 model...")
    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {device}")
        
        model = AutoModelForCausalLM.from_pretrained(
            "vikhyatk/moondream2",
            trust_remote_code=True,
            # Using float32 for CPU safety if bfloat16 isn't supported, but user used bfloat16.
            # I'll stick to what works or let it auto-cast.
            # For CPU, float32 is safer.
            dtype=torch.float32 if device == "cpu" else torch.float16,
            device_map=device
        )
        # Note: Moondream2 model object handles tokenizer/processor internally for .caption() usually,
        # but let's ensure we have what we need.
        print("Moondream2 model initialized.")
    except Exception as e:
        print(f"Error initializing model: {e}")
    
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
                    print(f"Generated Caption for {filename}: {caption['caption']}")

                    # Generate filename
                    print("Generating filename...")
                    fn_query = "Return a short, single-line, descriptive caption for the following picture. Use minimum words, like it's a filename. Avoid using special characters."
                    fn_result = model.query(rgb_img, fn_query)
                    
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

                except Exception as e:
                    print(f"Error generating metadata: {e}")
            else:
                print("Model not loaded, skipping caption.")

        return {"success": True, "filename": filename}

    except Exception as e:
        print(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)
