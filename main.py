from fastapi import FastAPI

from model.shemas import User
from routes.users_routes import router as users_router
from routes.posts_routes import router as posts_router
from routes.interactions_routes import router as interactions_router
from routes.routes import router as routes_router
from prometheus_client import start_http_server
import uvicorn

# Iniciar la aplicación
app = FastAPI()

# Incluir los routers
app.include_router(users_router, prefix="/v1/api/users")
app.include_router(posts_router, prefix="/v1/api/posts")
app.include_router(interactions_router, prefix="/v1/api/interactions")
app.include_router(routes_router)

def main():
    # Iniciar el servidor de Prometheus
    start_http_server(8000)
    # Iniciar el servidor de FastAPI
    uvicorn.run(app, host="localhost", port=8001)

if __name__ == "__main__":
    # Iniciar la aplicación
    main()
