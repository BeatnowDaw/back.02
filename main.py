from fastapi import FastAPI
from routes.route import router
from prometheus_client import start_http_server
import uvicorn

app = FastAPI()
app.include_router(router)

if __name__ == "__main__":

    start_http_server(8001)

    uvicorn.run(app, host="127.0.0.1", port=8000)
