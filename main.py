from fastapi import FastAPI
from pymongo.errors import PyMongoError
from routes.users_routes import router as users_router
from routes.posts_routes import router as posts_router
from routes.interactions_routes import router as interactions_router
from routes.lyrics_routes import router as lyrics_routes, handle_database_error
from routes.routes import router as routes_router
from prometheus_client import start_http_server
import uvicorn

# Iniciar la aplicación
app = FastAPI()

# Incluir los routers
app.include_router(users_router, prefix="/v1/api/users")
app.include_router(posts_router, prefix="/v1/api/posts")
app.include_router(interactions_router, prefix="/v1/api/interactions")
app.include_router(lyrics_routes, prefix="/v1/api/lyrics")
app.include_router(routes_router)
# Manejador de excepciones global para errores de base de datos
app.add_exception_handler(PyMongoError, handle_database_error)
def main():
    # Iniciar el servidor de Prometheus
    start_http_server(8000)
    # Iniciar el servidor de FastAPI
    uvicorn.run(app, host="localhost", port=8001)

if __name__ == "__main__":
    # Iniciar la aplicación
    main()
