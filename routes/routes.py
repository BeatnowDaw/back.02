from passlib.hash import bcrypt
from model.shemas import User, UserInDB
from config.security import guardar_log
from config.db import users_collection
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import HTTPException, Depends, APIRouter

# Iniciar router
router = APIRouter()

# Login
@router.post("/token")
@router.post("/login")  # Additional route
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_dict = await users_collection.find_one({"username": form_data.username})
    if not user_dict:
        guardar_log("Login failed - Incorrect username: " + form_data.username)
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    user = User(**user_dict)
    if not bcrypt.verify(form_data.password, user.password):
        guardar_log("Login failed - Incorrect password for username: " + form_data.username)
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    guardar_log("Login successful for username: " + form_data.username)
    return {"message": "ok"}
