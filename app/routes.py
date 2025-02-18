from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import Usuario
from sqlalchemy.sql import text
from flask import Response
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


routes = Blueprint("routes", __name__)


@routes.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("routes.dashboard"))
    return redirect(url_for("routes.login"))

@routes.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("routes.dashboard"))

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and usuario.check_password(password):
            login_user(usuario)
            return redirect(url_for("routes.dashboard"))
        else:
            flash("Credenciales incorrectas", "danger")

    return render_template("login.html")

@routes.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("routes.login"))


@routes.route("/dashboard")
@login_required
def dashboard():
    if current_user.rol_id == 1:  # Administrador
        stock_bajo = db.session.execute(text("""
            SELECT id, nombre, stock_actual, stock_minimo FROM materias_primas 
            WHERE stock_actual < stock_minimo;
        """)).fetchall()

        productos = db.session.execute(text("SELECT id, nombre, stock FROM productos WHERE stock > 0")).fetchall()

        ordenes_produccion = db.session.execute(text("""
            SELECT op.id, p.nombre, op.cantidad, op.fecha_inicio, op.estado 
            FROM ordenes_produccion op
            JOIN productos p ON op.producto_id = p.id
            ORDER BY op.fecha_inicio DESC
            LIMIT 5;
        """)).fetchall()

        pedidos = db.session.execute(text("""
            SELECT id, cliente_id, fecha_pedido, estado 
            FROM pedidos ORDER BY fecha_pedido DESC LIMIT 5;
        """)).fetchall()

        ingresos_totales = db.session.execute(text("""
            SELECT SUM(op.cantidad * p.precio) AS total_ingresos 
            FROM ordenes_produccion op
            JOIN productos p ON op.producto_id = p.id;
        """)).scalar()

        auditoria = db.session.execute(text("""
            SELECT usuario_id, tabla_afectada, operacion, fecha 
            FROM auditoria WHERE tabla_afectada = 'ordenes_produccion' 
            ORDER BY fecha DESC LIMIT 5;
        """)).fetchall()

        inventario = db.session.execute(text("""
            SELECT i.id, i.tipo, 
                   COALESCE(mp.nombre, p.nombre) AS nombre, 
                   i.cantidad, i.fecha_actualizacion 
            FROM inventario i
            LEFT JOIN materias_primas mp ON i.tipo = 'Materia Prima' AND i.referencia_id = mp.id
            LEFT JOIN productos p ON i.tipo = 'Producto' AND i.referencia_id = p.id
            ORDER BY i.fecha_actualizacion DESC;
        """)).fetchall()

        proveedores = db.session.execute(text("""
            SELECT id, nombre, contacto, telefono, email FROM proveedores;
        """)).fetchall()

        return render_template("dashboard_admin.html", 
                               stock_bajo=stock_bajo, productos=productos, 
                               ordenes_produccion=ordenes_produccion, pedidos=pedidos, 
                               ingresos_totales=ingresos_totales, auditoria=auditoria,
                               inventario=inventario, proveedores=proveedores)

    elif current_user.rol_id == 2:  # Gerente
        stock_bajo = db.session.execute(text("""
            SELECT id, nombre, stock_actual, stock_minimo FROM materias_primas 
            WHERE stock_actual < stock_minimo;
        """)).fetchall()

        ordenes_produccion = db.session.execute(text("""
            SELECT op.id, p.nombre, op.cantidad, op.fecha_inicio, op.estado 
            FROM ordenes_produccion op
            JOIN productos p ON op.producto_id = p.id
            ORDER BY op.fecha_inicio DESC
            LIMIT 5;
        """)).fetchall()

        pedidos = db.session.execute(text("""
            SELECT id, cliente_id, fecha_pedido, estado 
            FROM pedidos ORDER BY fecha_pedido DESC LIMIT 5;
        """)).fetchall()

        auditoria = db.session.execute(text("""
            SELECT usuario_id, tabla_afectada, operacion, fecha 
            FROM auditoria WHERE tabla_afectada = 'ordenes_produccion' 
            ORDER BY fecha DESC LIMIT 5;
        """)).fetchall()

        inventario = db.session.execute(text("""
            SELECT i.id, i.tipo, 
                   COALESCE(mp.nombre, p.nombre) AS nombre, 
                   i.cantidad, i.fecha_actualizacion 
            FROM inventario i
            LEFT JOIN materias_primas mp ON i.tipo = 'Materia Prima' AND i.referencia_id = mp.id
            LEFT JOIN productos p ON i.tipo = 'Producto' AND i.referencia_id = p.id
            ORDER BY i.fecha_actualizacion DESC;
        """)).fetchall()

        proveedores = db.session.execute(text("""
            SELECT id, nombre, contacto, telefono, email FROM proveedores;
        """)).fetchall()

        return render_template("dashboard_gerente.html", 
                               stock_bajo=stock_bajo, 
                               ordenes_produccion=ordenes_produccion, 
                               pedidos=pedidos, 
                               auditoria=auditoria,
                               inventario=inventario, 
                               proveedores=proveedores)

    elif current_user.rol_id == 3:  # Operario
        return render_template("dashboard_operario.html", usuario=current_user)

    elif current_user.rol_id == 4:  # Cliente
        cliente = db.session.execute(text("""
            SELECT id FROM clientes WHERE usuario_id = :usuario_id
        """), {"usuario_id": current_user.id}).fetchone()

        if cliente:
            pedidos_cliente = db.session.execute(text("""
                SELECT p.id, p.fecha_pedido, p.estado 
                FROM pedidos p
                WHERE p.cliente_id = :cliente_id
                ORDER BY p.fecha_pedido DESC;
            """), {"cliente_id": cliente.id}).fetchall()
        else:
            pedidos_cliente = []

        return render_template("dashboard_cliente.html", usuario=current_user, pedidos=pedidos_cliente)

    return render_template("dashboard.html", usuario=current_user)



@routes.route("/productos", methods=["GET", "POST"])
@login_required
def productos():
    if request.method == "POST":
        nombre = request.form["nombre"]
        descripcion = request.form["descripcion"]
        precio = request.form["precio"]
        stock = request.form["stock"]

        try:
            db.session.execute(text("""
                INSERT INTO productos (nombre, descripcion, precio, stock, fecha_creacion)
                VALUES (:nombre, :descripcion, :precio, :stock, NOW())
            """), {"nombre": nombre, "descripcion": descripcion, "precio": precio, "stock": stock})
            db.session.commit()
            flash("Producto agregado con éxito.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error al agregar el producto: {str(e)}", "danger")

        return redirect(url_for("routes.productos"))

    productos = db.session.execute(text("SELECT id, nombre, descripcion, precio, stock, fecha_creacion FROM productos")).fetchall()
    return render_template("productos.html", productos=productos)

@routes.route("/eliminar_producto/<int:id>")
@login_required
def eliminar_producto(id):
    try:
        db.session.execute(text("DELETE FROM productos WHERE id = :id"), {"id": id})
        db.session.commit()
        flash("Producto eliminado con éxito.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar el producto: {str(e)}", "danger")

    return redirect(url_for("routes.productos"))


@routes.route("/materias_primas", methods=["GET", "POST"])
@login_required
def materias_primas():
    if request.method == "POST":
        nombre = request.form["nombre"]
        descripcion = request.form["descripcion"]
        unidad_medida = request.form["unidad_medida"]
        stock_actual = request.form["stock_actual"]
        stock_minimo = request.form["stock_minimo"]
        precio = request.form["precio"]

        try:
            db.session.execute(text("""
                INSERT INTO materias_primas (nombre, descripcion, unidad_medida, stock_actual, stock_minimo, precio, fecha_ingreso)
                VALUES (:nombre, :descripcion, :unidad_medida, :stock_actual, :stock_minimo, :precio, NOW())
            """), {"nombre": nombre, "descripcion": descripcion, "unidad_medida": unidad_medida,
                   "stock_actual": stock_actual, "stock_minimo": stock_minimo, "precio": precio})
            db.session.commit()
            flash("Materia prima agregada con éxito.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error al agregar la materia prima: {str(e)}", "danger")

        return redirect(url_for("routes.materias_primas"))

    materias = db.session.execute(text("SELECT id, nombre, descripcion, unidad_medida, stock_actual, stock_minimo, precio FROM materias_primas")).fetchall()
    return render_template("materias_primas.html", materias=materias)

@routes.route("/eliminar_materia_prima/<int:id>")
@login_required
def eliminar_materia_prima(id):
    try:
        db.session.execute(text("DELETE FROM materias_primas WHERE id = :id"), {"id": id})
        db.session.commit()
        flash("Materia prima eliminada con éxito.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar la materia prima: {str(e)}", "danger")

    return redirect(url_for("routes.materias_primas"))

@routes.route("/actualizar_stock_materia_prima/<int:id>", methods=["POST"])
@login_required
def actualizar_stock_materia_prima(id):
    nuevo_stock = request.form["nuevo_stock"]

    try:
        db.session.execute(text("""
            UPDATE materias_primas 
            SET stock_actual = :nuevo_stock 
            WHERE id = :id
        """), {"nuevo_stock": nuevo_stock, "id": id})
        db.session.commit()
        flash("Stock actualizado con éxito.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al actualizar el stock: {str(e)}", "danger")

    return redirect(url_for("routes.materias_primas"))



@routes.route("/clientes", methods=["GET", "POST"])
@login_required
def clientes():
    if request.method == "POST":
        nombre = request.form["nombre"]
        telefono = request.form["telefono"]
        email = request.form["email"]
        direccion = request.form["direccion"]
        usuario_id = request.form["usuario_id"] 

        try:
            db.session.execute(text("""
                INSERT INTO clientes (nombre, telefono, email, direccion, usuario_id) 
                VALUES (:nombre, :telefono, :email, :direccion, :usuario_id)
            """), {
                "nombre": nombre,
                "telefono": telefono,
                "email": email,
                "direccion": direccion,
                "usuario_id": usuario_id
            })
            db.session.commit()
            flash("Cliente agregado con éxito.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error al agregar el cliente: {str(e)}", "danger")

        return redirect(url_for("routes.clientes"))

   
    clientes = db.session.execute(text("""
        SELECT c.id, c.nombre, c.telefono, c.email, c.direccion, u.nombre AS usuario 
        FROM clientes c
        LEFT JOIN usuarios u ON c.usuario_id = u.id
    """)).fetchall()

    
    usuarios = db.session.execute(text("""
        SELECT id, nombre FROM usuarios WHERE id NOT IN (SELECT usuario_id FROM clientes WHERE usuario_id IS NOT NULL)
    """)).fetchall()

    return render_template("clientes.html", clientes=clientes, usuarios=usuarios)


@routes.route("/eliminar_cliente/<int:id>")
@login_required
def eliminar_cliente(id):
    try:
        db.session.execute(text("DELETE FROM clientes WHERE id = :id"), {"id": id})
        db.session.commit()
        flash("Cliente eliminado con éxito.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar el cliente: {str(e)}", "danger")

    return redirect(url_for("routes.clientes"))




@routes.route("/pedidos", methods=["GET", "POST"])
@login_required
def pedidos():
    from app.models import Pedido, Cliente  

    if request.method == "POST":
        cliente_id = request.form["cliente_id"]

        try:
            db.session.execute(text("""
                INSERT INTO pedidos (cliente_id, fecha_pedido, estado)
                VALUES (:cliente_id, NOW(), 'Pendiente')
            """), {"cliente_id": cliente_id})
            db.session.commit()
            flash("Pedido agregado con éxito.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error al agregar el pedido: {str(e)}", "danger")

        return redirect(url_for("routes.pedidos"))

    pedidos = db.session.execute(text("""
        SELECT p.id, c.nombre AS cliente, p.fecha_pedido, p.estado
        FROM pedidos p
        JOIN clientes c ON p.cliente_id = c.id
        ORDER BY p.fecha_pedido DESC;
    """)).fetchall()

    clientes = db.session.execute(text("SELECT id, nombre FROM clientes")).fetchall()

    return render_template("pedidos.html", pedidos=pedidos, clientes=clientes)

@routes.route("/eliminar_pedido/<int:id>")
@login_required
def eliminar_pedido(id):
    try:
        db.session.execute(text("DELETE FROM pedidos WHERE id = :id"), {"id": id})
        db.session.commit()
        flash("Pedido eliminado con éxito.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar el pedido: {str(e)}", "danger")

    return redirect(url_for("routes.pedidos"))



@routes.route("/ordenes_produccion", methods=["GET", "POST"])
@login_required
def ordenes_produccion():
    if request.method == "POST":
        producto_id = request.form["producto_id"]
        cantidad = request.form["cantidad"]
        usuario_id = current_user.id  

        try:
            db.session.execute(text("""
                INSERT INTO ordenes_produccion (producto_id, cantidad, fecha_inicio, estado, usuario_id)
                VALUES (:producto_id, :cantidad, NOW(), 'Pendiente', :usuario_id)
            """), {
                "producto_id": producto_id,
                "cantidad": cantidad,
                "usuario_id": usuario_id
            })
            db.session.commit()
            flash("Orden de producción creada con éxito.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error al crear la orden de producción: {str(e)}", "danger")

        return redirect(url_for("routes.ordenes_produccion"))

    ordenes = db.session.execute(text("""
        SELECT op.id, p.nombre AS producto, op.cantidad, op.fecha_inicio, op.estado, u.nombre AS usuario
        FROM ordenes_produccion op
        JOIN productos p ON op.producto_id = p.id
        LEFT JOIN usuarios u ON op.usuario_id = u.id
        ORDER BY op.fecha_inicio DESC;
    """)).fetchall()

    productos = db.session.execute(text("SELECT id, nombre FROM productos")).fetchall()

    return render_template("ordenes_produccion.html", ordenes=ordenes, productos=productos)


@routes.route("/actualizar_estado_orden/<int:id>", methods=["POST"])
@login_required
def actualizar_estado_orden(id):
    nuevo_estado = request.form["nuevo_estado"]

    try:
        
        db.session.execute(text("""
            UPDATE ordenes_produccion 
            SET estado = :nuevo_estado, usuario_id = :usuario_id 
            WHERE id = :id
        """), {"nuevo_estado": nuevo_estado, "usuario_id": current_user.id, "id": id})

        
        if nuevo_estado == "Finalizado":
            db.session.execute(text("""
                UPDATE materias_primas
                SET stock_actual = stock_actual - dp.cantidad_usada
                FROM detalle_produccion dp
                WHERE materias_primas.id = dp.materia_prima_id AND dp.orden_id = :id
            """), {"id": id})

        db.session.commit()
        flash("Estado de la orden actualizado con éxito.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al actualizar el estado de la orden: {str(e)}", "danger")

    return redirect(url_for("routes.ordenes_produccion"))


@routes.route("/cambiar_contraseña", methods=["GET", "POST"])
@login_required
def cambiar_contraseña():
    if request.method == "POST":
        old_password = request.form["old_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if not current_user.check_password(old_password):
            flash("La contraseña actual es incorrecta.", "danger")
        elif new_password != confirm_password:
            flash("Las contraseñas no coinciden.", "danger")
        else:
            current_user.set_password(new_password)  
            db.session.commit()
            flash("Contraseña actualizada exitosamente.", "success")
            return redirect(url_for("routes.dashboard"))

    return render_template("cambiar_contraseña.html")


@routes.route("/maquinaria")
@login_required
def maquinaria():
    maquinaria = db.session.execute(text("""
        SELECT m.id, m.nombre, m.modelo, m.estado 
        FROM maquinaria m;
    """)).fetchall()

    mantenimientos = db.session.execute(text("""
        SELECT mt.id, mt.maquinaria_id, m.nombre AS maquinaria, mt.fecha, mt.descripcion, mt.costo
        FROM mantenimiento mt
        JOIN maquinaria m ON mt.maquinaria_id = m.id
        ORDER BY mt.fecha DESC;
    """)).fetchall()

    return render_template("maquinaria.html", maquinaria=maquinaria, mantenimientos=mantenimientos)



@routes.route("/auditoria")
@login_required
def auditoria():
    auditoria = db.session.execute(text("""
        SELECT a.usuario_id, u.nombre AS usuario, a.tabla_afectada, a.operacion, a.fecha
        FROM auditoria a
        JOIN usuarios u ON a.usuario_id = u.id
        ORDER BY a.fecha DESC;
    """)).fetchall()

    reportes = db.session.execute(text("""
        SELECT r.id, r.tipo, r.fecha_generacion, u.nombre AS generado_por
        FROM reportes r
        JOIN usuarios u ON r.usuario_id = u.id
        ORDER BY r.fecha_generacion DESC;
    """)).fetchall()

    return render_template("auditoria.html", auditoria=auditoria, reportes=reportes)

# --------------------------------------------------------------------------------------------------------------------------------------


# Función para generar un PDF
def generar_pdf(titulo, datos, columnas):
    """ Genera un PDF con los datos pasados en la lista. """
    from io import BytesIO
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle(titulo)

    # Título del Reporte
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, 750, titulo)
    pdf.setFont("Helvetica", 12)

    # Dibujar las columnas
    y = 700
    for columna in columnas:
        pdf.drawString(50 + columnas.index(columna) * 150, y, columna)
    y -= 20

    # Dibujar los datos en la tabla
    for fila in datos:
        for i, valor in enumerate(fila):
            pdf.drawString(50 + i * 150, y, str(valor))
        y -= 20

    pdf.save()
    buffer.seek(0)
    return buffer

# Ruta para descargar el reporte de Inventario
@routes.route("/reporte_inventario")
@login_required
def reporte_inventario():
    inventario = db.session.execute(text("""
        SELECT i.tipo, COALESCE(mp.nombre, p.nombre) AS nombre, i.cantidad, i.fecha_actualizacion
        FROM inventario i
        LEFT JOIN materias_primas mp ON i.tipo = 'Materia Prima' AND i.referencia_id = mp.id
        LEFT JOIN productos p ON i.tipo = 'Producto' AND i.referencia_id = p.id
    """)).fetchall()

    datos = [(item.tipo, item.nombre, item.cantidad, item.fecha_actualizacion) for item in inventario]
    columnas = ["Tipo", "Nombre", "Cantidad", "Última Actualización"]

    pdf_buffer = generar_pdf("Reporte de Inventario", datos, columnas)
    
    return Response(pdf_buffer, mimetype="application/pdf",
                    headers={"Content-Disposition": "attachment;filename=reporte_inventario.pdf"})

# Ruta para descargar el reporte de Órdenes de Producción
@routes.route("/reporte_produccion")
@login_required
def reporte_produccion():
    ordenes = db.session.execute(text("""
        SELECT op.id, p.nombre, op.cantidad, op.fecha_inicio, op.estado
        FROM ordenes_produccion op
        JOIN productos p ON op.producto_id = p.id
    """)).fetchall()

    datos = [(orden.id, orden.nombre, orden.cantidad, orden.fecha_inicio, orden.estado) for orden in ordenes]
    columnas = ["ID", "Producto", "Cantidad", "Fecha Inicio", "Estado"]

    pdf_buffer = generar_pdf("Reporte de Producción", datos, columnas)
    
    return Response(pdf_buffer, mimetype="application/pdf",
                    headers={"Content-Disposition": "attachment;filename=reporte_produccion.pdf"})

# Ruta para descargar el reporte de Pedidos
@routes.route("/reporte_pedidos")
@login_required
def reporte_pedidos():
    pedidos = db.session.execute(text("""
        SELECT p.id, c.nombre, p.fecha_pedido, p.estado
        FROM pedidos p
        JOIN clientes c ON p.cliente_id = c.id
    """)).fetchall()

    datos = [(pedido.id, pedido.nombre, pedido.fecha_pedido, pedido.estado) for pedido in pedidos]
    columnas = ["ID", "Cliente", "Fecha Pedido", "Estado"]

    pdf_buffer = generar_pdf("Reporte de Pedidos", datos, columnas)
    
    return Response(pdf_buffer, mimetype="application/pdf",
                    headers={"Content-Disposition": "attachment;filename=reporte_pedidos.pdf"})


# Ruta para un Reporte General del Sistema
@routes.route("/reporte_general")
@login_required
def reporte_general():
    total_productos = db.session.execute(text("SELECT COUNT(*) FROM productos")).scalar()
    total_materias_primas = db.session.execute(text("SELECT COUNT(*) FROM materias_primas")).scalar()
    total_pedidos = db.session.execute(text("SELECT COUNT(*) FROM pedidos")).scalar()
    total_ordenes = db.session.execute(text("SELECT COUNT(*) FROM ordenes_produccion")).scalar()
    total_ingresos = db.session.execute(text("""
        SELECT SUM(op.cantidad * p.precio) AS total_ingresos 
        FROM ordenes_produccion op
        JOIN productos p ON op.producto_id = p.id;
    """)).scalar()

    datos = [
        ("Total Productos", total_productos),
        ("Total Materias Primas", total_materias_primas),
        ("Total Pedidos", total_pedidos),
        ("Total Órdenes de Producción", total_ordenes),
        ("Total Ingresos ($)", total_ingresos)
    ]
    columnas = ["Descripción", "Cantidad"]

    pdf_buffer = generar_pdf("Reporte General del Sistema", datos, columnas)
    
    return Response(pdf_buffer, mimetype="application/pdf",
                    headers={"Content-Disposition": "attachment;filename=reporte_general.pdf"})