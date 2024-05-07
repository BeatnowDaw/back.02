from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, Field, validator

class User(BaseModel):
    full_name: Optional[str] = Field(alias="full_name")
    username: str = Field(alias="username")
    email: Optional[str] = Field(alias="email")
    password: Optional[str] = Field(alias="password")


class UserInDB(User):
    id: Optional[str] = Field(default=None, alias='_id')

    @validator('id', pre=True, always=True)
    def convert_id(cls, v):
        return str(v) if isinstance(v, ObjectId) else v

class UserInfo(UserInDB):
    followers: Optional[list[str]] = Field(alias="followers")
    following: Optional[list[str]] = Field(alias="following")