# Usar una imagen oficial de Python como base
FROM python:3.12-slim

# Estableces el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar los archivos del proyecto al contenedor
COPY main.py /app/

# Copiar el archivo .env al contenedor
COPY .env /app/.env

# Instalar las dependencias necesarias
RUN pip install --no-cache-dir fastapi uvicorn mysql-connector-python
RUN pip install python-dotenv

# Exponer el puerto en el que FastAPI corre
EXPOSE 8000

# Comando para correr la app de FastAPI con Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
