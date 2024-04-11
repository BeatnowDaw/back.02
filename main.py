from fastapi import FastAPI
from routes.route import router
from prometheus_client import start_http_server
import uvicorn

app = FastAPI()
app.include_router(router)

