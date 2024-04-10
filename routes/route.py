from model.schema import Usuario, Token
from config.security import oauth2_scheme, pwd_context, requests_counter, verificar_contraseña, obtener_usuario, guardar_log
from config.db import usuarios_collection
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import HTTPException, Depends, status, APIRouter

from prometheus_client import start_http_server, Counter

router = APIRouter()

@router.post("/api/v1/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    requests_counter.inc()
    usuario = obtener_usuario(form_data.username)
    if not usuario or not verificar_contraseña(form_data.password, usuario.contraseña):
        guardar_log(f"Intento de inicio de sesión fallido para usuario: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    guardar_log(f"Inicio de sesión exitoso para usuario: {form_data.username}")
    return {"access_token": form_data.username, "token_type": "bearer"}
 
 
# Endpoint para obtener información de usuario
@router.get("/api/v1/usuario/me")
async def obtener_usuario_actual(token: str = Depends(oauth2_scheme)):
    requests_counter.inc()
    return {"token": token}
 
 
# Endpoint para crear un nuevo usuario
@router.post("/api/v1/register")
async def register(usuario: Usuario):
    requests_counter.inc()
    usuario_encontrado = usuarios_collection.find_one({"nombre_usuario": usuario.nombre_usuario})
    if usuario_encontrado:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso")
    usuario_dict = usuario.dict()
    usuario_dict['contraseña'] = pwd_context.hash(usuario_dict['contraseña'])
    usuario_id = usuarios_collection.insert_one(usuario_dict).inserted_id
    return {"_id": str(usuario_id), **usuario.dict()}


