from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from model.follow_shemas import Follow
from config.db import follows_collection, get_database

router = APIRouter()


@router.post("/", response_model=Follow, status_code=status.HTTP_201_CREATED)
async def create_follow(follow: Follow, db=Depends(get_database)):
    follow_dict = follow.dict()
    follow_dict["follow_date"] = datetime.utcnow()
    result = await follows_collection.insert_one(follow_dict)
    follow_id = str(result.inserted_id)
    return {**follow.dict(), "_id": follow_id}

@router.get("/{follow_id}", response_model=Follow)
async def read_follow(follow_id: str, db=Depends(get_database)):
    follow = await follows_collection.find_one({"_id": follow_id})
    if follow:
        return follow
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow not found")


@router.put("/{follow_id}", response_model=Follow)
async def update_follow(follow_id: str, follow: Follow, db=Depends(get_database)):
    existing_follow = await follows_collection.find_one({"_id": follow_id})
    if existing_follow is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow not found")
    
    updated_follow = {**existing_follow, **follow.dict()}
    await follows_collection.replace_one({"_id": follow_id}, updated_follow)
    return updated_follow

@router.delete("/{follow_id}")
async def delete_follow(follow_id: str, db=Depends(get_database)):
    delete_result = await follows_collection.delete_one({"_id": follow_id})
    if delete_result.deleted_count == 1:
        return {"message": "Follow deleted successfully"}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow not found")

@router.get("/count/{user_id_followed}")
async def count_followers(user_id_followed: str, db=Depends(get_database)):
    count = await follows_collection.count_documents({"user_id_followed": user_id_followed})
    return {"user_id_followed": user_id_followed, "followers_count": count}

@router.get("/followers/{user_id_followed}")
async def get_followers(user_id_followed: str, db=Depends(get_database)):
    followers = await follows_collection.find({"user_id_followed": user_id_followed}).to_list(None)
    return followers

@router.get("/following/{user_id_following}")
async def get_following(user_id_following: str, db=Depends(get_database)):
    following = await follows_collection.find({"user_id_following": user_id_following}).to_list(None)
    return following
