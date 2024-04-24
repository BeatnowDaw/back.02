from fastapi import APIRouter, HTTPException, Depends, Security
from datetime import datetime
from config.db import get_database, post_collection, users_collection, interactions_collection
from config.security import get_current_user, get_user_id, check_post_exists, decode_token
from model.shemas import User

# Iniciar router
router = APIRouter()

# Dar like a publicación
@router.post("/like/{post_id}")
async def add_like(post_id: str, current_user: User = Depends(get_current_user), db=Depends(get_database)):
    await check_post_exists(post_id, db)
    user_id = await get_user_id(current_user.username)
    result = await interactions_collection.update_one(
        {"user_id": user_id, "post_id": post_id},
        {"$set": {"like_date": datetime.now()}},
        upsert=True
    )
    if result.modified_count == 0 and result.upserted_id is None:
        raise HTTPException(status_code=500, detail="Failed to add like")
    return {"message": "Like added successfully"}

# Guardar publicación
@router.post("/save/{post_id}")
async def save_publication(post_id: str, current_user: User = Depends(get_current_user), db=Depends(get_database)):
    await check_post_exists(post_id, db)
    user_id = await get_user_id(current_user.username)
    result = await interactions_collection.update_one(
        {"user_id": user_id, "post_id": post_id},
        {"$set": {"saved_date": datetime.now()}},
        upsert=True
    )
    if result.modified_count == 0 and result.upserted_id is None:
        raise HTTPException(status_code=500, detail="Failed to save publication")
    return {"message": "Publication saved successfully"}

# Dar dislike a publicación
@router.post("/dislike/{post_id}")
async def add_dislike(post_id: str, current_user: User = Depends(get_current_user), db=Depends(get_database)):
    await check_post_exists(post_id, db)
    user_id = await get_user_id(current_user.username)
    result = await interactions_collection.update_one(
        {"user_id": user_id, "post_id": post_id},
        {"$set": {"dislike_date": datetime.now()}},
        upsert=True
    )
    if result.modified_count == 0 and result.upserted_id is None:
        raise HTTPException(status_code=500, detail="Failed to add dislike")
    return {"message": "Dislike added successfully"}

# Dar dislike a publicación
@router.post("/unlike/{post_id}")
async def remove_like(post_id: str, current_user: User = Depends(get_current_user), db=Depends(get_database)):
    await check_post_exists(post_id, db)
    user_id = await get_user_id(current_user.username)
    result = await interactions_collection.update_one(
        {"user_id": user_id, "post_id": post_id},
        {"$unset": {"like_date": ""}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to remove like")
    return {"message": "Like removed successfully"}

# Quitar de guardados una publicación
@router.post("/unsave/{post_id}")
async def remove_saved(post_id: str, current_user: User = Depends(get_current_user), db=Depends(get_database)):
    await check_post_exists(post_id, db)
    user_id = await get_user_id(current_user.username)
    result = await interactions_collection.update_one(
        {"user_id": user_id, "post_id": post_id},
        {"$unset": {"saved_date": ""}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to remove saved publication")
    return {"message": "Saved publication removed successfully"}

# Quitar dislike a publicación
@router.post("/undislike/{post_id}")
async def remove_dislike(post_id: str, current_user: User = Depends(get_current_user), db=Depends(get_database)):
    await check_post_exists(post_id, db)
    user_id = await get_user_id(current_user.username)
    result = await interactions_collection.update_one(
        {"user_id": user_id, "post_id": post_id},
        {"$unset": {"dislike_date": ""}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to remove dislike")
    return {"message": "Dislike removed successfully"}

@router.get("/protected-route")
async def protected_route(current_user: User = Security(decode_token, scopes=["base"])):
    return {"message": "Hello, secured world!", "user": current_user.username}