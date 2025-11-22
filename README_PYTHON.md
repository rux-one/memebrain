# MemeBrain Python Backend

This is the new backend for MemeBrain, written in Python using FastAPI.

## Setup

1. **Prerequisites**
   - Python 3.8+
   - Virtual environment recommended (since global pip might be restricted)

2. **Install Dependencies**
   ```bash
   # Create venv
   python3 -m venv venv
   
   # Activate venv
   source venv/bin/activate
   
   # Install packages
   pip install -r server_py/requirements.txt
   ```

3. **Run Server**
   ```bash
   ./start_server_py.sh
   ```
   Or manually:
   ```bash
   source venv/bin/activate
   cd server_py
   python main.py
   ```
   The server runs on `http://localhost:3000`.

## Architecture

- **Framework**: FastAPI
- **Model**: Moondream2 (`vikhyatk/moondream2`) via `transformers`
- **Storage**: Local file system (`data/` directory)

## API Endpoints

- `POST /api/meme/upload`: Upload image, save to disk, generate caption.
- `GET /api/meme/search`: Search stub.
