from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, Field, validator
from datetime import datetime

class MusicBase(BaseModel):
    user_id: str = Field(alias="user_id")
    licenses: list[str] = Field(alias="license_id")
    bpm: int = Field(alias="bpm")
    genre_id: str = Field(alias="genre_id")
    moods: list[str] = Field(alias="moods")
    instruments: list[str] = Field(alias="instruments")
    tag_id: list[str] = Field(alias="tags")
    license_id: list[str] = Field(alias="licenses")

# Schemas de Usuarios
class User(BaseModel):
    full_name: Optional[str] = Field(alias="full_name")
    username: str = Field(alias="username")
    email: Optional[str] = Field(alias="email")
    password: Optional[str] = Field(alias="password")
    followers: Optional[list[str]] = Field(alias="followers")
    following: Optional[list[str]] = Field(alias="following")
    

class UserInDB(User):
    id: Optional[str] = Field(default=None, alias='_id')

    @validator('id', pre=True, always=True)
    def convert_id(cls, v):
        return str(v) if isinstance(v, ObjectId) else v

# Schemas de Publicaciones
class NewPost(BaseModel):
    title: Optional[str] = Field(alias="title")
    description: Optional[str] = Field(alias="description")

class Post(NewPost):
    user_id: str = Field(alias="user_id")
    publication_date: datetime = Field(alias="publication_date")
    #beat_info: MusicBase._id = Field(alias="beat_info")

class PostInDB(Post):
    id: str = Field(alias='_id')

    @validator('id', pre=True, always=True)
    def convert_id(cls, v):
        return str(v) if isinstance(v, ObjectId) else v

class PostShowed(PostInDB):
    likes: int = 0
    dislikes: int = 0
    saves: int = 0
    creator_username: Optional[str] = Field(default=None, alias="creator_username")
    isLiked: Optional[bool] = Field(default=False, alias="isLiked")
    isSaved: Optional[bool] = Field(default=False, alias="isSaved")

class Interactions(BaseModel):
    user_id: str = Field(alias="user_id")
    post_id: str = Field(alias="publication_id")
    like_date: Optional[datetime] = Field(default=None, alias="like_date")
    saved_date: Optional[datetime] = Field(default=None, alias="saved_date")
    dislike_date: Optional[datetime] = Field(default=None, alias="dislike_date")
    #user: UserInDB = Field(alias="user")

class NewLyrics(BaseModel):
    title: str = Field(alias="title")
    lyrics: str = Field(alias="lyrics")
    post_id: str = Field(alias="post_id")
    
class Lyrics(NewLyrics):
    user_id: str = Field(alias="user_id")
    
class LyricsInDB(Lyrics):
    id: str = Field(default=None,alias='_id')

    @validator('id', pre=True, always=True)
    def convert_id(cls, v):
        return str(v) if isinstance(v, ObjectId) else v

# Schemas para comprobar uso
'''
class Tag(BaseModel):
    name: str = Field(alias="name")

class LicenseType(BaseModel):
    license_type: str = Field(alias="license_type")
    description: str = Field(alias="description")

class License(BaseModel):
    license_type_id: str = Field(alias="license_type")
    user_description: str = Field(alias="user_description")
    post_id: str = Field(alias="post_id")
    price: float = Field(alias="price")

class Genre(BaseModel):
    name: str = Field(alias="name")
    description: str = Field(alias="description")

class Mood(BaseModel):
    name: str = Field(alias="name")
    description: str = Field(alias="description")

class Instrument(BaseModel):
    name: str = Field(alias="name")
    description: str = Field(alias="description")



class Purchase(BaseModel):
    buyer_user_id: str = Field(alias="user_id")
    owner_user_id: str = Field(alias="user_id")
    base_id: str = Field(alias="base_id")
    price: float = Field(alias="price")

'''




