from fastapi import APIRouter
from fastapi.responses import FileResponse

# Iniciar router
router = APIRouter()

@router.get("/android-apk")  # Cambiado a método GET para facilitar la descarga
async def download_android_apk():
    # Ruta directa al archivo APK en el servidor
    apk_path = "http://172.203.251.28/beatnow/res/apks/android/beatnow.apk"
    return FileResponse(apk_path, media_type='application/vnd.android.package-archive', filename="beatnow.apk")
