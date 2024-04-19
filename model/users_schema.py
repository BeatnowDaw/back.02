from pydantic import BaseModel

class Usuario(BaseModel):
    fullname: str
    email: str
    username: str
    password: str

class UsuarioInDB(Usuario):
    _id: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UsuarioInLogin(BaseModel):
    username: str
    password: str
