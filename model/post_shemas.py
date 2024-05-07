from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, Field, validator
from datetime import datetime

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