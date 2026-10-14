import os
import mysql.connector

conexion = mysql.connector.connect(
    host=os.environ.get("DB_HOST"),
    port=int(os.environ.get("DB_PORT", 24661)),
    user=os.environ.get("DB_USER"),
    password=os.environ.get("DB_PASSWORD"),
    database=os.environ.get("DB_NAME", "defaultdb"),
)

cursor = conexion.cursor()
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nombre VARCHAR(100) NOT NULL,
        correo VARCHAR(100) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL
    );
"""
)
conexion.commit()
cursor.close()
conexion.close()
