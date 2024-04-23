from typing import Optional

import bson
from bson import ObjectId
from pydantic import BaseModel, Field, validator
from datetime import datetime

class Tag(BaseModel):
    name: str = Field(alias="name")


class User(BaseModel):
    name: str = Field(alias="name")
    last_name: str = Field(alias="last_name")
    age: int = Field(alias="age")
    username: str = Field(alias="username")
    email: str = Field(alias="email")
    password: str = Field(alias="password")
    disabled: bool = Field(alias="disabled")

class UserInDB(User):
    id: Optional[str] = Field(default=None, alias='id')

    @validator('id', pre=True, always=True)
    def convert_id(cls, v):
        return str(v) if isinstance(v, ObjectId) else v


class Interactions(BaseModel):
    user_id: str = Field(alias="user_id")
    post_id: str = Field(alias="publication_id")
    like_date: Optional[datetime] = Field(default=None, alias="like_date")
    saved_date: Optional[datetime] = Field(default=None, alias="saved_date")
    dislike_date: Optional[datetime] = Field(default=None, alias="dislike_date")

class LicenseType(BaseModel):
    license_type: str = Field(alias="license_type")
    description: str = Field(alias="description")
class License(BaseModel):
    license_type_id: LicenseType = Field(alias="license_type")
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
class MusicBase(BaseModel):
    user_id: str = Field(alias="user_id")
    licenses: list[License] = Field(alias="license_id")
    bpm: int = Field(alias="bpm")
    genre_id: str = Field(alias="genre_id")
    moods: list[Mood] = Field(alias="moods")
    instruments: list[Instrument] = Field(alias="instruments")
    tag_id: list[Tag] = Field(alias="tags")
    license_id: list[License] = Field(alias="licenses")
class Purchase(BaseModel):
    buyer_user_id: str = Field(alias="user_id")
    owner_user_id: str = Field(alias="user_id")
    base_id: str = Field(alias="base_id")
    price: float = Field(alias="price")

class Post(BaseModel):
    user_id: str = Field(alias="user_id")
    publication_date: datetime = Field(alias="publication_date")
    title: str = Field(alias="title")
    description: str = Field(alias="description")
    beat_info: MusicBase = Field(alias="beat_info")

class PostInDB(Post):
    _id: str




