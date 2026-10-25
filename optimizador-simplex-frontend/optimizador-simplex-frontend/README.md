# Frontend de Optimizador Simplex

Interfaz creada con React + Vite + React Router + Axios para conectarse al backend Flask existente.

## Requisitos
- Node.js 20 o superior (recomendado).
- Backend Flask ejecutándose en `http://127.0.0.1:5000`.
- Base de datos inicializada y usuario con empresa activa, productos y recursos.

## Instalación (Windows / PowerShell)
1. Descomprime esta carpeta.
2. Abre una terminal dentro de `optimizador-simplex-frontend`.
3. Ejecuta:
   ```powershell
   npm install
   Copy-Item .env.example .env
   npm run dev
   ```
4. Abre la dirección que Vite muestre, normalmente `http://localhost:5173`.

El archivo `.env` del frontend define `VITE_API_URL=http://127.0.0.1:5000/api`. Si tu backend está en otra dirección, cambia esa variable y reinicia Vite.

## Usuario de demostración
El README del backend indica estas credenciales locales de demo:
- Correo: `demo@grupo2.com`
- Contraseña: `demo1234`

Solo funcionan si cargaste los datos semilla y el usuario demo existe. No las uses en un entorno público.

## Qué incluye
- Pantalla de inicio de sesión conectada a `POST /api/auth/login`.
- Protección visual de las pantallas con el token JWT y comprobación `GET /api/auth/me`.
- Panel general con conteos y últimos escenarios.
- Listado y formulario para crear productos.
- Listado y formulario para crear recursos.
- Creación de escenarios con objetivo, productos incluidos, producción mínima, demanda máxima y disponibilidad de recursos.
- Botón para ejecutar Simplex y mostrar el resultado, variables, uso de recursos y recomendaciones.
- Navegación con React Router y solicitudes HTTP mediante Axios.
- Diseño adaptable a escritorio y móvil.

## Importante: consumos de recursos
La interfaz no inventa automáticamente la matriz de consumos. El backend tiene `PUT /api/consumos` para guardar el consumo de cada combinación producto-recurso. Para que el resultado matemático represente correctamente el caso real, esa matriz debe estar configurada. Si no lo está, el backend puede rechazar el cálculo o producir un modelo incompleto.

## Cómo se conecta al backend
Axios agrega automáticamente `Authorization: Bearer <token>` a las solicitudes después del inicio de sesión. Los endpoints utilizados se documentan en el backend en `docs/api.md` y también se pueden revisar en `http://localhost:5000/apidocs`.

## Alcance actual
Esta entrega implementa una primera interfaz funcional para los flujos principales. No incluye edición/eliminación de productos y recursos, pantalla para editar la matriz de consumos, ni visualización paso a paso de tableaux del método Simplex. Esas pantallas se pueden agregar como siguiente fase.
