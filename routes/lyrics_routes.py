from fastapi import APIRouter, Depends, HTTPException
from typing import List
from model.shemas import Lyrics, User
from config.security import get_current_user
from config.db import get_database
from pymongo.errors import PyMongoError
from bson import ObjectId

router = APIRouter()

# Manejador de excepciones para errores de base de datos
async def handle_database_error(exception: PyMongoError):
    raise HTTPException(status_code=500, detail="Database error")

# Obtener todas las letras del usuario actual
@router.get("/user-lyrics", response_model=List[Lyrics])
async def get_user_lyrics(current_user: User = Depends(get_current_user), db=Depends(get_database)):
    user_id = current_user.user_id
    try:
        user_lyrics = await db.lyrics_collection.find({"user_id": user_id}).to_list(None)
        return user_lyrics
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail="Failed to fetch user lyrics") from e

# Crear nueva letra
@router.post("/", response_model=Lyrics)
async def create_lyrics(lyrics: Lyrics, current_user: User = Depends(get_current_user), db=Depends(get_database)):
    try:
        lyrics_dict = lyrics.dict()
        lyrics_dict["user_id"] = current_user.user_id
        result = await db.lyrics_collection.insert_one(lyrics_dict)
        lyrics.id = str(result.inserted_id)
        return lyrics
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail="Failed to create lyrics") from e

# Obtener una letra por su ID
@router.get("/{lyrics_id}", response_model=Lyrics)
async def get_lyrics(lyrics_id: str, current_user: User = Depends(get_current_user), db=Depends(get_database)):
    try:
        lyrics = await db.lyrics_collection.find_one({"_id": ObjectId(lyrics_id), "user_id": current_user.user_id})
        if lyrics:
            return lyrics
        else:
            raise HTTPException(status_code=404, detail="Lyrics not found")
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail="Failed to fetch lyrics") from e

# Actualizar una letra por su ID
@router.put("/{lyrics_id}", response_model=Lyrics)
async def update_lyrics(lyrics_id: str, lyrics: Lyrics, current_user: User = Depends(get_current_user), db=Depends(get_database)):
    try:
        await db.lyrics_collection.update_one({"_id": ObjectId(lyrics_id), "user_id": current_user.user_id}, {"$set": lyrics.dict()})
        return lyrics
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail="Failed to update lyrics") from e

# Eliminar una letra por su ID
@router.delete("/{lyrics_id}", response_model=Lyrics)
async def delete_lyrics(lyrics_id: str, current_user: User = Depends(get_current_user), db=Depends(get_database)):
    try:
        lyrics = await db.lyrics_collection.find_one_and_delete({"_id": ObjectId(lyrics_id), "user_id": current_user.user_id})
        if lyrics:
            return lyrics
        else:
            raise HTTPException(status_code=404, detail="Lyrics not found")
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail="Failed to delete lyrics") from e


