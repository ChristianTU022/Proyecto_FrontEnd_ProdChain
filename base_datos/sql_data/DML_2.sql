INSERT INTO roles (nombre, descripcion) VALUES 
('Administrador', 'Acceso completo al sistema'),
('Gerente', 'Gestión de producción e inventarios'),
('Operador', 'Supervisión de la producción'),
('Cliente', 'Acceso a pedidos y facturación');


INSERT INTO usuarios (nombre, email, password_hash, rol_id, estado) VALUES 
('Carlos Pérez', 'carlos.perez@empresa.com',MD5('Admin123'), 1, TRUE),
('Maria Rodríguez', 'maria.rodriguez@empresa.com', MD5('Admin123'), 2, TRUE),
('Juan López', 'juan.lopez@empresa.com', MD5('Admin123'), 3, TRUE),
('Luis Gómez', 'luis.gomez@cliente.com', MD5('Admin123'), 4, TRUE);


INSERT INTO permisos (nombre, descripcion) VALUES 
('GESTION_USUARIOS', 'Permiso para gestionar usuarios'),
('GESTION_INVENTARIO', 'Permiso para administrar el inventario'),
('GESTION_PRODUCCION', 'Permiso para administrar la producción'),
('VER_REPORTES', 'Permiso para visualizar reportes');


INSERT INTO usuario_permisos (usuario_id, permiso_id) VALUES 
(1, 1), (1, 2), (1, 3), (1, 4), -- Admin tiene todos los permisos
(2, 2), (2, 3), (2, 4),         -- Gerente tiene permisos específicos
(3, 3),                         -- Operador solo supervisa producción
(4, 4);                         -- Cliente solo visualiza reportes


INSERT INTO materias_primas (nombre, descripcion, unidad_medida, stock_actual, stock_minimo, precio) VALUES 
('Harina de trigo', 'Harina refinada para producción', 'Kg', 500, 100, 1.5),
('Huevos líquidos', 'Huevos pasteurizados para pasta', 'Litros', 300, 50, 3.0),
('Agua purificada', 'Agua tratada para producción', 'Litros', 1000, 200, 0.5);


INSERT INTO productos (nombre, descripcion, precio, stock) VALUES 
('Pasta corta', 'Pasta tipo penne', 5.00, 200),
('Pasta larga', 'Pasta tipo spaghetti', 4.50, 150),
('Pasta integral', 'Pasta con harina integral', 6.00, 100);


INSERT INTO inventario (tipo, referencia_id, cantidad) VALUES 
('Materia Prima', 1, 500),
('Materia Prima', 2, 300),
('Producto', 1, 200),
('Producto', 2, 150);


INSERT INTO proveedores (nombre, contacto, telefono, email) VALUES 
('Molinos San Jorge', 'Pedro Sánchez', '3015678900', 'pedro@molinosjorge.com'),
('Avícolas de Occidente', 'Ana Martínez', '3027788990', 'ana@avicolas.com'),
('Agua Pura S.A.', 'Carlos Rivas', '3154445566', 'carlos@aguapura.com');


INSERT INTO ordenes_produccion (producto_id, cantidad, fecha_inicio, fecha_fin, estado, usuario_id) VALUES 
(1, 100, '2024-01-01', '2024-01-02', 'Finalizado', 2),
(2, 150, '2024-02-10', '2024-02-12', 'En Proceso', 3),
(3, 50, '2024-03-05', '2024-03-06', 'Pendiente', 2);


INSERT INTO detalle_produccion (orden_id, materia_prima_id, cantidad_usada) VALUES 
(1, 1, 100),
(1, 2, 30),
(2, 1, 150),
(3, 3, 20);


INSERT INTO maquinaria (nombre, modelo, estado) VALUES 
('Mezcladora Industrial', 'MX-500', 'Operativa'),
('Secadora Automática', 'SD-300', 'En Mantenimiento'),
('Empacadora', 'EP-100', 'Operativa');


INSERT INTO mantenimiento (maquinaria_id, fecha, descripcion, costo) VALUES 
(2, '2024-01-15', 'Revisión de motor y sensores', 500.00),
(3, '2024-02-20', 'Cambio de piezas desgastadas', 700.00);


INSERT INTO clientes (nombre, telefono, email, direccion) VALUES 
('Supermercado XYZ', '3112233445', 'contacto@superxyz.com', 'Calle 123, Bogotá'),
('Distribuidora Alimentos', '3205566778', 'ventas@distribalimentos.com', 'Avenida 456, Medellín');


INSERT INTO pedidos (cliente_id, fecha_pedido, estado) VALUES 
(1, '2024-03-01', 'Pendiente'),
(2, '2024-03-02', 'Enviado');


INSERT INTO detalle_pedidos (pedido_id, producto_id, cantidad, precio) VALUES 
(1, 1, 50, 5.00),
(1, 2, 30, 4.50),
(2, 3, 40, 6.00);


INSERT INTO reportes (usuario_id, tipo, fecha_generacion) VALUES 
(1, 'Reporte de Producción', '2024-03-01'),
(2, 'Reporte de Inventario', '2024-03-02');


INSERT INTO auditoria (usuario_id, tabla_afectada, operacion, fecha) VALUES 
(1, 'ordenes_produccion', 'INSERT', '2024-01-01'),
(2, 'productos', 'UPDATE', '2024-02-10');



DROP FUNCTION IF EXISTS calcular_costo_orden(INT);

CREATE OR REPLACE FUNCTION calcular_costo_orden(_orden_id INT)
RETURNS DECIMAL AS $$
DECLARE
    total_costo DECIMAL := 0;
BEGIN
    SELECT SUM(mp.precio * dp.cantidad_usada)
    INTO total_costo
    FROM detalle_produccion dp
    JOIN materias_primas mp ON dp.materia_prima_id = mp.id
    WHERE dp.orden_id = _orden_id;  -- Se usa un alias (_orden_id) para evitar conflicto

    RETURN COALESCE(total_costo, 0);
END;
$$ LANGUAGE plpgsql;


SELECT calcular_costo_orden(1);
