# ZafeZone CAS – "Tu colegio, tu zona segura"

Plataforma web contra el bullying hecha con **Flask (Python)** y **MySQL**.
Incluye: inicio de sesión, registro, información sobre bullying, formulario de
**denuncia**, **diario emocional**, página "Mi cuenta" y un panel para que el
administrador revise las denuncias.

---

## 1. Qué necesitas instalar

1. **Python 3.9 o superior** → https://www.python.org/downloads/
   (en Windows marca la casilla *"Add Python to PATH"* al instalar)
2. **MySQL Server** → https://dev.mysql.com/downloads/mysql/
   (anota el usuario, la contraseña y el puerto que elijas al instalarlo)

## 2. Puesta en marcha (3 pasos)

Abre una terminal dentro de la carpeta del proyecto y sigue estos pasos.

**Paso 1 – Instalar las librerías de Python** (solo la primera vez)

```
pip install -r requirements.txt
```

**Paso 2 – Poner tu configuración**

Abre el archivo **`config.ini`** con el Bloc de notas y cambia:

| Dato | Qué es |
|------|--------|
| `host` | Dónde está MySQL (`localhost` si es en tu mismo computador) |
| `puerto` | Puerto de MySQL (normalmente `3306`) |
| `usuario` / `password` | El usuario y la contraseña de tu MySQL |
| `base_de_datos` | El nombre que quieras para la base de datos |
| `clave_secreta` | Un texto largo y secreto (ver el comentario dentro del archivo) |
| `[admin]` | Nombre y contraseña de la cuenta del administrador |

**Paso 3 – Crear la base de datos y encender la página**

```
python crear_base_datos.py
python app.py
```

El primer comando crea la base de datos, las tablas y la cuenta del
administrador (se puede ejecutar más de una vez sin borrar nada). El segundo
enciende la página. Ábrela en el navegador: **http://localhost:5000**
(o el puerto que pusiste en `puerto_web`).

> Si `python` no funciona, prueba con `python3` (Mac/Linux) o `py` (Windows).

## 3. Cómo se usa

- **Estudiantes:** pulsan *Regístrate aquí* en el login, crean su cuenta y entran.
- **Administrador:** entra con el nombre y la contraseña de la sección `[admin]`
  de `config.ini`. Verá en el menú la opción **Denuncias**, donde puede leer
  cada denuncia y marcarla como *Pendiente*, *En revisión* o *Resuelta*.
- El estudiante puede ver en **Mi cuenta** su diario emocional y el estado de
  sus denuncias.

## 4. Privacidad (importante)

- Las contraseñas **no se guardan en texto**: se guardan cifradas (hash).
- El **diario emocional es privado**: cada persona solo ve el suyo, ni
  siquiera el administrador puede leerlo en esta versión.
- Las **denuncias** solo las puede ver el administrador.

## 5. Estructura del proyecto

```
zafezone/
├── app.py                  ← La aplicación (rutas, login, denuncias, diario)
├── configuracion.py        ← Lee el config.ini
├── crear_base_datos.py     ← Crea la base de datos y las tablas
├── config.ini              ← LO ÚNICO QUE SE EDITA (MySQL, puerto, admin)
├── requirements.txt        ← Librerías de Python necesarias
├── base_de_datos/
│   └── tablas.sql          ← Definición de las tablas
├── templates/              ← Páginas HTML
│   ├── base_login.html, login.html, registro.html
│   ├── base_app.html, principal.html, mi_cuenta.html
│   ├── admin_denuncias.html, error.html, _mensajes.html
└── static/                 ← Archivos que descarga el navegador
    ├── css/ (login.css, principal.css, extra.css)
    ├── js/  (login.js, principal.js)
    ├── img/
    └── fonts/
```

## 6. Problemas frecuentes

| Mensaje | Solución |
|---------|----------|
| `Access denied for user` | Usuario o contraseña de MySQL incorrectos en `config.ini` |
| `Can't connect to MySQL server` | MySQL está apagado, o el `host` / `puerto` están mal |
| `No module named 'flask'` | Falta el Paso 1 (`pip install -r requirements.txt`) |
| Página con "Algo salió mal" | Revisa la terminal donde corre `app.py`: ahí aparece el detalle |
| `Address already in use` | Cambia `puerto_web` en `config.ini` (por ejemplo a `5001`) |

## 7. Antes de publicar en internet

- Cambia `clave_secreta` y la contraseña del administrador.
- Pon `debug = false` en `config.ini`.
- Usa HTTPS y un servidor de producción (por ejemplo *waitress* en Windows o
  *gunicorn* en Linux) en lugar de `python app.py`.
