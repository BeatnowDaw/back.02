import random
from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from datetime import datetime
from typing import List
from requests import post
from model.shemas import Post, PostInDB, PostShowed, NewPost
from config.db import get_database, post_collection, users_collection, interactions_collection
from config.security import get_current_user, get_user_id, get_username
from model.shemas import User
from routes.interactions_routes import count_likes, count_dislikes, count_saved

router = APIRouter()


# Crear publicación
@router.post("/", response_model=PostInDB)
async def create_publication(new_post: NewPost, current_user: User = Depends(get_current_user), db=Depends(get_database)):
    user_id = await get_user_id(current_user.username)
    if user_id == "Usuario no encontrado":
        raise HTTPException(status_code=404, detail="User not found")

    post = Post(user_id=str(ObjectId(user_id)), publication_date=datetime.now(), **new_post.dict())

    result = await post_collection.insert_one(post.dict())  # Convert the post object to a dictionary
    if result.inserted_id:
        post_db = PostInDB(_id=str(result.inserted_id), **post.dict())  # Convertir ObjectId a string para el retorno
        return post_db
    else:
        raise HTTPException(status_code=500, detail="Failed to create publication")

@router.get("/random-publication", response_model=PostShowed)
async def get_random_publication(current_user: User = Depends(get_current_user), db=Depends(get_database)):
    # Fetch all post IDs
    post_ids = await post_collection.find({}, {"_id": 1}).to_list(length=None)

    if not post_ids:
        raise HTTPException(status_code=404, detail="No publications found")

    # Select a random ID from the list
    random_post_id = random.choice(post_ids)['_id']

    # Use the existing read_publication function to fetch and return the publication details
    return await read_publication(str(random_post_id), current_user, db)

@router.get("/{post_id}", response_model=PostShowed)
async def read_publication(post_id: str, current_user: User = Depends(get_current_user), db=Depends(get_database)):
    post_dict = await post_collection.find_one({"_id": ObjectId(post_id)})
    if post_dict:
        postindb = Post(**post_dict)
        creator_name = await get_username(post_dict["user_id"])  # Use post_dict instead of post_id
        post = PostShowed(_id=str(ObjectId(post_id)), **postindb.dict(), likes=await count_likes(post_id), dislikes=await count_dislikes(post_id),
                          saves=await count_saved(post_id), creator_username=creator_name,isLiked=await has_liked_post(post_id, current_user),
                          isSaved=await has_saved_post(post_id, current_user))
        return post
    else:
        raise HTTPException(status_code=404, detail="Publication not found")

@router.put("/{post_id}", response_model=PostInDB)
async def update_publication(post_id: str, publication: NewPost, current_user: User = Depends(get_current_user),
                             db=Depends(get_database)):
    existing_publication = await post_collection.find_one({"_id": ObjectId(post_id)})
    if existing_publication:
        if str(existing_publication["user_id"]) != str(await get_user_id(current_user.username)):
            raise HTTPException(status_code=403, detail="You are not authorized to update this publication")

        # Actualizar los datos existentes con los datos de la publicación
        existing_publication.update(publication.dict(exclude_unset=True))

        # Actualizar la publicación en la base de datos
        result = await post_collection.update_one({"_id": ObjectId(post_id)}, {"$set": existing_publication})

        # Convertir ObjectId a string para el retorno
        existing_publication["_id"] = str(existing_publication["_id"])
        return existing_publication
    else:
        raise HTTPException(status_code=404, detail="Publication not found")


# Eliminar publicación por ID
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


# Listar todas las publicaciones
@router.get("/user/{username}", response_model=List[Post])
async def list_user_publications(username: str, current_user: User = Depends(get_current_user),
                                 db=Depends(get_database)):
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

async def has_liked_post(post_id: str, current_user: User):
    user_id = await get_user_id(current_user.username)
    like_exists = await interactions_collection.count_documents({"user_id": user_id, "post_id": post_id, "like_date": {"$exists": True}})
    return like_exists > 0

async def has_saved_post(post_id: str, current_user: User):
    user_id = await get_user_id(current_user.username)
    saved_exists = await interactions_collection.count_documents({"user_id": user_id, "post_id": post_id, "saved_date": {"$exists": True}})
    return saved_exists > 0