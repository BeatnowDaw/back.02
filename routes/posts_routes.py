from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from datetime import datetime
from typing import List
from model.shemas import Post, UserInDB
from config.db import get_database, post_collection, users_collection, interactions_collection
from config.security import get_current_user, get_user_id
from model.shemas import User


router = APIRouter()

@router.post("/", response_model=Post)
async def create_publication(post: Post, current_user: User = Depends(get_current_user), db=Depends(get_database)):
    user_id = await get_user_id(current_user.username)
    if user_id == "Usuario no encontrado":
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    new_post = post.dict()  # Convertir el objeto Post a un diccionario
    new_post["publication_date"] = datetime.now()  # Establecer la fecha de publicación actual
    new_post["user_id"] = user_id  # Utilizamos el _id del usuario actual

    result = await post_collection.insert_one(new_post)
    if result.inserted_id:
        new_post["_id"] = str(result.inserted_id)  # Convertir ObjectId a string para el retorno
        return new_post
    else:
        raise HTTPException(status_code=500, detail="Failed to create publication")
@router.get("/{post_id}", response_model=Post)
async def read_publication(post_id: str, db=Depends(get_database)):
    post = await post_collection.find_one({"_id": ObjectId(post_id)})
    if post:
        return post
    else:
        raise HTTPException(status_code=404, detail="Publication not found")

@router.put("/{post_id}", response_model=Post)
async def update_publication(post_id: str, publication: Post, current_user: User = Depends(get_current_user), db=Depends(get_database)):
    existing_publication = await post_collection.find_one({"_id": ObjectId(post_id)})
    if existing_publication:
        if existing_publication["user_id"] != await get_user_id(current_user.username):
            raise HTTPException(status_code=403, detail="You are not authorized to update this publication")
        updated_publication = dict(publication.dict())
        result = await post_collection.update_one({"_id": ObjectId(post_id)}, {"$set": updated_publication})
        if result.modified_count == 1:
            updated_publication["_id"] = post_id
            return updated_publication
    raise HTTPException(status_code=404, detail="Publication not found")

@router.delete("/{post_id}")
async def delete_publication(post_id: str, current_user: User = Depends(get_current_user), db=Depends(get_database)):
    existing_publication = await post_collection.find_one({"_id": ObjectId(post_id)})
    if existing_publication:
        if existing_publication["user_id"] != await get_user_id(current_user.username):
            raise HTTPException(status_code=403, detail="You are not authorized to delete this publication")
        result = await post_collection.delete_one({"_id": ObjectId(post_id)})
        if result.deleted_count == 1:
            return {"message": "Publication deleted successfully"}
    raise HTTPException(status_code=404, detail="Publication not found")


@router.get("/user/{username}", response_model=List[Post])
async def list_user_publications(username: str, current_user: User = Depends(get_current_user), db=Depends(get_database)):

    # Verificar si el usuario actual tiene permiso para acceder a las publicaciones del usuario solicitado
    if current_user.username != username:
        raise HTTPException(status_code=403, detail="You are not authorized to access this user's publications")

    # Verificar si el usuario solicitado existe
    user_exists = await users_collection.find_one({"username": username})
    if not user_exists:
        raise HTTPException(status_code=404, detail="User not found")

    # Buscar todas las publicaciones del usuario
    user_id = await get_user_id(username)
    user_publications = await post_collection.find({"user_id": user_id}).to_list(length=None)

    # Comprobar si se encontraron publicaciones
    if user_publications:
        return user_publications
    else:
        raise HTTPException(status_code=404, detail="User has no publications")