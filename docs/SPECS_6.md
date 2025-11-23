Since ChromaDB is problematic, let's refactor the backend to use Qdrant.
Update `docker-compose.yml` to include Qdrant instance.
Then refactor the backend to use Qdrant when inserting the meme metadata.
Update .env/.env.example to include Qdrant configuration.