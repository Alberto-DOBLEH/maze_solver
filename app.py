"""Servidor web del proyecto: rutas de laberinto con BFS y DFS.

La aplicacion solo expone la logica del paquete ``maze`` mediante una API
JSON muy pequena. Toda la parte visual (canvas, animacion, interaccion con
el mouse) vive en ``static/js/app.js``.

Rutas:
    GET  /              -> interfaz web
    GET  /api/salud     -> comprobacion de que el servidor responde
    POST /api/generate  -> genera un laberinto aleatorio reproducible
    POST /api/parse     -> convierte el texto de un archivo .txt en laberinto
    POST /api/solve     -> resuelve con BFS o DFS
    POST /api/compare   -> resuelve con ambos algoritmos y los contrasta
"""

from __future__ import annotations

from flask import Flask, jsonify, render_template, request

from maze import ALGORITMOS, Maze, MazeError, SolverError, comparar, generate, solve

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

#: Tope de celdas para no bloquear el servidor con peticiones absurdas.
MAX_CELDAS = 40_000


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/salud")
def salud():
    return jsonify({"estado": "ok", "algoritmos": list(ALGORITMOS)})


def _cuerpo_json():
    datos = request.get_json(silent=True)
    if datos is None:
        raise MazeError("Se esperaba un cuerpo JSON en la peticion.")
    return datos


def _leer_laberinto(datos):
    if "maze" in datos:
        laberinto = Maze.from_dict(datos["maze"])
    elif "text" in datos:
        laberinto = Maze.from_text(datos["text"])
    else:
        raise MazeError("Falta el laberinto: envia 'maze' o 'text'.")
    if laberinto.rows * laberinto.cols > MAX_CELDAS:
        raise MazeError(
            f"El laberinto excede el limite de {MAX_CELDAS} celdas "
            f"({laberinto.rows}x{laberinto.cols})."
        )
    return laberinto


@app.post("/api/generate")
def api_generate():
    datos = _cuerpo_json()
    try:
        filas = int(datos.get("rows", 21))
        columnas = int(datos.get("cols", 21))
        braid = float(datos.get("braid", 0.0))
    except (TypeError, ValueError):
        raise MazeError("'rows', 'cols' y 'braid' deben ser numericos.")

    if filas * columnas > MAX_CELDAS:
        raise MazeError(f"El laberinto excede el limite de {MAX_CELDAS} celdas.")

    semilla = datos.get("seed")
    if semilla is not None:
        try:
            semilla = int(semilla)
        except (TypeError, ValueError):
            raise MazeError("'seed' debe ser un numero entero.")

    laberinto = generate(rows=filas, cols=columnas, seed=semilla, braid=braid)
    return jsonify({"maze": laberinto.to_dict(), "text": laberinto.to_text()})


@app.post("/api/parse")
def api_parse():
    datos = _cuerpo_json()
    texto = datos.get("text")
    if not isinstance(texto, str):
        raise MazeError("'text' debe ser una cadena con el laberinto.")
    laberinto = Maze.from_text(texto)
    if laberinto.rows * laberinto.cols > MAX_CELDAS:
        raise MazeError(f"El laberinto excede el limite de {MAX_CELDAS} celdas.")
    return jsonify({"maze": laberinto.to_dict(), "text": laberinto.to_text()})


@app.post("/api/solve")
def api_solve():
    datos = _cuerpo_json()
    laberinto = _leer_laberinto(datos)
    algoritmo = datos.get("algorithm", "bfs")
    resultado = solve(laberinto, algoritmo)
    return jsonify({"maze": laberinto.to_dict(), "result": resultado.to_dict()})


@app.post("/api/compare")
def api_compare():
    datos = _cuerpo_json()
    laberinto = _leer_laberinto(datos)
    return jsonify({"maze": laberinto.to_dict(), "results": comparar(laberinto)})


@app.errorhandler(MazeError)
@app.errorhandler(SolverError)
def error_de_entrada(error):
    return jsonify({"error": str(error)}), 400


@app.errorhandler(404)
def no_encontrado(error):
    return jsonify({"error": "Ruta no encontrada."}), 404


@app.errorhandler(405)
def metodo_no_permitido(error):
    return jsonify({"error": "Metodo no permitido."}), 405


if __name__ == "__main__":
    # host local: uso academico, no se pretende exponer el servicio.
    app.run(host="127.0.0.1", port=5000, debug=True)
