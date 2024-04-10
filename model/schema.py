from pydantic import BaseModel

class Usuario(BaseModel):
    nombre: str
    apellidos: str
    edad: int
    nombre_usuario: str
    correo: str
    contraseña: str

class UsuarioInDB(Usuario):
    _id: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UsuarioInLogin(BaseModel):
    nombre_usuario: str
    contraseña: str
