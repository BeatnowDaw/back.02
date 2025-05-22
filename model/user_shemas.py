from typing import List, Optional
from bson import ObjectId
from pydantic import BaseModel, Field, validator

class NewUser(BaseModel):
    full_name: Optional[str]
    username: str
    email: Optional[str]
    password: Optional[str]
    is_active: Optional[bool] = False

class User(NewUser):
    bio: Optional[str] = None

class UserInDB(User):
    id: Optional[str] = None

    @validator('id', pre=True, always=True)
    def convert_id(cls, v, values, **kwargs):
        # Si el ID viene como ObjectId o desde MongoDB como "_id"
        if not v and '_id' in values:
            return str(values['_id'])
        return str(v) if isinstance(v, ObjectId) else v

class UserProfile(UserInDB):
    followers: int
    following: int
    post_num: int
    is_following: bool

class UserInfo(UserInDB):
    followers: Optional[List[str]]
    following: Optional[List[str]]

class UserSearch(BaseModel):
    username: str
