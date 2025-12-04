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

## Configuration

### Network Filesystems (DavFS, NFS, CIFS)

If your `DATA_PATH` is mounted via a network filesystem (e.g., davfs, NFS, CIFS), the default file monitoring won't detect changes because these filesystems don't support inotify events.

**Solution**: Enable polling mode by setting this in your `.env`:

```bash
USE_POLLING_OBSERVER=true
```

This switches the file monitor from inotify-based detection to polling (checks every ~1 second). It works with any filesystem type but uses slightly more CPU.

### Environment Variables

See `.env.example` for all available configuration options:
- `USE_POLLING_OBSERVER`: Enable for network filesystems (default: `false`)
- `ENABLE_FILE_MONITOR`: Enable automatic file processing (default: `true`)
- `MAX_QUEUE_SIZE`: Maximum files in processing queue (default: `100`)
- `DATA_PATH`: Directory for storing images

## Specs

Based on `docs/SPECS_0.md`.
