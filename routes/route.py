from model.schema import Usuario, Token, UsuarioInLogin
from config.security import oauth2_scheme, pwd_context, requests_counter, verificar_contraseña, obtener_usuario, guardar_log
from config.db import usuarios_collection
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import HTTPException, Depends, status, APIRouter

router = APIRouter()

@router.post("/api/v1/login")
async def login(user_data: UsuarioInLogin):
    usuario = usuarios_collection.find_one({"username": user_data.username})
    if not usuario:
        raise HTTPException(status_code=401, detail="Nombre de usuario o contraseña incorrectos")
    if not pwd_context.verify(user_data.password, usuario['password']):
        raise HTTPException(status_code=401, detail="Nombre de usuario o contraseña incorrectos")
    return {"message": "Inicio de sesión exitoso"}
 
 
@router.get("/api/v1/usuario/me")
async def obtener_usuario_actual(token: str = Depends(oauth2_scheme)):
    requests_counter.inc()
    return {"token": token}
 
 
@router.post("/api/v1/register", response_model=Usuario)
async def register(user: Usuario):
    requests_counter.inc()
    usuario_encontrado = usuarios_collection.find_one({"username": user.username})
    if usuario_encontrado:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso")
    password_hash = pwd_context.hash(user.password)
    user_dict = user.dict()
    user_dict['password'] = password_hash
    usuario_id = usuarios_collection.insert_one(user_dict).inserted_id
    return {"_id": str(usuario_id), **user_dict}
