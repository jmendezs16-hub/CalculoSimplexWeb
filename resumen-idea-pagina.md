# Optimizador Simplex Grupo 2: resumen de la idea

## Qué queremos hacer

Una página web para una empresa que fabrica varios productos y quiere saber cuánto producir de cada uno para ganar lo máximo posible, o gastar lo mínimo, con los recursos que tiene. El problema se resuelve con el método simplex y la página muestra el resultado de forma clara. Si el usuario quiere comprobar cómo se llegó a él, también puede ver el procedimiento tabla por tabla.

El enunciado pide una aplicación que maximice o minimice funciones objetivo con restricciones lineales, que muestre el procedimiento completo y que identifique cuándo no existe solución óptima. Lo resolvemos así: el resultado va primero, el procedimiento queda en una pestaña aparte y los casos especiales se explican en un panel de ayuda.

Por ahora solo se entrega la planificación, es decir, la maqueta y esta idea. Todavía no se programa nada.

## Ejemplo que usamos para diseñar

Es el de las lámparas que se vio en clase. Una compañía fabrica dos modelos, L1 y L2.

- Trabajo manual: 20 minutos para L1 y 30 para L2, con 100 horas al mes disponibles.
- Trabajo de máquina: 20 minutos para L1 y 10 para L2, con 80 horas al mes disponibles.
- Beneficio por unidad: Q15 para L1 y Q10 para L2.

Con esos datos el modelo queda así:

- Maximizar Z = 15x₁ + 10x₂
- 20x₁ + 30x₂ ≤ 6000
- 20x₁ + 10x₂ ≤ 4800
- x₁, x₂ ≥ 0

El resultado óptimo es fabricar 210 lámparas L1 y 60 lámparas L2, con un beneficio máximo de Q3,750.

## Cómo funciona la página

El usuario recorre la página en este orden.

1. Inicio. Muestra la empresa activa, tres accesos rápidos y el historial de planificaciones anteriores con su estado.
2. Catálogo. Se configura una sola vez. Se registran los productos o modelos con su beneficio o costo por unidad, los recursos con su disponibilidad por periodo y cuánto consume cada producto de cada recurso. Así la página sirve para cualquier empresa y no solo para las lámparas.
3. Planificar. El usuario elige el periodo, si quiere maximizar beneficio o minimizar costo y qué productos incluir. Los recursos aparecen ya llenos con los valores del catálogo y se pueden ajustar si ese mes cambió algo. Opcionalmente puede poner una producción mínima o una demanda máxima por producto. El usuario nunca escribe el modelo matemático, lo arma el sistema.
4. Resultado. Es la pantalla principal. Muestra cuántas unidades fabricar de cada producto, el beneficio total, cuánto se usa de cada recurso, una tabla con otras combinaciones posibles con la mejor resaltada y las recomendaciones del sistema. Esta pantalla no muestra cálculos.
5. Comprobación. Es la pestaña opcional. Muestra el modelo en forma estándar, la tabla inicial, cada pivoteo con la variable que entra y la que sale, y la tabla final. Está pensada para quien quiera verificar el procedimiento, por ejemplo el catedrático.
6. Ayuda. Un botón con una i, visible en toda la página, abre un panel lateral con una guía de uso, el significado de los avisos y un glosario.

## Cómo se calculan las recomendaciones

No se usa inteligencia artificial. El backend las genera con reglas fijas a partir de la tabla final del simplex.

- Cuello de botella. Es el recurso con mayor valor en la fila Z de la tabla final. En el ejemplo es la máquina, y cada hora extra aportaría cerca de Q37.50.
- Hasta cuántas horas extra sirve ese valor. Se calcula con los límites en los que la solución sigue siendo factible. Para la máquina son 20 horas más y para la mano de obra 140.
- Recurso sobrante. Si la variable de holgura de un recurso vale cero, ese recurso se agota. Si vale más que cero, sobra esa cantidad.
- Alternativas cercanas. Se comparan los demás puntos de esquina contra el óptimo, como producir solo L1, que rinde el 96 por ciento del máximo.

En código basta con leer la tabla final y aplicar una regla por cada recomendación.

## Casos sin solución óptima

El enunciado pide identificar cuándo no se puede llegar a un óptimo. La página lo avisa en el resultado y lo explica en el panel de ayuda.

- Sin solución factible. Las restricciones se contradicen. Se detecta cuando una variable artificial queda en la base con valor mayor que cero.
- Solución no acotada. El beneficio podría crecer sin límite. Se detecta cuando entra una variable pero todos los valores de su columna son menores o iguales a cero.
- Soluciones múltiples. Varias combinaciones dan el mismo beneficio. Se detecta cuando una variable no básica tiene coeficiente cero en la fila Z de la tabla óptima.
- Solución degenerada. Hay un empate en la razón mínima y alguna variable básica vale cero. El resultado es válido.

## Reparto entre frontend y backend

- Frontend. Las seis pantallas de la maqueta, los formularios del catálogo y de planificar, y la forma de mostrar tablas, gráfica y avisos.
- Backend. Recibe el catálogo y el plan por una API, arma el modelo, ejecuta el simplex guardando cada tabla intermedia, detecta los casos especiales y devuelve el resultado, las tablas y las recomendaciones.
- Base de datos. Guarda el catálogo de la empresa y el historial de planificaciones.

## Módulos extra que se pueden sumar

Ya están en la maqueta el catálogo y el historial. Quedan como opcionales:

- Un módulo de escenarios tipo "¿y si?", para cambiar una disponibilidad y comparar contra el plan actual. Reutiliza el mismo cálculo.
- Usuarios con roles, administrador y analista.
- Exportar el resultado a Excel, además del PDF.

## Pendientes por decidir

- Lenguaje y herramientas del backend y del frontend.
- Si el historial guarda todas las tablas del procedimiento o las recalcula al abrirlo.
- Cuáles de los módulos opcionales entran en el alcance final.
- Una corrección para tener en cuenta si se copia la tabla final del ejemplo: el valor de s₁ en la fila de x₁ es −0.25 y no 0.25.
