CREATE OR REPLACE FUNCTION actualizar_stock_produccion()
RETURNS TRIGGER AS $$
BEGIN
    -- Descontar la cantidad de materia prima utilizada en el inventario
    UPDATE materias_primas
    SET stock_actual = stock_actual - NEW.cantidad_usada
    WHERE id = NEW.materia_prima_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para actualizar stock al insertar detalle de producción
CREATE TRIGGER trg_actualizar_stock_produccion
AFTER INSERT ON detalle_produccion
FOR EACH ROW
EXECUTE FUNCTION actualizar_stock_produccion();

CREATE OR REPLACE FUNCTION verificar_stock_minimo()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.stock_actual < NEW.stock_minimo THEN
        RAISE NOTICE 'ALERTA: La materia prima % ha alcanzado el nivel mínimo de stock', NEW.nombre;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para verificar stock mínimo cada vez que se actualiza la materia prima
CREATE TRIGGER trg_verificar_stock_minimo
AFTER UPDATE ON materias_primas
FOR EACH ROW
EXECUTE FUNCTION verificar_stock_minimo();


CREATE OR REPLACE FUNCTION registrar_auditoria_produccion()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO auditoria (usuario_id, tabla_afectada, operacion, fecha)
    VALUES (NEW.usuario_id, 'ordenes_produccion', TG_OP, NOW());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para auditoría en inserción, actualización o eliminación
CREATE TRIGGER trg_auditoria_produccion
AFTER INSERT OR UPDATE OR DELETE ON ordenes_produccion
FOR EACH ROW
EXECUTE FUNCTION registrar_auditoria_produccion();


CREATE OR REPLACE FUNCTION calcular_costo_orden(orden_id INT)
RETURNS DECIMAL AS $$
DECLARE
    total_costo DECIMAL := 0;
BEGIN
    SELECT SUM(mp.precio * dp.cantidad_usada)
    INTO total_costo
    FROM detalle_produccion dp
    JOIN materias_primas mp ON dp.materia_prima_id = mp.id
    WHERE dp.orden_id = orden_id;

    RETURN total_costo;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION actualizar_estado_pedido()
RETURNS TRIGGER AS $$
DECLARE
    total_pendientes INT;
BEGIN
    -- Contar cuántos productos no han sido entregados en el pedido
    SELECT COUNT(*) INTO total_pendientes
    FROM detalle_pedidos dp
    WHERE dp.pedido_id = NEW.pedido_id AND dp.cantidad > 0;

    -- Si no hay productos pendientes, se actualiza el estado del pedido
    IF total_pendientes = 0 THEN
        UPDATE pedidos SET estado = 'Entregado' WHERE id = NEW.pedido_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para verificar y actualizar pedidos
CREATE TRIGGER trg_actualizar_estado_pedido
AFTER UPDATE ON detalle_pedidos
FOR EACH ROW
EXECUTE FUNCTION actualizar_estado_pedido();


CREATE OR REPLACE FUNCTION reporte_produccion_mensual(anio INT, mes INT)
RETURNS TABLE(
    producto VARCHAR,
    cantidad_producida DECIMAL,
    ingresos DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.nombre,
        SUM(op.cantidad) AS cantidad_producida,
        SUM(op.cantidad * p.precio) AS ingresos
    FROM ordenes_produccion op
    JOIN productos p ON op.producto_id = p.id
    WHERE EXTRACT(YEAR FROM op.fecha_inicio) = anio 
      AND EXTRACT(MONTH FROM op.fecha_inicio) = mes
    GROUP BY p.nombre;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION notificar_proveedor()
RETURNS TRIGGER AS $$
DECLARE
    proveedor_email VARCHAR;
BEGIN
    -- Obtener el email del proveedor asociado a la materia prima
    SELECT email INTO proveedor_email
    FROM proveedores
    WHERE id = NEW.id;

    -- Simulación de envío de correo
    PERFORM pg_notify('stock_alert', 'ALERTA: Stock bajo para ' || NEW.nombre || ' - Contactar a: ' || proveedor_email);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para enviar notificación cuando el stock es bajo
CREATE TRIGGER trg_notificar_proveedor
AFTER UPDATE ON materias_primas
FOR EACH ROW
WHEN (NEW.stock_actual < NEW.stock_minimo)
EXECUTE FUNCTION notificar_proveedor();


