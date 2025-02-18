
-- Tabla de roles (tipos de usuario)
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion TEXT
);

-- Tabla de usuarios
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(32) NOT NULL,
    rol_id INT REFERENCES roles(id) ON DELETE SET NULL,
    estado BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de permisos
CREATE TABLE permisos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT
);

-- Relación usuario-permisos
CREATE TABLE usuario_permisos (
    usuario_id INT REFERENCES usuarios(id) ON DELETE CASCADE,
    permiso_id INT REFERENCES permisos(id) ON DELETE CASCADE,
    PRIMARY KEY (usuario_id, permiso_id)
);

-- Tabla de materias primas
CREATE TABLE materias_primas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    unidad_medida VARCHAR(20),
    stock_actual DECIMAL(10,2),
    stock_minimo DECIMAL(10,2),
    precio DECIMAL(10,2),
    fecha_ingreso TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de productos
CREATE TABLE productos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    precio DECIMAL(10,2),
    stock DECIMAL(10,2),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de inventario
CREATE TABLE inventario (
    id SERIAL PRIMARY KEY,
    tipo VARCHAR(50) CHECK (tipo IN ('Materia Prima', 'Producto')),
    referencia_id INT NOT NULL,
    cantidad DECIMAL(10,2),
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de proveedores
CREATE TABLE proveedores (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    contacto VARCHAR(50),
    telefono VARCHAR(20),
    email VARCHAR(100)
);

-- Tabla de órdenes de producción
CREATE TABLE ordenes_produccion (
    id SERIAL PRIMARY KEY,
    producto_id INT REFERENCES productos(id) ON DELETE CASCADE,
    cantidad DECIMAL(10,2),
    fecha_inicio TIMESTAMP,
    fecha_fin TIMESTAMP,
    estado VARCHAR(50) CHECK (estado IN ('Pendiente', 'En Proceso', 'Finalizado')),
    usuario_id INT REFERENCES usuarios(id) ON DELETE SET NULL
);

-- Tabla de detalle de producción
CREATE TABLE detalle_produccion (
    id SERIAL PRIMARY KEY,
    orden_id INT REFERENCES ordenes_produccion(id) ON DELETE CASCADE,
    materia_prima_id INT REFERENCES materias_primas(id) ON DELETE SET NULL,
    cantidad_usada DECIMAL(10,2)
);

-- Tabla de maquinaria
CREATE TABLE maquinaria (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    modelo VARCHAR(50),
    estado VARCHAR(50) CHECK (estado IN ('Operativa', 'En Mantenimiento', 'Fuera de Servicio'))
);

-- Tabla de mantenimiento de maquinaria
CREATE TABLE mantenimiento (
    id SERIAL PRIMARY KEY,
    maquinaria_id INT REFERENCES maquinaria(id) ON DELETE CASCADE,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    descripcion TEXT,
    costo DECIMAL(10,2)
);

-- Tabla de clientes
CREATE TABLE clientes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    telefono VARCHAR(20),
    email VARCHAR(100),
    direccion TEXT
);


ALTER TABLE clientes ADD COLUMN usuario_id INT REFERENCES usuarios(id) ON DELETE SET NULL;

-- Tabla de pedidos de clientes
CREATE TABLE pedidos (
    id SERIAL PRIMARY KEY,
    cliente_id INT REFERENCES clientes(id) ON DELETE SET NULL,
    fecha_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado VARCHAR(50) CHECK (estado IN ('Pendiente', 'Enviado', 'Entregado', 'Cancelado'))
);

-- Detalle de pedidos
CREATE TABLE detalle_pedidos (
    id SERIAL PRIMARY KEY,
    pedido_id INT REFERENCES pedidos(id) ON DELETE CASCADE,
    producto_id INT REFERENCES productos(id) ON DELETE SET NULL,
    cantidad DECIMAL(10,2),
    precio DECIMAL(10,2)
);

-- Tabla de reportes
CREATE TABLE reportes (
    id SERIAL PRIMARY KEY,
    usuario_id INT REFERENCES usuarios(id) ON DELETE SET NULL,
    tipo VARCHAR(100),
    fecha_generacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de auditoría
CREATE TABLE auditoria (
    id SERIAL PRIMARY KEY,
    usuario_id INT REFERENCES usuarios(id) ON DELETE SET NULL,
    tabla_afectada VARCHAR(50),
    operacion VARCHAR(50),
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
