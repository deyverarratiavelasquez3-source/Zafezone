# -*- coding: utf-8 -*-
"""
configuracion.py
----------------
Lee el archivo config.ini o las variables de entorno de la nube.
"""

import configparser
import os

CARPETA_PROYECTO = os.path.dirname(os.path.abspath(__file__))
RUTA_CONFIG = os.path.join(CARPETA_PROYECTO, "config.ini")


def leer_configuracion():
    """Abre config.ini si existe, de lo contrario devuelve None."""
    if not os.path.exists(RUTA_CONFIG):
        return None  # En la nube puede no existir el archivo físico

    config = configparser.ConfigParser(interpolation=None)
    config.read(RUTA_CONFIG, encoding="utf-8")
    return config


# Cargamos la configuración una sola vez al importar el archivo
config = leer_configuracion()


def datos_mysql(config_obj=config):
    """Devuelve los datos de conexión priorizando variables de entorno (Nube) 
    y respaldándose en config.ini (Local)."""
    
    # Si existen variables de entorno en la nube, las usamos:
    if os.environ.get("DB_HOST"):
        return {
            "host": os.environ.get("DB_HOST"),
            "port": int(os.environ.get("DB_PORT", 3306)),
            "user": os.environ.get("DB_USER"),
            "password": os.environ.get("DB_PASSWORD"),
            "database": os.environ.get("DB_NAME"),
            "charset": "utf8mb4",
        }
    
    # Si no, usamos tu config.ini local de toda la vida:
    if config_obj and "mysql" in config_obj:
        seccion = config_obj["mysql"]
        return {
            "host": seccion.get("host", "localhost"),
            "port": seccion.getint("puerto", 3306),
            "user": seccion.get("usuario", "root"),
            "password": seccion.get("password", ""),
            "database": seccion.get("base_de_datos", "zafezone_cas").strip(),
            "charset": "utf8mb4",
        }
        
    raise FileNotFoundError("No se encontró configuración ni en variables de entorno ni en config.ini")


def nombre_base_de_datos(config_obj=config):
    """Devuelve el nombre de la base de datos."""
    if os.environ.get("DB_NAME"):
        return os.environ.get("DB_NAME")
    
    if config_obj and "mysql" in config_obj:
        return config_obj["mysql"].get("base_de_datos", "zafezone_cas").strip()
        
    return "zafezone_cas"
