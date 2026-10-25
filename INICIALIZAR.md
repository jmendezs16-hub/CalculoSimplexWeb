# Inicializar el proyecto (Windows / PowerShell)

Estructura:

```text
proyecto final/
  optimizador-simplex/optimizador-simplex/                    # backend Flask (puerto 5000)
  optimizador-simplex-frontend/optimizador-simplex-frontend/  # frontend React + Vite (puerto 5173)
  simplex_db.sql                                              # volcado completo de la base (phpMyAdmin / MariaDB)
```

Los entornos virtuales (`.venv`) no se incluyen: se crean en cada máquina.

## Requisitos
- Python 3.10+ y Node.js 20+
- MySQL 8 o MariaDB 10.4+ (por ejemplo el de XAMPP) en ejecución

## 1. Base de datos
Elige **una** de las dos opciones. Ambas crean las 13 tablas que usan los modelos y el usuario demo (`demo@grupo2.com` / `demo1234`) con la empresa de lámparas.

**A. Volcado `simplex_db.sql`** (phpMyAdmin → crear base `simplex_db` → Importar). Ya incluye datos de ejemplo.

**B. Scripts del backend**, en este orden, desde MySQL Workbench o consola:
1. `optimizador-simplex/optimizador-simplex/database/schema.sql` (crea `simplex_db` y las tablas)
2. `optimizador-simplex/optimizador-simplex/database/seed.sql` (usuario, empresa, productos, recursos y consumos)

Si usas un usuario distinto de `root`, créalo con permisos sobre `simplex_db`:
```sql
CREATE USER 'simplex'@'localhost' IDENTIFIED BY 'cambia_esto';
GRANT ALL PRIVILEGES ON simplex_db.* TO 'simplex'@'localhost';
```

## 2. Backend (http://127.0.0.1:5000)
```powershell
cd optimizador-simplex\optimizador-simplex
py -m venv .venv
.\.venv\Scripts\Activate.ps1      # si se bloquea: Set-ExecutionPolicy -Scope Process Bypass
python -m pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```
Edita `.env`:
```dotenv
DATABASE_URL=mysql+pymysql://USUARIO:CLAVE@127.0.0.1:3306/simplex_db?charset=utf8mb4
JWT_SECRET_KEY=<texto aleatorio de 32+ caracteres>
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```
(Clave aleatoria: `python -c "import secrets; print(secrets.token_urlsafe(48))"`. Si el usuario no tiene clave, usa `USUARIO@127.0.0.1`.)

Inicia:
```powershell
python run.py
```
Comprueba: http://127.0.0.1:5000/api/health → `{"ok": true}` y la documentación en http://127.0.0.1:5000/apidocs

Alternativa sin MySQL, solo para pruebas: `DATABASE_URL=sqlite:///app.db`, luego `python -m scripts.init_db` y `python -m scripts.create_demo_user` (la empresa se crea con el seed o a mano).

## 3. Frontend (http://localhost:5173)
```powershell
cd optimizador-simplex-frontend\optimizador-simplex-frontend
npm install
if (!(Test-Path .env)) { Copy-Item .env.example .env }   # VITE_API_URL=http://127.0.0.1:5000/api
npm run dev
```
Abre http://localhost:5173 e inicia sesión con `demo@grupo2.com` / `demo1234`.

## 4. Flujo de uso
1. **Productos** y **Recursos**: registra el catálogo.
2. **Consumos**: llena la matriz (cuánto recurso usa cada producto). Sin esto el resultado sale `no_acotado`.
3. **Escenarios**: elige objetivo (max/min), productos, límites y disponibilidades; crea el escenario y pulsa «Resolver con Simplex».
4. Resultado: plan, uso de recursos, combinaciones alternativas y recomendaciones. Pestaña **Comprobación** para el paso a paso, y botones de PDF.
5. Botón **i** (abajo a la derecha): ayuda, significado de avisos y glosario.

Ejemplo esperado con las lámparas (L1: 20/20 min, Q15; L2: 30/10 min, Q10; 6000 y 4800 min): L1 = 210, L2 = 60, Z = Q3,750.

## Problemas comunes
- `cryptography package is required`: ya está en `requirements.txt`; reinstala con `pip install -r requirements.txt`.
- `Access denied` / `Can't connect`: revisa usuario, clave y que MySQL esté encendido; la base debe llamarse `simplex_db`.
- Error de CORS: el origen del navegador debe estar en `CORS_ORIGINS`; reinicia el backend tras cambiarlo.
- El login falla con «usuario sin empresa»: falta el seed (o el volcado); el usuario necesita una empresa activa.
- Instalación del venv falla por «nombre de archivo demasiado largo»: mueve el proyecto a una ruta corta (p. ej. `C:\proyecto`).
- Cambiaste `.env` del frontend: reinicia `npm run dev`.
