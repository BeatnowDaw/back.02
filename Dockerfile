# backend/Dockerfile
FROM python:3.12

# Instalar los certificados raíz necesarios para SSL
RUN apt-get update && apt-get install -y ca-certificates
RUN update-ca-certificates

# Desactivar la verificación SSL a nivel de Python
RUN echo "export PYTHONWARNINGS='ignore:Unverified HTTPS request'" >> ~/.bashrc

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar el contenido del proyecto al contenedor
COPY . .

# Actualizar pip y instalar dependencias
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Comando para iniciar el servidor
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
