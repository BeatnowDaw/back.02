from passlib.handlers.bcrypt import bcrypt
import bcrypt
from model.shemas import User
from config.security import guardar_log
from config.db import users_collection
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import HTTPException, Depends, APIRouter


router = APIRouter()
@router.post("/token")  # Original route
@router.post("/login")  # Additional route
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    #guardar_log("Login attempt for username: " + form_data.username)

    user_dict = await users_collection.find_one({"username": form_data.username})
    if not user_dict:
        guardar_log("Login failed - Incorrect username: " + form_data.username)
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    user = User(**user_dict)
    if not bcrypt.checkpw(form_data.password.encode('utf-8'), user_dict['password'].encode('utf-8')):
        guardar_log("Login failed - Incorrect password for username: " + form_data.username)
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    guardar_log("Login successful for username: " + form_data.username)
    return {"access_token": user.username, "token_type": "bearer"}