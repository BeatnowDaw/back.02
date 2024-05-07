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

class Interactions(BaseModel):
    user_id: str = Field(alias="user_id")
    post_id: str = Field(alias="publication_id")
    like_date: Optional[datetime] = Field(default=None, alias="like_date")
    saved_date: Optional[datetime] = Field(default=None, alias="saved_date")
    dislike_date: Optional[datetime] = Field(default=None, alias="dislike_date")
    #user: UserInDB = Field(alias="user")



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




