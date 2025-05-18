from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
import bcrypt

from config.db import users_collection
from config.security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, guardar_log

router = APIRouter(prefix="/v1/api", tags=["Auth"])

@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    # Buscar usuario en BD
    user_doc = await users_collection.find_one({"username": form_data.username})
    if not user_doc:
        guardar_log(f"Login failed - Incorrect username: {form_data.username}")
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    # Verificar contraseña
    stored_hash = user_doc.get('password')
    if not bcrypt.checkpw(form_data.password.encode('utf-8'), stored_hash):
        guardar_log(f"Login failed - Incorrect password for username: {form_data.username}")
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    # Generar token JWT
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username},
        expires_delta=access_token_expires
    )
    guardar_log(f"Login successful for username: {form_data.username}")
    return {"access_token": access_token, "token_type": "bearer"}
