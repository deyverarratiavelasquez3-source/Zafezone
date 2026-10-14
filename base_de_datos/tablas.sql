-- ============================================================
--  TABLAS DE ZAFEZONE CAS
--  Este archivo lo lee crear_base_datos.py. Cada instruccion
--  termina con punto y coma. Si cambias algo aqui, no pongas
--  punto y coma dentro de los comentarios.
-- ============================================================

-- Personas que usan la plataforma (estudiantes y administradores)
CREATE TABLE IF NOT EXISTS usuarios (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    nombre        VARCHAR(50)  NOT NULL UNIQUE,
    curso         VARCHAR(50)  NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol           VARCHAR(20)  NOT NULL DEFAULT 'estudiante',
    creado_en     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Denuncias de bullying enviadas desde el formulario
CREATE TABLE IF NOT EXISTS denuncias (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id         INT          NULL,
    nombre_denunciante VARCHAR(100) NOT NULL,
    nombre_agresor     VARCHAR(100) NOT NULL,
    lugar              VARCHAR(30)  NOT NULL,
    fecha_hecho        DATE         NOT NULL,
    hora_hecho         TIME         NOT NULL,
    descripcion        TEXT         NOT NULL,
    estado             VARCHAR(20)  NOT NULL DEFAULT 'pendiente',
    creado_en          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Registros del diario emocional (cada estudiante ve solo los suyos)
CREATE TABLE IF NOT EXISTS diario_emocional (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT         NOT NULL,
    emocion    VARCHAR(20) NOT NULL,
    texto      TEXT        NULL,
    creado_en  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
