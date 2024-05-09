from datetime import timedelta
from email.header import Header
import os
from typing import Annotated, List
import shutil
from bson import ObjectId
from passlib.handlers.bcrypt import bcrypt
import bcrypt
from model.user_shemas import NewUser, User, UserProfile
from model.lyrics_shemas import Lyrics
from config.security import oauth2_scheme, guardar_log, SSH_USERNAME_RES, SSH_PASSWORD_RES, SSH_HOST_RES, \
    get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, get_user_id
from config.db import users_collection, interactions_collection, get_database, lyrics_collection, follows_collection, post_collection
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import File, HTTPException, Depends, UploadFile, status, APIRouter
import paramiko
from routes.follow_routes import get_followers, get_following
from routes.posts_routes import list_user_publications
import pymongo

# Iniciar router
router = APIRouter()

# Registro
@router.post("/register")
async def register(user: NewUser):
    # Check if the username is already taken
    existing_user = await users_collection.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # Hash the password before saving it
    password_hash = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    user_dict = user.dict()
    user_dict['password'] = password_hash
    result = await users_collection.insert_one(user_dict)
    with paramiko.SSHClient() as ssh:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SSH_HOST_RES, username=SSH_USERNAME_RES, password=SSH_PASSWORD_RES)

        username = user_dict['username']
        directory_commands = f"sudo mkdir -p /var/www/html/beatnow/{username}/photo_profile /var/www/html/beatnow/{username}/posts"
        stdin, stdout, stderr = ssh.exec_command(directory_commands)

        exit_status = stderr.channel.recv_exit_status()

        if exit_status != 0:
            raise HTTPException(status_code=500, detail="Error creating the folder on the remote server")
    return {"_id": str(result.inserted_id)}

@router.delete("/delete")
async def delete_user(current_user: NewUser = Depends(get_current_user), db=Depends(get_database)):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Conexión SSH
        with paramiko.SSHClient() as ssh:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=SSH_HOST_RES, username=SSH_USERNAME_RES, password=SSH_PASSWORD_RES)

            # Eliminar la carpeta del usuario en el servidor
            user_dir = f"/var/www/html/beatnow/{current_user.username}"
            ssh.exec_command(f"sudo rm -rf {user_dir}")

            # Verificar si la carpeta se borró correctamente
            _, stderr, _ = ssh.exec_command(f"test -d {user_dir}")
            if stderr.channel.recv_exit_status() == 0:
                raise HTTPException(status_code=500, detail="Error deleting user directory from server")

        # Obtener el ID del usuario
        user_id = await get_user_id(current_user.username)
        if not user_id:
            raise HTTPException(status_code=500, detail="User ID not found")

        # Obtener los IDs de los posts del usuario
        user_posts = await post_collection.find({"user_id": ObjectId(user_id)}, {"_id": 1}).to_list(None)
        post_ids = [post["_id"] for post in user_posts]
        #ELiminar los follows
        await follows_collection.delete_many({"user_id_following": user_id})
        await follows_collection.delete_many({"user_id_followed": user_id})
        #Eliminar las letras
        await lyrics_collection.delete_many({"user_id": user_id})
        # Eliminar todas las interacciones asociadas a los posts del usuario
        await interactions_collection.delete_many({"post_id": {"$in": post_ids}})
        await interactions_collection.delete_many({"user_id": user_id})
        # Eliminar todos los posts del usuario
        await post_collection.delete_many({"user_id": user_id})
        # Eliminar al usuario de la colección de usuarios
        delete_result = await users_collection.delete_one({"_id": ObjectId(user_id)})
        if delete_result.deleted_count == 1:
            print("User deleted successfully from database")
        else:
            print("User deletion failed or user not found in database")

        return {"message": "User deleted successfully"}

    except paramiko.AuthenticationException as e:
        raise HTTPException(status_code=500, detail="SSH authentication failed")
    except paramiko.SSHException as e:
        raise HTTPException(status_code=500, detail="SSH connection error")
    except paramiko.ssh_exception.NoValidConnectionsError as e:
        raise HTTPException(status_code=500, detail="No valid SSH connections available")
    except pymongo.errors.PyMongoError as e:
        raise HTTPException(status_code=500, detail="Database error: " + str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred: " + str(e))

# Recoger datos del usuario actual
@router.get("/users/me")
async def read_users_me(
    current_user: Annotated[NewUser, Depends(get_current_user)],
):
    return current_user

'''
#Listar todos los usuarios
@router.get("/users")
async def get_all_users(token: str = Depends(oauth2_scheme)):
    user = await get_current_user(token)  
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.username == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized",
        )

    all_users = await users_collection.find({}, {"username": 1, "_id": 0}).to_list(length=None)
    usernames = [user["username"] for user in all_users]
    return {"usernames": usernames}
'''
@router.post("/login")  # Additional route
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user_dict = await users_collection.find_one({"username": form_data.username})
    if not user_dict:
        guardar_log("Login failed - Incorrect username: " + form_data.username)
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    user = NewUser(**user_dict)
    if not bcrypt.checkpw(form_data.password.encode('utf-8'), user_dict['password']):
        guardar_log("Login failed - Incorrect password for username: " + form_data.username)
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password"
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    guardar_log("Login successful for username: " + form_data.username)
    return {"message": "ok"}

@router.get("/saved-posts")
async def get_saved_posts(current_user: NewUser = Depends(get_current_user), db=Depends(get_database)):
    user_id = await get_user_id(current_user.username)
    saved_posts = await interactions_collection.find({"user_id": user_id, "saved_date": {"$exists": True}}).to_list(None)
    
    # Convertir ObjectId a cadenas
    for post in saved_posts:
        post["_id"] = str(post["_id"])
    
    return {"saved_posts": saved_posts}


@router.get("/liked-posts")
async def get_liked_posts(current_user: NewUser = Depends(get_current_user), db=Depends(get_database)):
    user_id = await get_user_id(current_user.username)
    liked_posts = await interactions_collection.find({"user_id": user_id, "like_date": {"$exists": True}}).to_list(None)
    
    # Convertir ObjectId a cadenas
    for post in liked_posts:
        post["_id"] = str(post["_id"])
    
    return {"liked_posts": liked_posts}
'''
@router.get("/lyrics", response_model=List[Lyrics])
async def get_user_lyrics(current_user: NewUser = Depends(get_current_user), db=Depends(get_database)):
    user_id = await get_user_id(current_user.username)
    user_lyrics = await lyrics_collection.find({"user_id": user_id}).to_list(None)
    
    # Convertir ObjectId a cadenas
    for lyric in user_lyrics:
        lyric["_id"] = str(lyric["_id"])
    
    return user_lyrics
'''


@router.get("/profile/{user_id}", response_model=UserProfile)
async def get_user_lyrics(user_id: str, current_user: NewUser = Depends(get_current_user), db=Depends(get_database)):
    user_dict = await users_collection.find_one({"_id": ObjectId(user_id)})
    if user_dict:
        userindb = User(**user_dict)
        user_id_following = await get_user_id(current_user.username)
        if user_id_following==user_id:
            isFollowing = 0
        else:
            
            existing_follow = await follows_collection.find_one({"user_id_followed": user_id, "user_id_following": user_id_following})
            if existing_follow:
                isFollowing = 1
            else:
                isFollowing = -1
        profile = UserProfile(**userindb.dict(),_id=str(ObjectId(user_id)),  followers = await get_followers(user_id), following = await get_following(user_id),
                          post_num = await lyrics_collection.count_documents({"user_id": user_id}), post= await list_user_publications(user_id), is_following = isFollowing )
        return profile
    else:
        raise HTTPException(status_code=404, detail="User id not Found")

@router.post("/delete_photo_profile")
async def delete_photo_profile(current_user: NewUser = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Conexión SSH y eliminación de la foto de perfil del usuario en el servidor
        with paramiko.SSHClient() as ssh:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=SSH_HOST_RES, username=SSH_USERNAME_RES, password=SSH_PASSWORD_RES)

            user_photo_dir = f"/var/www/html/beatnow/{current_user.username}/photo_profile"
            ssh.exec_command(f"sudo rm -rf {user_photo_dir}/*")

            # Verificar si la carpeta se borró correctamente
            _, stderr, _ = ssh.exec_command(f"test -d {user_photo_dir}")
            if stderr.channel.recv_exit_status() == 0:
                raise HTTPException(status_code=500, detail="Error deleting user photo profile from server")

    except paramiko.SSHException as e:
        raise HTTPException(status_code=500, detail=f"SSH error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    return {"message": "Photo profile deleted successfully"}


@router.post("/change_photo_profile")
async def change_photo_profile(file: UploadFile = File(...), current_user: NewUser = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    root_path = "/var/www/html/beatnow"  # Ruta raíz donde se almacenan las fotos de perfil
    user_photo_dir = os.path.join(root_path, current_user.username, "photo_profile")  # Carpeta de fotos de perfil del usuario

    try:
        # Conexión SSH
        with paramiko.SSHClient() as ssh:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=SSH_HOST_RES, username=SSH_USERNAME_RES, password=SSH_PASSWORD_RES)

            # Verificar si el directorio del usuario existe, si no, crearlo
            if not ssh.exec_command(f"test -d {user_photo_dir}")[1].read():
                # Crear directorios en el servidor remoto
                ssh.exec_command(f"sudo mkdir -p {user_photo_dir}")
                ssh.exec_command(f"sudo chown -R $USER:$USER {user_photo_dir}")

            # Eliminar contenido existente en la carpeta de fotos de perfil del usuario
            ssh.exec_command(f"sudo rm -rf {user_photo_dir}/*")

            # Guardar la nueva foto de perfil con un nombre único y formato png
            file_path = os.path.join(user_photo_dir, "photo_profile.png")
            with ssh.open_sftp().file(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

    except paramiko.SSHException as e:
        raise HTTPException(status_code=500, detail=f"SSH error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    return {"message": "Photo profile updated successfully"}
