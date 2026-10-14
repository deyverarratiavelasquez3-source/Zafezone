# -*- coding: utf-8 -*-
"""
crear_base_datos.py
-------------------
Se ejecuta UNA sola vez (la clienta lo ejecuta después de editar config.ini):

    python crear_base_datos.py

Qué hace:
  1. Se conecta a MySQL con los datos de config.ini
  2. Crea la base de datos (si no existe)
  3. Crea las tablas leyendo base_de_datos/tablas.sql
  4. Crea la cuenta del administrador (si no existe)

Se puede ejecutar varias veces sin problema: no borra nada.
"""

import os
import re
import sys

import mysql.connector
from werkzeug.security import generate_password_hash

from configuracion import (
    CARPETA_PROYECTO,
    leer_configuracion,
    datos_mysql,
    nombre_base_de_datos,
)

RUTA_TABLAS = os.path.join(CARPETA_PROYECTO, "base_de_datos", "tablas.sql")


def leer_instrucciones_sql():
    """Lee tablas.sql y devuelve una lista con cada instrucción SQL."""
    with open(RUTA_TABLAS, encoding="utf-8") as archivo:
        lineas = archivo.readlines()

    # Quitamos los comentarios (las líneas que empiezan con --)
    sin_comentarios = [l for l in lineas if not l.strip().startswith("--")]

    # Separamos por punto y coma: cada pedazo es una instrucción
    texto = "".join(sin_comentarios)
    instrucciones = [pedazo.strip() for pedazo in texto.split(";")]
    return [i for i in instrucciones if i]  # descartamos los vacíos


def main():
    print("=== Instalador de la base de datos de ZafeZone CAS ===\n")

    # --- 1. Leer la configuración -------------------------------------
    try:
        config = leer_configuracion()
        conexion_datos = datos_mysql(config)
        nombre_bd = nombre_base_de_datos(config)
    except Exception as error:
        print("ERROR leyendo config.ini:", error)
        sys.exit(1)

    # El nombre de la base de datos se escribe dentro de una instrucción SQL,
    # por eso solo permitimos letras, números y guion bajo (evita errores).
    if not re.fullmatch(r"[A-Za-z0-9_]+", nombre_bd):
        print("ERROR: el nombre de la base de datos solo puede tener")
        print("letras, números y guion bajo (_). Corrígelo en config.ini")
        sys.exit(1)

    # --- 2. Conectarse a MySQL ----------------------------------------
    print("Conectando a MySQL en %s:%s con el usuario '%s'..." % (
        conexion_datos["host"], conexion_datos["port"], conexion_datos["user"]))
    try:
        conexion = mysql.connector.connect(**conexion_datos)
    except mysql.connector.Error as error:
        print("\nNO se pudo conectar a MySQL.")
        print("Detalle:", error)
        print("\nRevisa en config.ini: host, puerto, usuario y password,")
        print("y comprueba que MySQL esté encendido.")
        sys.exit(1)

    cursor = conexion.cursor()

    try:
        # --- 3. Crear la base de datos --------------------------------
        cursor.execute(
            "CREATE DATABASE IF NOT EXISTS `%s` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci" % nombre_bd
        )
        cursor.execute("USE `%s`" % nombre_bd)
        print("Base de datos '%s' lista." % nombre_bd)

        # --- 4. Crear las tablas --------------------------------------
        for instruccion in leer_instrucciones_sql():
            cursor.execute(instruccion)
        print("Tablas creadas: usuarios, denuncias, diario_emocional.")

        # --- 5. Crear el administrador --------------------------------
        nombre_admin = config["admin"].get("nombre", "admin").strip()
        password_admin = config["admin"].get("password", "")

        if len(password_admin) < 6:
            print("\nERROR: la contraseña del admin en config.ini debe tener")
            print("al menos 6 caracteres.")
            sys.exit(1)

        cursor.execute("SELECT id FROM usuarios WHERE nombre = %s", (nombre_admin,))
        if cursor.fetchone():
            print("El administrador '%s' ya existía (no se modificó)." % nombre_admin)
        else:
            # Nunca se guarda la contraseña tal cual: se guarda su "hash"
            cursor.execute(
                "INSERT INTO usuarios (nombre, password_hash, rol) "
                "VALUES (%s, %s, 'admin')",
                (nombre_admin, generate_password_hash(password_admin)),
            )
            print("Administrador '%s' creado." % nombre_admin)

        conexion.commit()

    except mysql.connector.Error as error:
        print("\nOcurrió un error en MySQL:", error)
        print("Si dice 'Access denied', el usuario no tiene permiso para crear")
        print("bases de datos. Prueba con el usuario root en config.ini.")
        sys.exit(1)
    finally:
        cursor.close()
        conexion.close()

    print("\n¡Listo! Ahora ejecuta:  python app.py")


if __name__ == "__main__":
    main()
