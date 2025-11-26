import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Configuration
PORT = int(os.getenv("PORT", 3000))
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data"))
STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../client/dist"))

os.makedirs(DATA_DIR, exist_ok=True)
print(f"Data directory: {DATA_DIR}")
print(f"Static directory: {STATIC_DIR}")

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    """Mock search for testing with realistic results"""
    if not query.strip():
        return {"message": "Empty query", "results": [], "query": query}
    
    # Simulate more realistic mock results based on query
    mock_results = []
    
    if "cat" in query.lower() or "animal" in query.lower():
        mock_results.append({
            "id": "1",
            "score": 0.89,
            "filename": "cat_programming.jpg", 
            "caption": "Cat sitting on laptop keyboard with code on screen"
        })
        mock_results.append({
            "id": "2",
            "score": 0.76,
            "filename": "cat_coding.jpg",
            "caption": "Programming cat meme with HTML tags"
        })
    
    if "code" in query.lower() or "programming" in query.lower() or "developer" in query.lower():
        mock_results.append({
            "id": "3",
            "score": 0.92,
            "filename": "code_working.jpg",
            "caption": "When the code finally works after 3 hours of debugging"
        })
        mock_results.append({
            "id": "4", 
            "score": 0.81,
            "filename": "developer_life.jpg",
            "caption": "Developer turning coffee into code since 2010"
        })
    
    if "funny" in query.lower() or "meme" in query.lower():
        mock_results.append({
            "id": "5",
            "score": 0.85,
            "filename": "funny_meme.jpg",
            "caption": "Classic meme template with tech twist"
        })
    
    # If no specific matches, give generic results
    if not mock_results:
        mock_results = [
            {
                "id": "1",
                "score": 0.73,
                "filename": "generic_meme_1.jpg",
                "caption": "A tech-related meme that might match your search"
            },
            {
                "id": "2",
                "score": 0.68, 
                "filename": "generic_meme_2.jpg",
                "caption": "Another relevant meme from the collection"
            }
        ]
    
    return {
        "message": f"Found {len(mock_results)} results for '{query}'",
        "results": mock_results,
        "query": query
    }

# Serve Frontend
if os.path.exists(STATIC_DIR):
    print(f"Serving static files from: {STATIC_DIR}")
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Check if file exists in static dir
        file_path = os.path.join(STATIC_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        
        # Fallback to index.html
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("simple_server:app", host="0.0.0.0", port=PORT, reload=True)
