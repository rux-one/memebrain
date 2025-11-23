Ok let's dockerize this application for testing on a remote server.
The idea is that the whole app works on a single port, frontend it built and `dist` is served as the homepage.
Then python server runs on the same port, but different path (/api).
Port & data path need to be configurable via `.env` file.
Add `.env.example` file with default values.
App is runnable using `docker compose up`.

Also python `print` output needs to be visible in docker logs.
+ let's use `DATA_PATH` env variable in docker compose to set the storage directory inside the container.