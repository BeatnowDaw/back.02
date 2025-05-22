from datetime import timedelta
from typing import Annotated, List, Literal, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from bson import ObjectId
import bcrypt
import paramiko

from config.db import (
    users_collection,
    post_collection,
    interactions_collection,
    lyrics_collection,
    follows_collection,
    get_database,
)
from config.security import (
    get_current_user,
    get_current_user_without_confirmation,
    get_user_id,
    guardar_log,
    SSH_HOST_RES,
    SSH_USERNAME_RES,
    SSH_PASSWORD_RES,
)
from routes.mail_routes import send_confirmation
from model.user_shemas import NewUser, UserInDB, UserProfile
from model.post_shemas import PostInDB
from model.lyrics_shemas import LyricsInDB
from routes.follow_routes import count_followers, count_following

router = APIRouter(prefix="/v1/api/users", tags=["Users"])

# --- Response Models ---
class AvailabilityResponse(BaseModel):
    status: Literal["ok", "ko"]
    detail: str

class MessageResponse(BaseModel):
    message: str

# --- Helper for SSH and email --
def _sync_provision_user(user_id: str, username: str) -> None:
    with paramiko.SSHClient() as ssh:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SSH_HOST_RES, username=SSH_USERNAME_RES, password=SSH_PASSWORD_RES)
        mkdir_cmd = f"sudo mkdir -p /var/www/beatnow/{user_id}/photo_profile /var/www/beatnow/{user_id}/posts"
        photo_cmd = f"sudo cp /var/www/beatnow/res/photo-profile.jpg /var/www/beatnow/{user_id}/photo_profile/photo_profile.png"
        ssh.exec_command(mkdir_cmd)
        ssh.exec_command(photo_cmd)
    send_confirmation(username)

async def _provision_user(background_tasks: BackgroundTasks, user_id: str, username: str):
    from starlette.concurrency import run_in_threadpool
    background_tasks.add_task(run_in_threadpool, _sync_provision_user, user_id, username)

# --- User Deletion ---
@router.delete("/delete", response_model=MessageResponse)
async def delete_user(
    current_user: Annotated[NewUser, Depends(get_current_user)],
    db=Depends(get_database)
):
    user_id = await get_user_id(current_user.username)
    if not user_id:
        raise HTTPException(status_code=500, detail="User ID not found")
    # Asynchronous cleanup
    await post_collection.delete_many({"user_id": user_id})
    await interactions_collection.delete_many({"user_id": user_id})
    await follows_collection.delete_many({"user_id_following": user_id})
    await follows_collection.delete_many({"user_id_followed": user_id})
    await lyrics_collection.delete_many({"user_id": user_id})
    await users_collection.delete_one({"_id": ObjectId(user_id)})
    return {"message": "User deleted successfully"}

# --- List User Publications ---
@router.get("/posts/{username}", response_model=List[PostInDB])
async def list_user_publications(
    username: str,
    current_user: Annotated[NewUser, Depends(get_current_user)],
    db=Depends(get_database)
):
    user_doc = await users_collection.find_one({"username": username})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    uid = str(user_doc["_id"])
    posts = await post_collection.find({"user_id": uid}).to_list(None)
    for p in posts:
        p["_id"] = str(p["_id"])
    return posts

# --- User Profile ---
@router.get("/profile/{user_id}", response_model=UserProfile)
async def get_user_profile(
    user_id: str,
    current_user: Annotated[NewUser, Depends(get_current_user)],
    db=Depends(get_database)
):
    doc = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="User not found")
    user_obj = UserInDB(**doc)
    followers = await count_followers(user_id) or {"followers_count": 0}
    following = await count_following(user_id) or {"following_count": 0}
    post_count = await post_collection.count_documents({"user_id": user_id})
    is_following = await follows_collection.find_one({
        "user_id_followed": user_id,
        "user_id_following": await get_user_id(current_user.username)
    }) is not None
    return UserProfile(
        **user_obj.dict(),
        _id=user_id,
        followers=followers["followers_count"],
        following=following["following_count"],
        post_num=post_count,
        is_following=is_following
    )

# --- Update User ---
@router.put("/update", response_model=MessageResponse)
async def update_user(
    user_update: UserInDB,
    current_user: Annotated[NewUser, Depends(get_current_user)],
    db=Depends(get_database)
):
    doc = await users_collection.find_one({"username": current_user.username})
    if str(doc["_id"]) != user_update.id:
        raise HTTPException(status_code=400, detail="Cannot update other user")
    pwd_hash = bcrypt.hashpw(user_update.password.encode('utf-8'), bcrypt.gensalt())
    data = user_update.dict(exclude_none=True)
    data['password'] = pwd_hash
    await users_collection.update_one({"_id": ObjectId(user_update.id)}, {"$set": data})
    return {"message": "User updated successfully"}

# --- Current User Info ---
@router.get("/me", response_model=UserProfile)
async def read_users_me(
    current_user_data: Annotated[NewUser, Depends(get_current_user_without_confirmation)],
):
    # Buscar el usuario completo en la base de datos
    user = await users_collection.find_one({"username": current_user_data.username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_id = str(user["_id"])

    # Contar seguidores y seguidos
    from routes.follow_routes import count_followers, count_following
    followers_data = await count_followers(user_id)
    following_data = await count_following(user_id)

    followers = followers_data.get("followers_count", 0) if isinstance(followers_data, dict) else 0
    following = following_data.get("following_count", 0) if isinstance(following_data, dict) else 0

    # Contar publicaciones
    post_num = await post_collection.count_documents({"user_id": user_id})

    # Retornar perfil
    return UserProfile(
        id=user_id,
        full_name=user.get("full_name"),
        username=user.get("username"),
        email=user.get("email"),
        password=user.get("password"),
        is_active=user.get("is_active", False),
        bio=user.get("bio"),
        followers=followers,
        following=following,
        post_num=post_num,
        is_following=True
    )

# --- Saved & Liked Posts ---
@router.get("/saved-posts")
async def get_saved_posts(
    current_user: Annotated[NewUser, Depends(get_current_user)]
):
    uid = await get_user_id(current_user.username)
    saved = await interactions_collection.find({"user_id": uid, "saved_date": {"$exists": True}}).to_list(None)
    for s in saved: s["_id"] = str(s["_id"])
    return {"saved_posts": saved}

@router.get("/liked-posts")
async def get_liked_posts(
    current_user: Annotated[NewUser, Depends(get_current_user)]
):
    uid = await get_user_id(current_user.username)
    liked = await interactions_collection.find({"user_id": uid, "like_date": {"$exists": True}}).to_list(None)
    for l in liked: l["_id"] = str(l["_id"])
    return {"liked_posts": liked}

# --- User Lyrics ---
@router.get("/lyrics", response_model=List[LyricsInDB])
async def get_user_lyrics(
    current_user: Annotated[NewUser, Depends(get_current_user)]
):
    uid = await get_user_id(current_user.username)
    lyrics = await lyrics_collection.find({"user_id": uid}).to_list(None)
    for ly in lyrics: ly["_id"] = str(ly["_id"])
    return lyrics

# --- Photo Profile ---
@router.delete("/delete_photo_profile", response_model=MessageResponse)
async def delete_photo_profile(
    current_user: Annotated[NewUser, Depends(get_current_user)]
):
    uid = await get_user_id(current_user.username)
    cmd = f"sudo cp /var/www/html/res/photo-profile.jpg /var/www/html/beatnow/{uid}/photo_profile/photo_profile.png"
    try:
        with paramiko.SSHClient() as ssh:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(SSH_HOST_RES, SSH_USERNAME_RES, SSH_PASSWORD_RES)
            _, stdout, stderr = ssh.exec_command(cmd)
            if stderr.channel.recv_exit_status() != 0:
                raise Exception(stderr.read().decode())
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to reset photo profile")
    return {"message": "Photo profile reset successfully"}

@router.put("/change_photo_profile")
async def change_photo_profile(file: UploadFile = File(...), current_user: NewUser = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = await get_user_id(current_user.username)
    user_photo_dir = f"/var/www/html/beatnow/{user_id}/photo_profile"
    
    try:
        # Establish SSH connection
        with paramiko.SSHClient() as ssh:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=SSH_HOST_RES, username=SSH_USERNAME_RES, password=SSH_PASSWORD_RES)

            # Verify if the user's directory exists, if not, create it
            mkdir_command = f"test -d {user_photo_dir} || sudo mkdir -p {user_photo_dir}"
            stdin, stdout, stderr = ssh.exec_command(mkdir_command)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                error_message = stderr.read().decode()
                raise HTTPException(status_code=500, detail=f"Failed to create directory: {error_message}")
            
            # Ensure the correct permissions
            chown_command = f"sudo chown -R $USER:$USER {user_photo_dir}"
            stdin, stdout, stderr = ssh.exec_command(chown_command)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                error_message = stderr.read().decode()
                raise HTTPException(status_code=500, detail=f"Failed to set permissions: {error_message}")

            # Remove existing content in the user's profile photo folder
            rm_command = f"sudo rm -rf {user_photo_dir}/*"
            stdin, stdout, stderr = ssh.exec_command(rm_command)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                error_message = stderr.read().decode()
                raise HTTPException(status_code=500, detail=f"Failed to remove existing files: {error_message}")

            # Save the new profile photo with a unique name and png format
            sftp = ssh.open_sftp()
            file_path = os.path.join(user_photo_dir, "photo_profile.png")
            with sftp.open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            sftp.close()

    except paramiko.SSHException as e:
        raise HTTPException(status_code=500, detail=f"SSH error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    return {"message": "Photo profile updated successfully"}

# --- Availability Endpoints ---
@router.get("/check-availability/{field}", response_model=AvailabilityResponse)
async def check_availability(
    field: Literal["email", "username"],
    email: Optional[str] = None,
    username: Optional[str] = None,
):
    value = email if field == "email" else username
    if not value:
        raise HTTPException(status_code=400, detail="Missing query parameter")
    try:
        exists = await users_collection.find_one({field: value})
    except Exception:
        raise HTTPException(status_code=500, detail="Error checking availability")
    if exists:
        return {"status": "ko", "detail": f"{field.capitalize()} already registered"}
    return {"status": "ok", "detail": f"{field.capitalize()} is available"}

@router.get("/check-email", response_model=AvailabilityResponse)
async def check_email(email: str):
    return await check_availability("email", email=email)

@router.get("/check-username", response_model=AvailabilityResponse)
async def check_username(username: str):
    return await check_availability("username", username=username)