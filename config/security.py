from typing import Annotated

from bson import ObjectId
from fastapi import Depends, HTTPException,status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
import logging
from prometheus_client import Counter
from config.db import users_collection, post_collection
from datetime import datetime
from model.shemas import User, UserInDB

SSH_USERNAME_RES = "beatnowadmin"
SSH_PASSWORD_RES = "Monlau20212021!"
SSH_HOST_RES = "172.203.251.28"


# Configuración de la seguridad y autenticación OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
 
# Configuración de logs
logging.basicConfig(filename='app.log', level=logging.INFO)
 
# Configuración de Prometheus
requests_counter = Counter('requests_total', 'Total number of requests')

async def get_user(username: str):
    user = await users_collection.find_one({"username": username})

    if user:
        return User(**user)

async def fake_decode_token(token):
    # This doesn't provide any security at all
    # Check the next version
    user = await get_user(token)  # Await the result of get_user
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = await fake_decode_token(token)  # Ensure this is awaited
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    user = await current_user  # Await the coroutine
    if user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user

from config.db import users_collection

async def get_user_id(username: str):
    user = await users_collection.find_one({"username": username})
    if user:
        return str(user["_id"])
    else:
        return "Usuario no encontrado"  # O maneja esto de otra forma

async def check_post_exists(post_id: str, db):
    existing_post = await post_collection.find_one({"_id": ObjectId(post_id)})
    if not existing_post:
        raise HTTPException(status_code=404, detail="Post not found")

 
def guardar_log(evento):
    now = datetime.now()
    logging.info(f'{now} - {evento}')