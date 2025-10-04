from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import mysql.connector
from typing import List
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import os

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Leer las variables de entorno
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')  # Si no existe, usar 'localhost'
MYSQL_PORT = os.getenv('MYSQL_PORT', '3307')      # Si no existe, usar 3307
MYSQL_USER = os.getenv('MYSQL_USER', 'root')      # Si no existe, usar 'root'
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'root')  # Si no existe, usar 'root'
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'ms1_db')  # Nombre de la base de datos

FASTAPI_PORT = os.getenv('FASTAPI_PORT', '8000')  # Si no existe, usar 8000

CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '*')

# Conexión a la base de datos
def get_db_connection():
    try:
        return mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            port=MYSQL_PORT  # Puerto donde está MySQL (lo configuramos en el contenedor)
        )
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Error al conectar con la base de datos: {err}")


# Crear la instacia de FastAPI con título, descipción y versión personalizada
app = FastAPI(
    title = "API de Gestión de Usuarios",
    description = "Esta API permite gestionar usuarios y derecciones.",
    version="1.0.0"
)



# Creación de los esquemas y tablas para el microservicio 1 ----

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

# Evento de inicio de FastAPI para asegurarse de que la base de datos y tablas están disponibles
@app.on_event("startup")
async def startup():
    create_database_if_not_exists()  # Crear la base de datos si no existe
    create_tables_if_not_exists()    # Crear las tablas si no existen
# --------------------------------------------------------------




if CORS_ALLOWED_ORIGINS == '*':
    allowed_origins = ["*"]
else:
    allowed_origins = CORS_ALLOWED_ORIGINS.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
)

# Pydantic models para validar datos
class LoginRequest(BaseModel):
    correo: str
    contraseña: str

class UsuarioRequest(BaseModel):
    nombre: str
    correo: str
    contraseña: str
    telefono: str

class UsuarioResponse(BaseModel):
    id_usuario: int
    nombre: str
    correo: str
    contraseña: str
    telefono: str


class DireccionRequest(BaseModel):
    id_usuario: int
    direccion: str
    ciudad: str
    codigo_postal: str

class DireccionResponse(BaseModel):
    id_direccion: int
    id_usuario: int
    direccion: str
    ciudad: str
    codigo_postal: str


# Endpoint de prueba
@app.get("/health")
def health():
    return {"message": "¡Backend funcionando correctamente!"}



@app.post("/login")
async def login(request: LoginRequest):
    # Obtener la conexión a la base de datos
    connection = get_db_connection()
    cursor = connection.cursor()

    # Buscar al usuario por correo
    cursor.execute(
        "SELECT id_usuario, nombre, correo, contraseña, telefono FROM usuarios WHERE correo = %s", 
        (request.correo,)
    )
    usuario = cursor.fetchone()

    # Cerrar la conexión
    cursor.close()
    connection.close()

    if not usuario:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    # Verificar si la contraseña coincide
    if request.contraseña != usuario[3]:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    # Armar respuesta sin la contraseña
    user_data = {
        "id_usuario": usuario[0],
        "nombre": usuario[1],
        "correo": usuario[2],
        "telefono": usuario[4]
    }

    return JSONResponse(content=user_data, status_code=200)

    
# Endpoints de Usuarios

# GET /usuarios/all
@app.get("/usuarios/all", response_model=List[UsuarioResponse])
def get_all_usuarios():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios;")
    usuarios = cursor.fetchall()
    cursor.close()
    conn.close()

    if not usuarios:
        raise HTTPException(status_code=404, detail="No se encontraron usuarios.")

    return [UsuarioResponse(**usuario) for usuario in usuarios]


# GET /usuarios/{id_usuario}
@app.get("/usuarios/{id_usuario}", response_model=UsuarioResponse)
def get_usuario(id_usuario: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE id_usuario = %s;", (id_usuario,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if result is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return UsuarioResponse(**result)


# POST /usuarios
@app.post("/usuarios", response_model=UsuarioResponse)
def create_usuario(usuario: UsuarioRequest):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Verificar si el correo ya existe
    cursor.execute("SELECT correo FROM usuarios WHERE correo = %s", (usuario.correo,))
    existing_user = cursor.fetchone()
    
    if existing_user:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="El correo electrónico ya está registrado.")
    
    try:
        # Insertar el nuevo usuario
        cursor.execute("""
            INSERT INTO usuarios (nombre, correo, contraseña, telefono)
            VALUES (%s, %s, %s, %s);
        """, (usuario.nombre, usuario.correo, usuario.contraseña, usuario.telefono))
        conn.commit()
        
        # Obtener el nuevo usuario insertado
        cursor.execute("SELECT * FROM usuarios WHERE id_usuario = LAST_INSERT_ID();")
        new_usuario = cursor.fetchone()
        cursor.close()
        conn.close()

        return UsuarioResponse(**new_usuario)

    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Error al realizar la consulta: {err}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")


# PUT /usuarios/{id_usuario}
@app.put("/usuarios/{id_usuario}", response_model=UsuarioResponse)
def update_usuario(id_usuario: int, usuario: UsuarioRequest):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id_usuario FROM usuarios WHERE id_usuario = %s", (id_usuario,))
    user_exists = cursor.fetchone()

    if not user_exists:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    
    cursor.execute("SELECT id_usuario FROM usuarios WHERE correo = %s AND id_usuario != %s", (usuario.correo, id_usuario))
    existing_user = cursor.fetchone()

    if existing_user:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="El correo electrónico ya está registrado.")

    try:
        # Actualizar el usuario
        cursor.execute("""
            UPDATE usuarios SET nombre = %s, correo = %s, contraseña = %s, telefono = %s
            WHERE id_usuario = %s;
        """, (usuario.nombre, usuario.correo, usuario.contraseña, usuario.telefono, id_usuario))
        conn.commit()

        # Obtener el usuario actualizado
        cursor.execute("SELECT * FROM usuarios WHERE id_usuario = %s;", (id_usuario,))
        updated_usuario = cursor.fetchone()

        cursor.close()
        conn.close()

        if updated_usuario is None:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        return UsuarioResponse(**updated_usuario)

    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Error al realizar la consulta: {err}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")



# DELETE /usuarios/{id_usuario}
@app.delete("/usuarios/{id_usuario}")
def delete_usuario(id_usuario: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id_usuario, nombre, correo, contraseña, telefono FROM usuarios WHERE id_usuario = %s", (id_usuario,))
    user_exists = cursor.fetchone()
    
    if not user_exists:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    try:
        cursor.execute("DELETE FROM usuarios WHERE id_usuario = %s;", (id_usuario,))
        conn.commit()
        cursor.close()
        conn.close()

        # Devolver los detalles del usuario eliminado
        return JSONResponse(
            status_code=200,
            content={"message": "Usuario eliminado correctamente"}
        )

    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Error al realizar la consulta: {err}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")



# Endpoints de Direcciones

# GET /direcciones/{id_usuario}
@app.get("/direcciones/{id_usuario}", response_model=List[DireccionResponse])
def get_direcciones(id_usuario: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM direcciones WHERE id_usuario = %s;", (id_usuario,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()

    if not result:
        raise HTTPException(status_code=404, detail="No se encontraron direcciones para este usuario.")

    return [DireccionResponse(**direccion) for direccion in result]


# POST /direcciones
@app.post("/direcciones", response_model=DireccionResponse)
def create_direccion(direccion: DireccionRequest):
    # Verificar que el usuario exista
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id_usuario FROM usuarios WHERE id_usuario = %s;", (direccion.id_usuario,))
    usuario = cursor.fetchone()

    if not usuario:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="El usuario especificado no existe.")

    # Insertar la nueva dirección
    cursor.execute("""
        INSERT INTO direcciones (id_usuario, direccion, ciudad, codigo_postal)
        VALUES (%s, %s, %s, %s);
    """, (direccion.id_usuario, direccion.direccion, direccion.ciudad, direccion.codigo_postal))
    conn.commit()

    # Obtener la nueva dirección insertada
    cursor.execute("SELECT * FROM direcciones WHERE id_direccion = LAST_INSERT_ID();")
    new_direccion = cursor.fetchone()
    cursor.close()
    conn.close()

    return DireccionResponse(**new_direccion)


# PUT /direcciones/{id_direccion}
@app.put("/direcciones/{id_direccion}", response_model=DireccionResponse)
def update_direccion(id_direccion: int, direccion: DireccionRequest):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Verificar que la dirección exista
    cursor.execute("SELECT * FROM direcciones WHERE id_direccion = %s;", (id_direccion,))
    existing_direccion = cursor.fetchone()

    if not existing_direccion:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Dirección no encontrada.")

    # Verificar que el usuario exista
    cursor.execute("SELECT id_usuario FROM usuarios WHERE id_usuario = %s;", (direccion.id_usuario,))
    usuario = cursor.fetchone()

    if not usuario:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="El usuario especificado no existe.")

    # Actualizar la dirección
    cursor.execute("""
        UPDATE direcciones SET direccion = %s, ciudad = %s, codigo_postal = %s
        WHERE id_direccion = %s;
    """, (direccion.direccion, direccion.ciudad, direccion.codigo_postal, id_direccion))
    conn.commit()

    # Obtener la dirección actualizada
    cursor.execute("SELECT * FROM direcciones WHERE id_direccion = %s;", (id_direccion,))
    updated_direccion = cursor.fetchone()
    cursor.close()
    conn.close()

    if updated_direccion is None:
        raise HTTPException(status_code=404, detail="Dirección no encontrada.")

    return DireccionResponse(**updated_direccion)



# DELETE /direcciones/{id_direccion}
@app.delete("/direcciones/{id_direccion}")
def delete_direccion(id_direccion: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Verificar que la dirección exista
    cursor.execute("SELECT * FROM direcciones WHERE id_direccion = %s;", (id_direccion,))
    direccion_exists = cursor.fetchone()

    if not direccion_exists:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Dirección no encontrada.")

    # Eliminar la dirección
    cursor.execute("DELETE FROM direcciones WHERE id_direccion = %s;", (id_direccion,))
    conn.commit()
    cursor.close()
    conn.close()

    return {"message": "Dirección eliminada exitosamente"}
