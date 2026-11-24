# Rutas en laberintos · BFS vs DFS

Proyecto final de **Tópicos Avanzados de Ingeniería de Software**.

Aplicación web en Python que resuelve laberintos con dos algoritmos de búsqueda
en grafos —**BFS** (búsqueda en anchura) y **DFS** (búsqueda en profundidad)—
seleccionables desde la interfaz, con animación paso a paso, métricas de
desempeño y comparación lado a lado sobre el mismo laberinto.

---

## 1. Requisitos

- Python 3.10 o superior (probado en 3.14).
- Navegador moderno (Chrome, Firefox, Edge).
- No requiere paquetes del sistema: todo se instala en un entorno virtual.

## 2. Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Ejecución

```bash
source .venv/bin/activate
python app.py
```

Abrir <http://127.0.0.1:5000> en el navegador.

También se puede usar el atajo:

```bash
./arrancar.sh
```

## 4. Uso

| Acción | Cómo |
|---|---|
| Generar laberinto aleatorio | Ajustar filas, columnas, semilla y «Atajos», y pulsar **Generar laberinto** |
| Semilla al azar | Botón **⟳** junto a la semilla (o tecla `N`): elige una semilla nueva y genera de inmediato |
| Elegir algoritmo | Botones **BFS** / **DFS** del panel 3 |
| Resolver e animar | **Resolver ruta** (o tecla `R`) |
| Comparar ambos | **Comparar BFS vs DFS** (o tecla `C`) |
| Dibujar muros | Clic o arrastrar sobre el lienzo |
| Borrar muros | Arrastrar con `Shift` o hacer clic sobre un muro |
| Mover el inicio | `Alt` + clic |
| Mover la meta | `Ctrl` + clic |
| Guardar / abrir `.txt` | Botones **Guardar .txt** / **Cargar .txt** |
| Guardar evidencia | **Guardar captura PNG** (genera la imagen de la vista actual) |

Atajos: `G` generar, `N` semilla aleatoria, `R` resolver, `C` comparar, `B` BFS, `D` DFS.

La semilla hace que un laberinto sea **reproducible**: la misma semilla y las
mismas dimensiones siempre producen el mismo laberinto, lo que permite repetir
la demostración y comparar resultados entre ejecuciones.

El control **Atajos** abre callejones sin salida y crea rutas alternativas. Con
0 % el laberinto es *perfecto* (un único camino entre dos celdas), por lo que
BFS y DFS encuentran el mismo camino; al subir el porcentaje aparecen ciclos y
las diferencias entre algoritmos se hacen visibles.

## 5. Formato de archivo `.txt`

```text
#########
#S......#
#.#####.#
#.#...#.#
#...#..G#
#########
```

- `#` muro
- `.` o espacio: pasillo
- `S` inicio (obligatorio)
- `G` o `E`: meta (obligatoria)

## 6. Estructura del proyecto

```
proyecto_integrador/
├── app.py                  Servidor Flask y API JSON
├── maze/
│   ├── grid.py             Modelo: matriz, vecinos, lectura/escritura
│   ├── generator.py        Generación por backtracking con semilla
│   └── solver.py           Motor de búsqueda, BFS y DFS
├── templates/index.html    Interfaz
├── static/css/styles.css   Estilos
├── static/js/app.js        Canvas, animación y eventos
├── tests/                  Pruebas con pytest (54 casos)
├── docs/                   Reporte en PDF y capturas
├── requirements.txt
└── arrancar.sh
```

## 7. API

| Método | Ruta | Cuerpo | Respuesta |
|---|---|---|---|
| GET | `/api/salud` | — | estado y algoritmos disponibles |
| POST | `/api/generate` | `{rows, cols, seed, braid}` | `{maze, text}` |
| POST | `/api/parse` | `{text}` | `{maze, text}` |
| POST | `/api/solve` | `{maze \| text, algorithm}` | `{maze, result}` |
| POST | `/api/compare` | `{maze \| text}` | `{maze, results}` |

Ejemplo:

```bash
curl -s -X POST http://127.0.0.1:5000/api/solve \
  -H 'Content-Type: application/json' \
  -d '{"text":"#######\n#S....#\n#.###.#\n#....G#\n#######","algorithm":"bfs"}'
```

Los errores de validación responden `400` con `{"error": "..."}`.

## 8. Pruebas

```bash
source .venv/bin/activate
pytest -q                     # suite completa
pytest --cov=maze --cov=app   # con cobertura
```

Las pruebas cubren: lectura y escritura de laberintos, generación reproducible
y conectividad, optimalidad de BFS, validez de las rutas, casos sin solución y
la API HTTP.

## 9. Decisiones de diseño

- **Un solo motor para dos algoritmos.** BFS y DFS comparten `_buscar()` y solo
  cambian la estructura de frontera: `deque` FIFO contra `list` LIFO. Esto
  evita duplicar lógica y hace que la comparación sea justa, porque ambos
  recorren el mismo código.
- **El solver es un generador.** Emite eventos con el nodo expandido y el
  tamaño de la frontera, de modo que la animación del navegador se construye
  con el mismo cálculo que se usa en las pruebas.
- **La lógica no depende de Flask.** El paquete `maze` no importa nada de la
  web; se puede usar desde consola o desde otra interfaz.
- **Orden fijo de vecinos** (arriba, derecha, abajo, izquierda). Hace los
  resultados deterministas y las pruebas estables.
- **Sin dependencias de frontend.** HTML, CSS y JavaScript sin compilación:
  el proyecto se ejecuta con un solo comando.

## 10. Documentación del proyecto

| Archivo | Contenido |
|---|---|
| `docs/Reporte_BFS_DFS_Laberintos.pdf` | Reporte completo: planteamiento, objetivos, requisitos, marco teórico, arquitectura, diagrama de flujo, implementación, pruebas, evidencias, resultados, conclusiones, guion de exposición y anexo de código |
| `docs/capturas/` | Diagramas y capturas de ejecución usadas como evidencia |
| `docs/diagramas.html` | Fuente editable de los diagramas (se abre en el navegador) |

El PDF no incluye portada: se agrega por separado según la entrega.

## 11. Complejidad

Con `V` celdas transitables y `E` conexiones entre ellas:

| Algoritmo | Tiempo | Espacio (frontera) | Garantía |
|---|---|---|---|
| BFS | O(V + E) | O(V) | camino más corto en pasos |
| DFS | O(V + E) | O(V) | encuentra alguna ruta, no necesariamente la más corta |

En un laberinto perfecto (un solo camino entre dos celdas) ambos devuelven la
misma ruta; la diferencia aparece cuando hay ciclos o rutas alternativas, y ahí
BFS siempre gana en longitud mientras DFS suele expandir menos nodos.
