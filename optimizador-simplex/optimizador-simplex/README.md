# Optimizador Simplex — backend

API REST para gestionar el catálogo de una empresa, construir escenarios de producción y resolverlos con el método simplex.

## Tecnologías

- Python y Flask con application factory.
- SQLAlchemy, MySQL 8 y PyMySQL.
- JWT para proteger la API.
- Marshmallow para validar entradas, Flasgger para OpenAPI y ReportLab para PDF.
- El motor simplex está en Python puro y usa `fractions.Fraction`.

## Requisitos

- Python 3.10 o posterior.
- MySQL 8 en ejecución.
- PowerShell en Windows o una terminal compatible.

## Instalación en Windows

Desde la carpeta raíz del proyecto:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Si PowerShell bloquea la activación, permite scripts para esta sesión y vuelve a activarlo:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Base de datos MySQL

1. Inicia MySQL y crea la base y las tablas. Puedes ejecutar `database/schema.sql` desde MySQL Workbench o desde la consola de MySQL.
2. Carga los datos demostrativos ejecutando `database/seed.sql` una vez. Crea `demo@grupo2.com` con contraseña `demo1234`, la empresa de lámparas, productos, recursos y consumos.
3. Crea el usuario de MySQL de la aplicación (o usa el que ya configuraste):

```sql
CREATE USER 'simplex'@'localhost' IDENTIFIED BY 'cambia_esto';
GRANT ALL PRIVILEGES ON simplex_db.* TO 'simplex'@'localhost';
```

4. Si todavía no tienes `.env`, créalo desde la plantilla. El comando conserva un `.env` existente:

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

Edita el `.env` de la raíz. No publiques este archivo ni compartas su clave JWT.

Ejemplo de variables:

```dotenv
DATABASE_URL=mysql+pymysql://simplex:TU_PASSWORD@localhost:3306/simplex_db
JWT_SECRET_KEY=PEGA_AQUI_UN_SECRETO_ALEATORIO_LARGO
FRONTEND_ORIGIN=http://localhost:5173
```

Para generar una clave local en PowerShell:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

`FRONTEND_ORIGIN` puede contener varios orígenes separados por coma. Si usas la variable antigua `CORS_ORIGINS`, esta tiene prioridad.

Si trabajas con SQLite en desarrollo, puedes configurar `DATABASE_URL=sqlite:///app.db`; crea las tablas faltantes con:

```powershell
python -m scripts.init_db
```

El mismo comando sirve para una base MySQL ya creada. En MySQL, crea primero `simplex_db` o ejecuta `database/schema.sql`.

## Crear un usuario demo manualmente

Si no cargas `database/seed.sql`, crea las tablas primero y ejecuta:

```powershell
python -m scripts.create_demo_user --nombre "Usuario Demo" --correo demo@example.com
```

El script pide la contraseña dos veces y guarda únicamente su hash. El usuario nuevo no incluye automáticamente catálogo de lámparas; para ese conjunto de datos usa el seed SQL.

## Ejecutar la API

Con el entorno virtual activo y el archivo `.env` configurado:

```powershell
python run.py
```

La API se inicia en `http://127.0.0.1:5000`. La raíz `/` no tiene una página web y puede responder `404`; comprueba el backend en:

- Salud: `http://127.0.0.1:5000/api/health` → `{"ok": true}`
- Swagger: `http://127.0.0.1:5000/apidocs`

## Flujo de autenticación y uso

1. Envía `POST /api/auth/login` con correo y contraseña. Copia `token` de la respuesta.
2. Envía las demás solicitudes con `Authorization: Bearer <token>`.
3. Configura el perfil y el catálogo (`/api/empresa`, `/api/productos`, `/api/recursos`, `/api/consumos`).
4. Crea un escenario en `POST /api/escenarios`, valida con `/api/escenarios/{id}/validar` y calcula con `/api/escenarios/{id}/resolver`.
5. Consulta el resultado y su procedimiento, o descarga un PDF.

El usuario de seed puede iniciar sesión con `demo@grupo2.com` y `demo1234`. Cambia esa contraseña antes de usar los datos fuera de una demostración local.

## Estructura del backend

```text
app/
  __init__.py             # create_app y registro de extensiones/blueprints
  config.py               # configuraciones development/testing/production
  extensions.py           # SQLAlchemy, JWT y CORS
  auth/                   # login, perfil actual y errores JWT
  catalog/                # empresa, productos, recursos y consumos
  models/                 # entidades SQLAlchemy
  results/                # consulta de resultados y PDF
  scenarios/              # historial, creación, validación y duplicación
  schemas/                # validación Marshmallow
  services/               # simplex, modelo y recomendaciones
database/                 # schema.sql y seed.sql
docs/                     # contrato de la API
scripts/                  # utilidades para crear tablas/usuario demo
```

## Configuraciones

`create_app("development")` usa valores de desarrollo; `create_app("testing")` usa SQLite en memoria; `create_app("production")` requiere `JWT_SECRET_KEY`. Para producción, configura una clave fuerte y un servidor WSGI apropiado; `py run.py` es para desarrollo local.

El frontend React todavía vive fuera del alcance de esta carpeta backend. Su origen debe coincidir con `FRONTEND_ORIGIN`.

## Estado de pruebas

Las dependencias de `pytest`, `pytest-bdd` y `pytest-cov` quedan declaradas, pero aún no hay carpeta `tests/` ni se midió cobertura. Por eso esta entrega no afirma que pase la meta de cobertura del 80 % de la guía.

