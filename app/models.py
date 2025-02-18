import hashlib
from flask_login import UserMixin
from sqlalchemy import func
from . import db

class Usuario(db.Model, UserMixin):
    __tablename__ = "usuarios" 

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(32), nullable=False)  
    rol_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=True)
    estado = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=db.func.current_timestamp())

 
    def set_password(self, password):
        self.password_hash = hashlib.md5(password.encode()).hexdigest()

    
    def check_password(self, password):
        return self.password_hash == hashlib.md5(password.encode()).hexdigest()


class Rol(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.Text)

class Permiso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    descripcion = db.Column(db.Text)


class UsuarioPermiso(db.Model):
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), primary_key=True)
    permiso_id = db.Column(db.Integer, db.ForeignKey("permiso.id"), primary_key=True)


class MateriaPrima(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    unidad_medida = db.Column(db.String(20))
    stock_actual = db.Column(db.Numeric(10,2))
    stock_minimo = db.Column(db.Numeric(10,2))
    precio = db.Column(db.Numeric(10,2))
    fecha_ingreso = db.Column(db.DateTime, default=db.func.current_timestamp())


class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    precio = db.Column(db.Numeric(10,2))
    stock = db.Column(db.Numeric(10,2))
    fecha_creacion = db.Column(db.DateTime, default=db.func.current_timestamp())


class Inventario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)  # Puede ser "Materia Prima" o "Producto"
    referencia_id = db.Column(db.Integer, nullable=False)  # ID del producto o materia prima
    cantidad = db.Column(db.Numeric(10,2))
    fecha_actualizacion = db.Column(db.DateTime, default=db.func.current_timestamp())


class Proveedor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    contacto = db.Column(db.String(50))
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(100))


class OrdenProduccion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey("producto.id"), nullable=False)
    cantidad = db.Column(db.Numeric(10,2))
    fecha_inicio = db.Column(db.DateTime)
    fecha_fin = db.Column(db.DateTime)
    estado = db.Column(db.String(50), nullable=False)  # "Pendiente", "En Proceso", "Finalizado"
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=True)


class DetalleProduccion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    orden_id = db.Column(db.Integer, db.ForeignKey("orden_produccion.id"), nullable=False)
    materia_prima_id = db.Column(db.Integer, db.ForeignKey("materia_prima.id"), nullable=True)
    cantidad_usada = db.Column(db.Numeric(10,2))


class Maquinaria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    modelo = db.Column(db.String(50))
    estado = db.Column(db.String(50), nullable=False)  # "Operativa", "En Mantenimiento", "Fuera de Servicio"


class Mantenimiento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    maquinaria_id = db.Column(db.Integer, db.ForeignKey("maquinaria.id"), nullable=False)
    fecha = db.Column(db.DateTime, default=db.func.current_timestamp())
    descripcion = db.Column(db.Text)
    costo = db.Column(db.Numeric(10,2))


class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(100))
    direccion = db.Column(db.Text)


class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("cliente.id"), nullable=True)
    fecha_pedido = db.Column(db.DateTime, default=db.func.current_timestamp())
    estado = db.Column(db.String(50), nullable=False)  # "Pendiente", "Enviado", "Entregado", "Cancelado"


class DetallePedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey("pedido.id"), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey("producto.id"), nullable=True)
    cantidad = db.Column(db.Numeric(10,2))
    precio = db.Column(db.Numeric(10,2))


class Reporte(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=True)
    tipo = db.Column(db.String(100))
    fecha_generacion = db.Column(db.DateTime, default=db.func.current_timestamp())


class Auditoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=True)
    tabla_afectada = db.Column(db.String(50))
    operacion = db.Column(db.String(50))
    fecha = db.Column(db.DateTime, default=db.func.current_timestamp())