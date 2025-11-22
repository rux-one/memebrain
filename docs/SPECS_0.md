Simple web application:
- Frontend in VueJS
- Backend in a basic tRPC server
- No database in this iteration
- Two pages:
    - Home: A blank page with text search input, command-pallete like, minimal design
    - Upload: A page to upload a new meme image, no other inputs than file

- Backend (tRPC) endpoints:
    - /api/meme/search: Search for memes via text search, leave it unimplemented in this iteration
    - /api/meme/upload: Upload a new meme image, save it in `data` directory locally, random uuid for filename. Backend needs to convert all images to jpg or webp to save space.

- Basic ts lint at this point.