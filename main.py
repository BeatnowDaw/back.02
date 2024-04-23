from fastapi import FastAPI

from model.shemas import User
from routes.users_routes import router as users_router
from routes.posts_routes import router as posts_router
from routes.interactions_routes import router as interactions_router
from routes.routes import router as routes_router
from prometheus_client import start_http_server
import uvicorn

app = FastAPI()
app.include_router(users_router, prefix="/v1/api/users")
app.include_router(posts_router, prefix="/v1/api/posts")
app.include_router(interactions_router, prefix="/v1/api/interactions")
app.include_router(routes_router)



@app.get("/")
async def root():
    return {"message": "Hello World"}

def main():
    start_http_server(8000)
    uvicorn.run(app, host="localhost", port=8001)

if __name__ == "__main__":
    main()
