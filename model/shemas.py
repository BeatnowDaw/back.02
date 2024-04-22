from typing import List,Dict, Any
from bson import ObjectId
from pydantic import BaseModel, Field
from datetime import datetime
from bson import ObjectId
'''
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError('Invalid ObjectId')
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, schema):
        schema['type'] = 'string'

class User(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias='_id')
    name: str = Field(alias="name")
    last_name: str = Field(alias="last_name")
    age: int = Field(alias="age")
    username: str = Field(alias="username")
    email: str = Field(alias="email")
    password: str = Field(alias="password")
    disabled: bool = Field(alias="disabled")
    posts: List['Post'] = []

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }

class Post(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias='_id')
    title: str = Field(alias="title")
    carpet_file: str = Field(alias="carpet_file")
    publication_date: datetime = Field(alias="publication_date")
    description: str = Field(alias="description")
    user_id: PyObjectId  # Referencia al ID del usuario
    tags: List[str] = Field(alias="tags")

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }

'''
class Post(BaseModel):
    user_id: str = Field(alias="user_id")
    title: str = Field(alias="title")
    carpet_file: str = Field(alias="carpet_file")
    publication_date: datetime = Field(alias="publication_date")
    description: str = Field(alias="description")
    tags: list = Field(alias="tags")


class PostInDB(Post):
    _id: str


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
    _id: str

