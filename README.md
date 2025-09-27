### **Microservicio 1: Gestión de Usuarios**

#### **Relaciones entre tablas**:

1. **Usuarios** → **Direcciones**: Relación 1:N. Un usuario puede tener varias direcciones asociadas.

#### **Tablas y relaciones**:

* **Usuarios** (1:N con Direcciones)

  * `id_usuario` (PK, INT, AUTO_INCREMENT)
  * `nombre` (VARCHAR(100))
  * `correo` (VARCHAR(100), UNIQUE)
  * `contraseña` (VARCHAR(255))
  * `telefono` (VARCHAR(15))

* **Direcciones**

  * `id_direccion` (PK, INT, AUTO_INCREMENT)
  * `id_usuario` (FK a Usuarios, INT)
  * `direccion` (VARCHAR(255))
  * `ciudad` (VARCHAR(100))
  * `codigo_postal` (VARCHAR(10))

#### **Endpoints**:

1. **Usuarios:**

   * `GET /usuarios/{id_usuario}`: Obtener detalles de un usuario.
   * `POST /usuarios`: Crear un nuevo usuario.
   * `PUT /usuarios/{id_usuario}`: Actualizar detalles de un usuario.
   * `DELETE /usuarios/{id_usuario}`: Eliminar un usuario.
2. **Direcciones:**

   * `GET /direcciones/{id_usuario}`: Obtener todas las direcciones de un usuario.
   * `POST /direcciones`: Agregar una nueva dirección.
   * `PUT /direcciones/{id_direccion}`: Actualizar una dirección existente.
   * `DELETE /direcciones/{id_direccion}`: Eliminar una dirección.
