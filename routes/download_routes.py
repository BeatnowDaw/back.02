from fastapi import APIRouter
from fastapi.responses import FileResponse
import paramiko

from config.security import SSH_HOST_RES, SSH_PASSWORD_RES, SSH_USERNAME_RES

# Iniciar router
router = APIRouter()

APK_DIRECTORY= "/beatnow/res/apks/android/"
@router.get("/android-apk")  # Cambiado a método GET para facilitar la descarga
async def download_android_apk():
    # Ruta directa al archivo APK en el servidor
    apk_path = "http://172.203.251.28/beatnow/res/apks/android/beatnow.apk"
    return FileResponse(apk_path, media_type='application/vnd.android.package-archive', filename="beatnow.apk")


@router.get("/latest-apk")
async def download_latest_apk():
    # Iniciar la conexión SSH
    with paramiko.SSHClient() as ssh:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SSH_HOST_RES, username=SSH_USERNAME_RES, password=SSH_PASSWORD_RES)

        # Comando para listar archivos y obtener el más reciente
        stdin, stdout, stderr = ssh.exec_command(f"ls -t {APK_DIRECTORY}/*.apk")
        latest_apk = stdout.readline().strip()  # Lee el primer resultado que es el más reciente

        if latest_apk:
            full_path = f"http://{SSH_HOST_RES}{APK_DIRECTORY}/{latest_apk}"
            return FileResponse(full_path, media_type='application/vnd.android.package-archive', filename=latest_apk)
        else:
            return {"error": "No APK found"}