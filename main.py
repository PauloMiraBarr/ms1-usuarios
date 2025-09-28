from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mysql.connector
from typing import List
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Leer las variables de entorno
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')  
MYSQL_PORT = os.getenv('MYSQL_PORT', '3307')      
MYSQL_USER = os.getenv('MYSQL_USER', 'root')      
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'root')  
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'ms1_db')  

CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '*')  # Cargar los orígenes permitidos desde .env

# Función para obtener la conexión a la base de datos
def get_db_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        port=MYSQL_PORT
    )

# Función para crear la base de datos si no existe
def create_database_if_not_exists():
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            port=MYSQL_PORT
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DATABASE};")
        cursor.close()
        conn.close()
    except mysql.connector.Error as e:
        print(f"Error al crear la base de datos: {e}")

# Función para crear las tablas si no existen
def create_tables_if_not_exists():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Crear la tabla de usuarios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id_usuario INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(100),
                correo VARCHAR(100) UNIQUE,
                contraseña VARCHAR(255),
                telefono VARCHAR(15)
            );
        """)

        # Crear la tabla de direcciones
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS direcciones (
                id_direccion INT AUTO_INCREMENT PRIMARY KEY,
                id_usuario INT,
                direccion VARCHAR(255),
                ciudad VARCHAR(100),
                codigo_postal VARCHAR(10),
                FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE
            );
        """)

        cursor.close()
        conn.close()
    except mysql.connector.Error as e:
        print(f"Error al crear las tablas: {e}")

# Crear la instancia de FastAPI
app = FastAPI(
    title = "API de Gestión de Usuarios",
    description = "Esta API permite gestionar usuarios y direcciones.",
    version="1.0.0"
)

# Configurar el middleware CORS para permitir orígenes configurados en el .env
if CORS_ALLOWED_ORIGINS == '*':
    allowed_origins = ["*"]  # Permitir todos los orígenes
else:
    allowed_origins = CORS_ALLOWED_ORIGINS.split(",")  # Convertir la cadena en una lista

# Agregar el middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Usar los orígenes cargados desde el .env
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos HTTP
    allow_headers=["*"],  # Permitir todos los encabezados
)

# Pydantic models para validar datos
class Usuario(BaseModel):
    nombre: str
    correo: str
    contraseña: str
    telefono: str

class Direccion(BaseModel):
    id_usuario: int
    direccion: str
    ciudad: str
    codigo_postal: str

# Evento de inicio de FastAPI para asegurarse de que la base de datos y tablas están disponibles
@app.on_event("startup")
async def startup():
    create_database_if_not_exists()  # Crear la base de datos si no existe
    create_tables_if_not_exists()    # Crear las tablas si no existen

# Endpoints de Usuarios

# GET /usuarios/{id_usuario}
@app.get("/usuarios/{id_usuario}", response_model=Usuario)
def get_usuario(id_usuario: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE id_usuario = %s;", (id_usuario,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if result is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return result

# POST /usuarios
@app.post("/usuarios", response_model=Usuario)
def create_usuario(usuario: Usuario):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        INSERT INTO usuarios (nombre, correo, contraseña, telefono)
        VALUES (%s, %s, %s, %s);
    """, (usuario.nombre, usuario.correo, usuario.contraseña, usuario.telefono))
    conn.commit()
    cursor.execute("SELECT * FROM usuarios WHERE id_usuario = LAST_INSERT_ID();")
    new_usuario = cursor.fetchone()
    cursor.close()
    conn.close()
    return new_usuario

# PUT /usuarios/{id_usuario}
@app.put("/usuarios/{id_usuario}", response_model=Usuario)
def update_usuario(id_usuario: int, usuario: Usuario):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        UPDATE usuarios SET nombre = %s, correo = %s, contraseña = %s, telefono = %s
        WHERE id_usuario = %s;
    """, (usuario.nombre, usuario.correo, usuario.contraseña, usuario.telefono, id_usuario))
    conn.commit()
    cursor.execute("SELECT * FROM usuarios WHERE id_usuario = %s;", (id_usuario,))
    updated_usuario = cursor.fetchone()
    cursor.close()
    conn.close()
    if updated_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return updated_usuario

# DELETE /usuarios/{id_usuario}
@app.delete("/usuarios/{id_usuario}")
def delete_usuario(id_usuario: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id_usuario = %s;", (id_usuario,))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Usuario eliminado exitosamente"}

# Endpoints de Direcciones

# GET /direcciones/{id_usuario}
@app.get("/direcciones/{id_usuario}", response_model=List[Direccion])
def get_direcciones(id_usuario: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM direcciones WHERE id_usuario = %s;", (id_usuario,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

# POST /direcciones
@app.post("/direcciones", response_model=Direccion)
def create_direccion(direccion: Direccion):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        INSERT INTO direcciones (id_usuario, direccion, ciudad, codigo_postal)
        VALUES (%s, %s, %s, %s);
    """, (direccion.id_usuario, direccion.direccion, direccion.ciudad, direccion.codigo_postal))
    conn.commit()
    cursor.execute("SELECT * FROM direcciones WHERE id_direccion = LAST_INSERT_ID();")
    new_direccion = cursor.fetchone()
    cursor.close()
    conn.close()
    return new_direccion

# PUT /direcciones/{id_direccion}
@app.put("/direcciones/{id_direccion}", response_model=Direccion)
def update_direccion(id_direccion: int, direccion: Direccion):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        UPDATE direcciones SET direccion = %s, ciudad = %s, codigo_postal = %s
        WHERE id_direccion = %s;
    """, (direccion.direccion, direccion.ciudad, direccion.codigo_postal, id_direccion))
    conn.commit()
    cursor.execute("SELECT * FROM direcciones WHERE id_direccion = %s;", (id_direccion,))
    updated_direccion = cursor.fetchone()
    cursor.close()
    conn.close()
    if updated_direccion is None:
        raise HTTPException(status_code=404, detail="Dirección no encontrada")
    return updated_direccion

# DELETE /direcciones/{id_direccion}
@app.delete("/direcciones/{id_direccion}")
def delete_direccion(id_direccion: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM direcciones WHERE id_direccion = %s;", (id_direccion,))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Dirección eliminada exitosamente"}
