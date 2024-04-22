from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from datetime import datetime
from typing import List
from model.shemas import Post
from config.db import get_database
from config.security import get_current_user
from model.shemas import User
router = APIRouter()


@router.post("/", response_model=Post)
async def create_publication(publication: Post, current_user: User = Depends(get_current_user), db=Depends(get_database)):
    new_publication = dict(publication.dict())
    new_publication["_id"] = ObjectId()  # Generar un nuevo ID para la publicación
    new_publication["publication_date"] = datetime.now()  # Establecer la fecha de publicación actual
    new_publication["user_id"] = current_user._id  # Utilizamos el _id del usuario actual
    result = await db["publications"].insert_one(new_publication)
    if result.inserted_id:
        return {**new_publication, "_id": str(new_publication["_id"])}
    else:
        raise HTTPException(status_code=500, detail="Failed to create publication")
@router.get("/{publication_id}", response_model=Post)
async def read_publication(publication_id: str, db=Depends(get_database)):
    publication = await db["publications"].find_one({"_id": ObjectId(publication_id)})
    if publication:
        return publication
    else:
        raise HTTPException(status_code=404, detail="Publication not found")

@router.put("/{publication_id}", response_model=Post)
async def update_publication(publication_id: str, publication: Post, current_user: User = Depends(get_current_user), db=Depends(get_database)):
    existing_publication = await db["publications"].find_one({"_id": ObjectId(publication_id)})
    if existing_publication:
        if existing_publication["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="You are not authorized to update this publication")
        updated_publication = dict(publication.dict())
        result = await db["publications"].update_one({"_id": ObjectId(publication_id)}, {"$set": updated_publication})
        if result.modified_count == 1:
            updated_publication["_id"] = publication_id
            return updated_publication
    raise HTTPException(status_code=404, detail="Publication not found")

@router.delete("/{publication_id}")
async def delete_publication(publication_id: str, current_user: User = Depends(get_current_user), db=Depends(get_database)):
    existing_publication = await db["publications"].find_one({"_id": ObjectId(publication_id)})
    if existing_publication:
        if existing_publication["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="You are not authorized to delete this publication")
        result = await db["publications"].delete_one({"_id": ObjectId(publication_id)})
        if result.deleted_count == 1:
            return {"message": "Publication deleted successfully"}
    raise HTTPException(status_code=404, detail="Publication not found")


@router.get("/user/{user_id}", response_model=List[Post])
async def list_user_publications(user_id: str, db=Depends(get_database)):
    user_publications = await db["publications"].find({"user_id": user_id}).to_list(length=None)
    if user_publications:
        return user_publications
    else:
        raise HTTPException(status_code=404, detail="User has no publications")
