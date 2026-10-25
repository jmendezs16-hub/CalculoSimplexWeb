# Diagrama entidad-relación

```mermaid
erDiagram
    USUARIOS ||--o{ EMPRESAS : posee
    EMPRESAS ||--o{ PRODUCTOS : ofrece
    EMPRESAS ||--o{ RECURSOS : dispone
    PRODUCTOS ||--o{ CONSUMOS : requiere
    RECURSOS ||--o{ CONSUMOS : consumido_por
    EMPRESAS ||--o{ ESCENARIOS : planifica
    ESCENARIOS ||--o{ ESCENARIO_PRODUCTOS : configura
    PRODUCTOS ||--o{ ESCENARIO_PRODUCTOS : incluido
    ESCENARIOS ||--o{ ESCENARIO_RECURSOS : ajusta
    RECURSOS ||--o{ ESCENARIO_RECURSOS : limitado
    ESCENARIOS ||--o| RESULTADOS : calcula
    RESULTADOS ||--o{ RESULTADO_VARIABLES : produce
    PRODUCTOS ||--o{ RESULTADO_VARIABLES : variable
    RESULTADOS ||--o{ RESULTADO_RECURSOS : consume
    RECURSOS ||--o{ RESULTADO_RECURSOS : recurso
    RESULTADOS ||--o{ RECOMENDACIONES : sugiere
    RESULTADOS ||--o{ ITERACIONES : documenta
```

Las tablas de asociación (`consumos`, `escenario_productos`, `escenario_recursos`, `resultado_variables` y `resultado_recursos`) usan claves primarias compuestas según `database/schema.sql`.

