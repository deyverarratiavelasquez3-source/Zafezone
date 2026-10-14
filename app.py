# -*- coding: utf-8 -*-
"""
app.py - Aplicación web ZafeZone CAS ("Tu colegio, tu zona segura")
===================================================================
Para encenderla:   python app.py

Páginas:
  /login                      Iniciar sesión
  /registro                   Crear cuenta de estudiante
  /principal                  Información, Denuncia y Diario emocional
  /mi-cuenta                  Datos del usuario y su historial
  /admin/denuncias            (solo administrador) Ver y gestionar denuncias
  /logout                     Cerrar sesión
"""

from functools import wraps

import mysql.connector
from flask import (
    Flask, render_template, request, redirect, url_for, session, flash
)
from werkzeug.security import generate_password_hash, check_password_hash

from configuracion import leer_configuracion, datos_mysql, nombre_base_de_datos

# ------------------------------------------------------------------
# 1. CONFIGURACIÓN INICIAL
# ------------------------------------------------------------------
CONFIG = leer_configuracion()

# Datos para conectarnos a MySQL (salen de config.ini)
DATOS_MYSQL = datos_mysql(CONFIG)
DATOS_MYSQL["database"] = nombre_base_de_datos(CONFIG)

app = Flask(__name__)

# La clave secreta protege las sesiones (las "cookies" del login)
app.secret_key = CONFIG["app"].get("clave_secreta", "")
if app.secret_key.startswith("cambia-esta-clave") or not app.secret_key:
    print("AVISO: cambia 'clave_secreta' en config.ini antes de publicar.")
    app.secret_key = app.secret_key or "clave-temporal-solo-para-pruebas"

# Opciones de seguridad de la cookie de sesión
app.config["SESSION_COOKIE_HTTPONLY"] = True   # JavaScript no puede leerla
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # evita envíos desde otras webs

# Opciones que se muestran en los formularios (y que validamos en el servidor)
LUGARES = ["Curso", "Patio", "Cafetería"]

# clave: (emoji, texto del botón, color del botón)
EMOCIONES = {
    "feliz":    ("😊", "Feliz",     "amarillo"),
    "normal":   ("😐", "Normal",    "verde"),
    "abrumado": ("😟", "Abrumado",  "rosa"),
    "triste":   ("😢", "Triste",    "morado"),
}

# clave guardada en la base de datos: texto para mostrar
ESTADOS = {
    "pendiente":   "Pendiente",
    "en revision": "En revisión",
    "resuelta":    "Resuelta",
}


# ------------------------------------------------------------------
# 2. FUNCIONES PARA HABLAR CON MYSQL
#    Cada función abre una conexión, hace su trabajo y la cierra.
#    Siempre usamos %s en el SQL y pasamos los valores aparte:
#    así nadie puede "inyectar" código malicioso en la base de datos.
# ------------------------------------------------------------------
def conectar():
    """Abre una conexión nueva a MySQL."""
    return mysql.connector.connect(**DATOS_MYSQL)


def consultar(sql, valores=(), uno=False):
    """
    Ejecuta un SELECT.
      uno=True  -> devuelve una sola fila (o None si no hay)
      uno=False -> devuelve una lista con todas las filas
    Cada fila es un diccionario: fila["nombre"], fila["curso"], etc.
    """
    conexion = conectar()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(sql, valores)
        return cursor.fetchone() if uno else cursor.fetchall()
    finally:
        conexion.close()


def ejecutar(sql, valores=()):
    """Ejecuta un INSERT, UPDATE o DELETE y guarda los cambios."""
    conexion = conectar()
    try:
        cursor = conexion.cursor()
        cursor.execute(sql, valores)
        conexion.commit()
    finally:
        conexion.close()


# ------------------------------------------------------------------
# 3. PROTECCIÓN DE PÁGINAS
#    Un "decorador" es una etiqueta (@algo) que se pone encima de una
#    ruta para que primero se haga una comprobación.
# ------------------------------------------------------------------
def login_requerido(funcion):
    """Solo deja entrar a quien ya inició sesión."""
    @wraps(funcion)
    def envoltura(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Primero debes iniciar sesión.", "error")
            return redirect(url_for("login"))
        return funcion(*args, **kwargs)
    return envoltura


def admin_requerido(funcion):
    """Solo deja entrar al administrador."""
    @wraps(funcion)
    def envoltura(*args, **kwargs):
        if session.get("rol") != "admin":
            flash("No tienes permiso para entrar a esa página.", "error")
            return redirect(url_for("principal"))
        return funcion(*args, **kwargs)
    return envoltura


# ------------------------------------------------------------------
# 4. FORMATOS PARA MOSTRAR FECHAS EN LAS PÁGINAS (filtros de plantilla)
#    Se usan en el HTML así:  {{ fila.creado_en|fechahora }}
# ------------------------------------------------------------------
@app.template_filter("fecha")
def filtro_fecha(valor):
    return valor.strftime("%d/%m/%Y") if valor else ""


@app.template_filter("fechahora")
def filtro_fechahora(valor):
    return valor.strftime("%d/%m/%Y %H:%M") if valor else ""


@app.template_filter("hora")
def filtro_hora(valor):
    # MySQL entrega las horas como "timedelta" (un tiempo transcurrido),
    # así que la convertimos a texto HH:MM
    if valor is None:
        return ""
    segundos = int(valor.total_seconds())
    return "%02d:%02d" % (segundos // 3600, (segundos % 3600) // 60)
# Ejemplo de cómo agregar la creación automática de tablas:
def inicializar_bd():
    try:
        # Usa la misma función/conexión que ya tienes configurada con env vars
        conexion = obtener_conexion() 
        cursor = conexion.cursor()
        
        # Ejecuta la creación de la tabla usuarios si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                correo VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL
            );
        """)
        
        # (Opcional) Agrega aquí las demás tablas que use tu app
        
        conexion.commit()
        cursor.close()
        conexion.close()
        print("¡Base de datos e infraestructura de tablas verificadas exitosamente!")
    except Exception as e:
        print(f"Error al inicializar tablas: {e}")

# Llama a la función al arrancar la app
inicializar_bd()

# ------------------------------------------------------------------
# 5. LOGIN, REGISTRO Y LOGOUT
# ------------------------------------------------------------------
@app.route("/")
def inicio():
    """La raíz del sitio manda al login o a la página principal."""
    if "usuario_id" in session:
        return redirect(url_for("principal"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    # Si ya inició sesión no hace falta mostrar el login otra vez
    if "usuario_id" in session:
        return redirect(url_for("principal"))

    nombre = ""
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        password = request.form.get("password", "")

        # Buscamos al usuario en la base de datos
        usuario = consultar(
            "SELECT id, nombre, password_hash, rol FROM usuarios WHERE nombre = %s",
            (nombre,), uno=True,
        )

        # Comparamos la contraseña escrita con el hash guardado
        if usuario and check_password_hash(usuario["password_hash"], password):
            session.clear()  # borramos cualquier sesión anterior
            session["usuario_id"] = usuario["id"]
            session["nombre"] = usuario["nombre"]
            session["rol"] = usuario["rol"]
            return redirect(url_for("principal"))

        # Mismo mensaje si falla el nombre o la contraseña (más seguro)
        flash("Nombre o contraseña incorrectos.", "error")

    return render_template("login.html", nombre=nombre)


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if "usuario_id" in session:
        return redirect(url_for("principal"))

    datos = {}
    if request.method == "POST":
        datos = request.form
        nombre = request.form.get("nombre", "").strip()
        curso = request.form.get("curso", "").strip()
        password = request.form.get("password", "")
        password2 = request.form.get("password2", "")

        # Validaciones: si algo está mal, avisamos y volvemos a mostrar el formulario
        if len(nombre) < 3 or len(nombre) > 50:
            flash("El nombre debe tener entre 3 y 50 caracteres.", "error")
        elif len(curso) > 50:
            flash("El curso es demasiado largo.", "error")
        elif len(password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "error")
        elif password != password2:
            flash("Las contraseñas no coinciden.", "error")
        else:
            try:
                ejecutar(
                    "INSERT INTO usuarios (nombre, curso, password_hash, rol) "
                    "VALUES (%s, %s, %s, 'estudiante')",
                    (nombre, curso or None, generate_password_hash(password)),
                )
                flash("¡Cuenta creada! Ya puedes iniciar sesión.", "exito")
                return redirect(url_for("login"))
            except mysql.connector.IntegrityError:
                # La columna "nombre" es UNIQUE: MySQL rechaza los repetidos
                flash("Ese nombre ya está en uso, elige otro.", "error")

    return render_template("registro.html", datos=datos)


@app.route("/logout")
def logout():
    session.clear()
    flash("Cerraste sesión correctamente.", "exito")
    return redirect(url_for("login"))


# ------------------------------------------------------------------
# 6. PÁGINA PRINCIPAL (Información + Denuncia + Diario emocional)
# ------------------------------------------------------------------
def mostrar_principal(datos_denuncia=None, datos_diario=None):
    """
    Dibuja la página principal. Si un formulario tuvo errores, recibe lo que
    la persona ya había escrito para no hacerla escribir todo de nuevo.
    """
    return render_template(
        "principal.html",
        d=datos_denuncia or {},
        e=datos_diario or {},
        lugares=LUGARES,
        emociones=EMOCIONES,
    )


@app.route("/principal")
@login_requerido
def principal():
    return mostrar_principal()


@app.route("/denuncia", methods=["POST"])
@login_requerido
def enviar_denuncia():
    """Recibe el formulario de denuncia y lo guarda en MySQL."""
    denunciante = request.form.get("nombre_denunciante", "").strip()
    agresor = request.form.get("nombre_agresor", "").strip()
    lugar = request.form.get("lugar", "")
    fecha = request.form.get("fecha", "")
    hora = request.form.get("hora", "")
    descripcion = request.form.get("descripcion", "").strip()

    # --- Validaciones ---
    error = None
    if not denunciante or not agresor:
        error = "Escribe el nombre del denunciante y el del agresor."
    elif len(denunciante) > 100 or len(agresor) > 100:
        error = "Los nombres no pueden pasar de 100 caracteres."
    elif lugar not in LUGARES:
        error = "Elige el lugar donde ocurrió."
    elif not fecha or not hora:
        error = "Indica la fecha y la hora aproximada."
    elif len(descripcion) < 10:
        error = "Cuéntanos con un poco más de detalle lo que pasó."
    elif len(descripcion) > 5000:
        error = "La descripción es demasiado larga (máximo 5000 caracteres)."

    if error:
        flash(error, "error")
        return mostrar_principal(datos_denuncia=request.form)

    # --- Guardar ---
    ejecutar(
        "INSERT INTO denuncias (usuario_id, nombre_denunciante, nombre_agresor, "
        "lugar, fecha_hecho, hora_hecho, descripcion) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (session["usuario_id"], denunciante, agresor, lugar, fecha, hora, descripcion),
    )
    flash("Tu denuncia fue enviada. Gracias por ser valiente 💙", "exito")
    return redirect(url_for("principal"))


@app.route("/diario", methods=["POST"])
@login_requerido
def guardar_diario():
    """Recibe el registro del diario emocional y lo guarda en MySQL."""
    emocion = request.form.get("emocion", "")
    texto = request.form.get("texto", "").strip()

    if emocion not in EMOCIONES:
        flash("Elige cómo te sientes hoy.", "error")
        return mostrar_principal(datos_diario=request.form)
    if len(texto) > 5000:
        flash("El texto es demasiado largo (máximo 5000 caracteres).", "error")
        return mostrar_principal(datos_diario=request.form)

    ejecutar(
        "INSERT INTO diario_emocional (usuario_id, emocion, texto) VALUES (%s, %s, %s)",
        (session["usuario_id"], emocion, texto or None),
    )
    flash("Tu registro fue guardado ♡", "exito")

    # Mensaje de apoyo si la emoción fue difícil
    if emocion in ("triste", "abrumado"):
        flash("Gracias por contarlo. Si lo necesitas, habla con un adulto de "
              "confianza o con el orientador del colegio. No estás solo/a.", "info")

    return redirect(url_for("principal"))


# ------------------------------------------------------------------
# 7. MI CUENTA
# ------------------------------------------------------------------
@app.route("/mi-cuenta")
@login_requerido
def mi_cuenta():
    usuario = consultar(
        "SELECT nombre, curso, rol, creado_en FROM usuarios WHERE id = %s",
        (session["usuario_id"],), uno=True,
    )

    # Últimos 30 registros del diario (solo los de esta persona)
    diario = consultar(
        "SELECT emocion, texto, creado_en FROM diario_emocional "
        "WHERE usuario_id = %s ORDER BY creado_en DESC LIMIT 30",
        (session["usuario_id"],),
    )

    # Denuncias enviadas por esta persona (solo su estado, sin el detalle)
    denuncias = consultar(
        "SELECT lugar, fecha_hecho, estado, creado_en FROM denuncias "
        "WHERE usuario_id = %s ORDER BY creado_en DESC",
        (session["usuario_id"],),
    )

    return render_template(
        "mi_cuenta.html",
        usuario=usuario, diario=diario, denuncias=denuncias,
        emociones=EMOCIONES, estados=ESTADOS,
    )


# ------------------------------------------------------------------
# 8. PANEL DEL ADMINISTRADOR
# ------------------------------------------------------------------
@app.route("/admin/denuncias")
@login_requerido
@admin_requerido
def admin_denuncias():
    # LEFT JOIN: trae también el nombre de la cuenta que envió la denuncia
    denuncias = consultar(
        "SELECT d.id, d.nombre_denunciante, d.nombre_agresor, d.lugar, "
        "d.fecha_hecho, d.hora_hecho, d.descripcion, d.estado, d.creado_en, "
        "u.nombre AS cuenta "
        "FROM denuncias d LEFT JOIN usuarios u ON u.id = d.usuario_id "
        "ORDER BY d.creado_en DESC"
    )
    return render_template("admin_denuncias.html", denuncias=denuncias, estados=ESTADOS)


@app.route("/admin/denuncias/<int:denuncia_id>/estado", methods=["POST"])
@login_requerido
@admin_requerido
def cambiar_estado(denuncia_id):
    nuevo_estado = request.form.get("estado", "")
    if nuevo_estado in ESTADOS:
        ejecutar("UPDATE denuncias SET estado = %s WHERE id = %s",
                 (nuevo_estado, denuncia_id))
        flash("Estado actualizado.", "exito")
    else:
        flash("Estado no válido.", "error")
    return redirect(url_for("admin_denuncias"))


# ------------------------------------------------------------------
# 9. SI MYSQL FALLA (apagado, contraseña mal, tablas sin crear...)
# ------------------------------------------------------------------
@app.errorhandler(mysql.connector.Error)
def error_de_mysql(error):
    print("ERROR DE MYSQL:", error)  # el detalle se ve en la consola
    return render_template("error.html"), 500


# ------------------------------------------------------------------
# 10. ENCENDER LA APLICACIÓN
# ------------------------------------------------------------------
if __name__ == "__main__":
    puerto_web = CONFIG["app"].getint("puerto_web", 5000)
    modo_debug = CONFIG["app"].getboolean("debug", False)
    app.run(host="0.0.0.0", port=puerto_web, debug=modo_debug)
