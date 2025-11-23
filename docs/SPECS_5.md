Let's add ChromaDB to the docker compose setup.
Update .env & requirements.txt to include ChromaDB.
Every time an image is described, let's calculate embeddings with `all-MiniLM-L6-v2` from HuggingFace, using  of the description and save them together with the filename to ChromaDB.

Additionaly, let's update `docker-compose.yml` with ChromaDB admin service [`thanatosdi/chromadb-admin` image].