# MemeBrain

A simple web application for managing memes.

## Project Structure

- `client`: Vue 3 + Vite + TailwindCSS
- `server`: Express + tRPC + Sharp
- `data`: Directory for storing uploaded meme images

## Getting Started

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Start Development Servers**
   
   This command starts both client and server in parallel (if configured) or you can run them separately.
   
   ```bash
   npm run dev
   ```

   *Note: Ensure you have `nodemon` installed globally or strictly use the workspace scripts.*

   Alternatively:
   - Terminal 1: `npm run dev -w server` (Runs on port 3000)
   - Terminal 2: `npm run dev -w client` (Runs on port 5173)

3. **Access the App**
   Open [http://localhost:5173](http://localhost:5173)

## Features

- **Home**: Search memes (currently a stub).
- **Upload**: Upload new memes (converts to JPG and saves to `data/`).

## Specs

Based on `docs/SPECS_0.md`.
