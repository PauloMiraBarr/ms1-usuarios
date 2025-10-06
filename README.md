### **Microservicio 1: Gestión de Usuarios**

Servicio REST construido con **FastAPI** para gestionar Usuarios y sus Direcciones.

Base de datos en **MySQL 8** con integridad referencial y eliminación en cascada de direcciones cuando se elimina un usuario.

#### **Relaciones entre tablas**:

1. **Usuarios** → **Direcciones**: Relación 1:N. Un usuario puede tener varias direcciones asociadas.

***Nota***: La tabla direcciones tiene una foreign key con `ON DELETE CASCADE`, lo que significa que al eliminar un usuario se eliminan automáticamente sus direcciones asociadas.

#### **Tablas y relaciones**:

* **Usuarios** (1:N con Direcciones)

  * `id_usuario` (PK, INT, AUTO_INCREMENT)
  * `nombre` (VARCHAR(100))
  * `correo` (VARCHAR(100), UNIQUE)
  * `contraseña` (VARCHAR(255))
  * `telefono` (VARCHAR(15))

* **Direcciones**

  * `id_direccion` (PK, INT, AUTO_INCREMENT)
  * `id_usuario` (FK a Usuarios, INT, con ON DELETE CASCADE)
  * `direccion` (VARCHAR(255))
  * `ciudad` (VARCHAR(100))
  * `codigo_postal` (VARCHAR(10))
 
#### Esquema Json

**Usuarios**
``` json
{
	"id_usuario": 1,
	"nombre": "Pepito",
	"correo": "peitos@mail.com",
	"contraseña": "la_increible_contrasenha_secreta_pepil",
	"telefono": 987654321
}
```

**Direcciones**
``` json
{
	"id_direccion": 1,
	"id_usuario": 1,
	"direccion": "Puente bello, 560",
	"ciudad": "Lima",
	"codigo_postal": "A4"
}
```

#### **DTO's (Pydantic Models)**

``` python
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
```

#### **Endpoints**:

- **SWAGGER UI**
 `GET /docs`: Devuelve la documentación en formato Swagger UI de FastAPI.

- **Healthcheck**

`GET /health`: Devuelve un mensaje y código 200 indicando que el backend está activo.

- **Autenticación**

`POST /login` body LoginRequest - response
`{ "id_usuario": 1, "nombre": "Juan", "correo": "user@correo.com", "telefono": "555-1234" }`

1. **Usuarios:**

   * `GET /all`: Obtener detalles de todos los usuarios.
   * `GET /usuarios/{id_usuario}`: Obtener detalles de un usuario.
   * `POST /usuarios`: Crear un nuevo usuario.
   * `PUT /usuarios/{id_usuario}`: Actualizar detalles de un usuario.
   * `DELETE /usuarios/{id_usuario}`: Eliminar un usuario.
2. **Direcciones:**

   * `GET /direcciones/{id_usuario}`: Obtener todas las direcciones de un usuario.
   * `POST /direcciones`: Agregar una nueva dirección.
   * `PUT /direcciones/{id_direccion}`: Actualizar una dirección existente.
   * `DELETE /direcciones/{id_direccion}`: Eliminar una dirección.

#### Variables de entorno (`.env`)
```
# FastAPI
FASTAPI_PORT=8000

# MySQL
MYSQL_HOST=
MYSQL_PORT=
MYSQL_USER=
MYSQL_PASSWORD=
MYSQL_DATABASE=

# CORS
CORS_ALLOWED_ORIGINS=*
```

#### Cómo corrrer

Instalar librerías necesarias para Python.

```
pip install fastapi
pip install uvicorn
pip install mysql-connector-python
pip install python-dotenv
```

Correr el programa.

```
uvicorn main:app --reload
```
