# Modelo matemático y método simplex

## Forma estándar usada por la API

El escenario produce una función objetivo y restricciones para variables de decisión no negativas:

```text
max/min Z = c₁x₁ + c₂x₂ + … + cₙxₙ
A x (<=, >=, =) b
xⱼ >= 0
```

Las primeras filas de `A` representan los recursos. Después se agregan las cotas de producción mínima (`xⱼ >= mínimo`) y de demanda máxima (`xⱼ <= máximo`). La disponibilidad del escenario sustituye a la disponibilidad base de cada recurso cuando se proporciona un ajuste.

## Tableau y pivoteo

Las entradas se convierten a `fractions.Fraction` antes de iniciar el cálculo. En cada tableau se registra la base, las columnas, los coeficientes y el lado derecho. Para maximizar, se elige como variable entrante la primera variable no básica con costo reducido positivo, siguiendo Bland. La fila saliente se elige con la razón no negativa mínima; los empates también se resuelven por Bland. El pivote se aplica con eliminación de Gauss-Jordan.

El historial guarda el tableau antes de cada pivote y un tableau terminal. Cada registro incluye fase, pivote, variable que entra y variable que sale. Las fracciones se serializan como texto para no perder precisión.

## Restricciones de dos fases y minimización

- Una restricción `<=` obtiene una variable de holgura.
- Una restricción `>=` obtiene una variable de exceso y una artificial.
- Una igualdad obtiene una variable artificial.
- La fase I maximiza el negativo de la suma de artificiales. Si el óptimo de esa fase es menor que cero, el modelo es infactible.
- Antes de la fase II se retiran las artificiales; las filas redundantes se eliminan.
- Para minimizar, el algoritmo maximiza `-Z` internamente y devuelve `Z` y los precios sombra con el signo del problema original.

## Casos especiales y valores duales

- `no_acotado`: hay una variable entrante con costo reducido favorable, pero no existe coeficiente positivo para calcular razón de salida.
- `multiple`: un tableau óptimo tiene una variable no básica con costo reducido cero.
- `degenerado`: alguna solución básica vale cero o hubo empate en la razón mínima.
- `infactible`: las artificiales no pueden llegar a cero en fase I.
- `optimo`: solución óptima única y no degenerada según esos criterios.

Las holguras se calculan respecto al sentido original de cada restricción. Los precios sombra se obtienen con los costos básicos y la transformación acumulada de las restricciones. El servicio de recomendaciones usa esa misma transformación para estimar cuánto puede aumentar o disminuir un lado derecho conservando la base óptima.

## Ejemplo de las lámparas

```text
Maximizar Z = 15x₁ + 10x₂
20x₁ + 30x₂ <= 6000
20x₁ + 10x₂ <= 4800
x₁, x₂ >= 0
```

El óptimo es `x₁ = 210`, `x₂ = 60`, `Z = 3750`. Las dos restricciones quedan vinculantes. En el historial se muestra el tableau inicial y las tablas anteriores a cada pivote; el contador de pivoteos es dos.

