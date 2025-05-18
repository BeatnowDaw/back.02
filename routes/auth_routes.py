from datetime import timedelta
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from bson import ObjectId
import bcrypt
import paramiko

from config.db import users_collection
from config.security import (
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    guardar_log,
    SSH_HOST_RES,
    SSH_USERNAME_RES,
    SSH_PASSWORD_RES,
)
from routes.mail_routes import send_confirmation
from model.user_shemas import NewUser
from starlette.concurrency import run_in_threadpool

router = APIRouter(prefix="/v1/api/auth", tags=["Auth"] )

class RegisterResponse(BaseModel):
    id: str

# Helper: provisioning SSH and email in background
def _sync_provision(user_id: str, username: str):
    with paramiko.SSHClient() as ssh:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SSH_HOST_RES, username=SSH_USERNAME_RES, password=SSH_PASSWORD_RES)
        # Crear carpetas y copiar foto default
        ssh.exec_command(f"sudo mkdir -p /var/www/html/beatnow/{user_id}/photo_profile /var/www/html/beatnow/{user_id}/posts")
        ssh.exec_command(f"sudo cp /var/www/html/res/photo-profile.jpg /var/www/html/beatnow/{user_id}/photo_profile/photo_profile.png")
    # Enviar email de confirmación
    send_confirmation(username)

async def _provision(background_tasks: BackgroundTasks, user_id: str, username: str):
    background_tasks.add_task(run_in_threadpool, _sync_provision, user_id, username)

@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(
    user: NewUser,
    background_tasks: BackgroundTasks
):
    # Validar duplicados
    if await users_collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already registered")
    if await users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hashear contraseña
    pwd_hash = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    user_dict = user.dict(exclude={"password"})
    user_dict["password"] = pwd_hash

    # Insertar en DB
    result = await users_collection.insert_one(user_dict)
    user_id = str(result.inserted_id)

    # Lanzar provisioning en background (no await)
    background_tasks.add_task(_sync_provision, user_id, user.username)

    return {"id": user_id}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/login", response_model=TokenResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    # 1) Compruebo credenciales
    user_doc = await users_collection.find_one({"username": form_data.username})
    if not user_doc or not bcrypt.checkpw(
        form_data.password.encode('utf-8'),
        user_doc['password']
    ):
        guardar_log(f"Login failed for {form_data.username}")
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    # 2) Genero JWT
    access_token = create_access_token(
        data={"sub": form_data.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    guardar_log(f"Login successful for {form_data.username}")

    # 3) Devuelvo token
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }