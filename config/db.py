from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.database import Database
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import traceback

# Configura el cliente MongoDB asíncrono con Motor
mongo_client = AsyncIOMotorClient(
    'mongodb+srv://marcelespinoza:marcelespinoza@beatnow.hq9er.mongodb.net/'
    '?retryWrites=true&w=majority&appName=BeatNow',
    tls=True,
    tlsAllowInvalidCertificates=False
)

db = mongo_client['BeatNow']

# Colecciones de la base de datos
users_collection = db['Users']
post_collection = db['Posts']
interactions_collection = db['Interactions']
lyrics_collection = db['Lyrics']
follows_collection = db['Follows']
genres_collection = db['Genres']
moods_collection = db['Moods']
instruments_collection = db['Instruments']
mail_code_collection = db['MailCode']
password_reset_collection = db['PasswordReset']

async def get_database() -> Database:
    """Devuelve la instancia de la base de datos."""
    return db

async def handle_database_error(request: Request, exc: PyMongoError):
    """
    Maneja errores de la base de datos y devuelve un JSON con código 500.
    Además imprime el stack trace en consola para debugging.
    """
    traceback.print_exc()
    # Puedes personalizar el contenido según el tipo de excepción
    detail = str(exc)
    if isinstance(exc, ServerSelectionTimeoutError):
        detail = "No se pudo conectar a la base de datos. Por favor, verifica la configuración de red y credenciales."
    return JSONResponse(
        status_code=500,
        content={"detail": f"Database error: {detail}"}
    )

def parse_list(value: Optional[str]) -> Optional[List[str]]:
    """Convierte una cadena CSV en lista, o retorna None si está vacía."""
    if value:
        return value.split(',')
    return None
