from typing import Optional

import bson
from bson import ObjectId
from pydantic import BaseModel, Field, validator
from datetime import datetime

class Tags(BaseModel):
    name: str = Field(alias="name")


class User(BaseModel):
    name: str = Field(alias="name")
    last_name: str = Field(alias="last_name")
    age: int = Field(alias="age")
    username: str = Field(alias="username")
    email: str = Field(alias="email")
    password: str = Field(alias="password")
    disabled: bool = Field(alias="disabled")
    #posts: List[Post] = []
class UserInDB(User):
    id: Optional[str] = Field(default=None, alias='id')

    @validator('id', pre=True, always=True)
    def convert_id(cls, v):
        return str(v) if isinstance(v, ObjectId) else v
class Post(BaseModel):
    user_id: str = Field(alias="user_id")
    title: str = Field(alias="title")
    carpet_file: str = Field(alias="carpet_file")
    publication_date: datetime = Field(alias="publication_date")
    description: str = Field(alias="description")
    tags: list[Tags] = Field(alias="tags")


class PostInDB(Post):
    _id: str






