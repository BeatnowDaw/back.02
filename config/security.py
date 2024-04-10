from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
import logging
from prometheus_client import Counter
from config.db import usuarios_collection
from model.schema import UsuarioInDB

from datetime import datetime

# Configuración de la seguridad y autenticación OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
 
# Configuración de logs
logging.basicConfig(filename='app.log', level=logging.INFO)
 
# Configuración de Prometheus
requests_counter = Counter('requests_total', 'Total number of requests')

def verificar_contraseña(contraseña_plana, contraseña_hash):
    return pwd_context.verify(contraseña_plana, contraseña_hash)
 
 
def obtener_usuario(nombre_usuario: str):
    usuario = usuarios_collection.find_one({"nombre_usuario": nombre_usuario})
    if usuario:
        return UsuarioInDB(**usuario)
 
 
def guardar_log(evento):
    now = datetime.now()
    logging.info(f'{now} - {evento}')