# API REST

La documentación interactiva también está disponible en `http://localhost:5000/apidocs`.

Todas las respuestas son JSON salvo las descargas PDF. Excepto `POST /api/auth/login`, las rutas requieren:

```http
Authorization: Bearer <token>
```

Los errores usan el formato uniforme:

```json
{"error":{"codigo":"datos_invalidos","mensaje":"Descripción del problema."}}
```

## Salud y autenticación

### `GET /api/health`

No requiere token. Responde `200` con `{"ok":true}`.

### `POST /api/auth/login`

Petición:

```json
{"correo":"demo@grupo2.com","password":"demo1234"}
```

Responde `200` con `{"token":"…","usuario":{"id":1,"nombre":"Grupo 2","correo":"demo@grupo2.com","creado_en":"…"}}`. Credenciales incorrectas responden `401`.

### `GET /api/auth/me`

Responde con `usuario` y `empresa_activa`; la empresa puede ser `null` hasta que exista una empresa activa.

## Empresa y catálogo

### `GET, PUT /api/empresa`

`GET` devuelve el perfil de la empresa activa. `PUT` acepta uno o más campos:

```json
{"nombre":"Fábrica de lámparas","rubro":"Manufactura","moneda":"Q","periodo":"mensual"}
```

`periodo` admite `diario`, `semanal`, `mensual` o `anual`.

### Productos

- `GET /api/productos` lista los productos de la empresa activa.
- `POST /api/productos` crea uno con `codigo`, `nombre`, `beneficio_unitario` y opcionalmente `activo`.
- `PUT /api/productos/{id}` actualiza esos campos.
- `DELETE /api/productos/{id}` elimina el producto si no forma parte de resultados guardados.

Ejemplo de creación:

```json
{"codigo":"L1","nombre":"Lámpara modelo L1","beneficio_unitario":15,"activo":true}
```

### Recursos

- `GET /api/recursos` lista los recursos.
- `POST /api/recursos` crea un recurso con `nombre`, `unidad` y `disponible`.
- `PUT /api/recursos/{id}` actualiza sus campos.
- `DELETE /api/recursos/{id}` lo elimina si no aparece en resultados guardados.

### Consumos

- `GET /api/consumos` devuelve todas las parejas producto-recurso; una cantidad no guardada se representa como `0`.
- `PUT /api/consumos` reemplaza la matriz completa. Acepta un arreglo JSON directo o `{ "consumos": [...] }`; debe incluir cada combinación una sola vez.

```json
[
  {"producto_id":1,"recurso_id":1,"cantidad":20},
  {"producto_id":1,"recurso_id":2,"cantidad":20},
  {"producto_id":2,"recurso_id":1,"cantidad":30},
  {"producto_id":2,"recurso_id":2,"cantidad":10}
]
```

## Escenarios

### `GET /api/escenarios`

Devuelve el historial de la empresa activa con estado y valor Z si el escenario ya se resolvió.

### `POST /api/escenarios`

```json
{
  "nombre":"Plan de octubre",
  "periodo":"mensual",
  "objetivo":"max",
  "productos":[
    {"producto_id":1,"incluido":true,"produccion_min":null,"demanda_max":null},
    {"producto_id":2,"incluido":true,"produccion_min":null,"demanda_max":null}
  ],
  "recursos":[
    {"recurso_id":1,"disponible":6000},
    {"recurso_id":2,"disponible":4800}
  ]
}
```

`objetivo` es `max` o `min`. `recursos` puede estar vacío para conservar las disponibilidades del catálogo. Las disponibilidades, mínimos y máximos no pueden ser negativos.

### `POST /api/escenarios/{id}/validar`

No ejecuta el simplex. Responde `{"valido":true,"avisos":[]}` o incluye avisos de estructura y de recursos insuficientes para cubrir los mínimos.

### `POST /api/escenarios/{id}/resolver`

Ejecuta el simplex y guarda el resultado y todos sus detalles dentro de una transacción. Responde `201` al crear el primer resultado o `200` al reemplazarlo:

```json
{"resultado_id":1}
```

### `POST /api/escenarios/{id}/duplicar`

Duplica productos, límites y disponibilidades, sin copiar el resultado. El nombre es opcional:

```json
{"nombre":"Copia para noviembre"}
```

## Resultados

### `GET /api/resultados/{id}`

Incluye escenario, estado, `valor_z`, variables (producto, cantidad y aporte), uso/disponibilidad/holgura/precio sombra de recursos, posibilidades cercanas y recomendaciones.

### `GET /api/resultados/{id}/procedimiento`

Devuelve la forma estándar usada, diagnósticos y todos los tableaux guardados. Cada iteración incluye base, columnas, filas exactas como fracciones, pivote, variable entrante y variable saliente.

### `GET /api/resultados/{id}/pdf?tipo=reporte`

Descarga el reporte PDF. Usa `tipo=comprobacion` para descargar las tablas de iteración con el pivote resaltado.

## Aislamiento de datos

Las rutas filtran el catálogo por la empresa activa. Escenarios y resultados verifican que su empresa pertenezca al usuario autenticado. Si un recurso no existe o pertenece a otra cuenta, la API responde como no encontrado.
