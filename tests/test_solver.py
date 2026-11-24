"""Pruebas de los algoritmos BFS y DFS."""

from collections import deque

import pytest

from maze import Maze, SolverError, bfs, comparar, dfs, generate, solve


#: Laberinto con dos rutas entre inicio y meta. BFS recorre el pasillo
#: superior (10 pasos) y DFS se mete por la rama inferior izquierda (14 pasos).
DOS_RUTAS = """\
#########
#S......#
#.#####.#
#.#...#.#
#.#.#.#.#
#...#..G#
#########
"""

SIN_RUTA = """\
#####
#S#G#
#####
"""


def pasos(maze, start, goal):
    """BFS de referencia, independiente del codigo de produccion."""
    dist = {start: 0}
    cola = deque([start])
    while cola:
        nodo = cola.popleft()
        if nodo == goal:
            return dist[nodo]
        for vecino in maze.neighbors(nodo):
            if vecino not in dist:
                dist[vecino] = dist[nodo] + 1
                cola.append(vecino)
    return None


def es_camino_valido(maze, camino):
    if not camino:
        return False
    if camino[0] != maze.start or camino[-1] != maze.goal:
        return False
    if len(set(camino)) != len(camino):
        return False
    for actual, siguiente in zip(camino, camino[1:]):
        if siguiente not in maze.neighbors(actual):
            return False
    return True


# --------------------------------------------------------------------- BFS


def test_bfs_encuentra_el_camino_mas_corto():
    maze = Maze.from_text(DOS_RUTAS)
    resultado = bfs(maze)
    assert resultado.solved
    assert resultado.path_length == 10
    assert resultado.path_length == pasos(maze, maze.start, maze.goal)
    assert es_camino_valido(maze, resultado.path)


def test_bfs_expande_en_orden_de_distancia():
    """En BFS la distancia de expansion nunca disminuye."""
    maze = Maze.from_text(DOS_RUTAS)
    resultado = bfs(maze)
    distancias = [pasos(maze, maze.start, nodo) for nodo in resultado.visits]
    assert distancias == sorted(distancias)


def test_bfs_dentro_de_la_frontera():
    """Los nodos que expande BFS no superan la profundidad del camino optimo."""
    maze = Maze.from_text(DOS_RUTAS)
    resultado = bfs(maze)
    optimo = resultado.path_length
    assert all(pasos(maze, maze.start, n) <= optimo for n in resultado.visits)


# --------------------------------------------------------------------- DFS


def test_dfs_encuentra_alguna_ruta_valida():
    maze = Maze.from_text(DOS_RUTAS)
    resultado = dfs(maze)
    assert resultado.solved
    assert es_camino_valido(maze, resultado.path)


def test_dfs_puede_devolver_un_camino_mas_largo_que_bfs():
    maze = Maze.from_text(DOS_RUTAS)
    corto = bfs(maze)
    largo = dfs(maze)
    assert largo.path_length == 14
    assert largo.path_length > corto.path_length


def test_dfs_usa_pila_y_bfs_cola():
    """DFS debe llegar al fondo antes de abrir una rama nueva."""
    maze = Maze.from_text(DOS_RUTAS)
    resultado = dfs(maze)
    assert resultado.visits[1] == (2, 1), "DFS debe bajar en vertical, no avanzar en horizontal"
    resultado_bfs = bfs(maze)
    assert resultado_bfs.visits[1] == (1, 2), "BFS debe avanzar en horizontal (menor distancia)"


# --------------------------------------------------------------- casos borde


@pytest.mark.parametrize("algoritmo", ["bfs", "dfs"])
def test_sin_ruta(algoritmo):
    maze = Maze.from_text(SIN_RUTA)
    resultado = solve(maze, algoritmo)
    assert not resultado.solved
    assert resultado.path == []
    assert resultado.path_length == 0
    assert resultado.expanded > 0


@pytest.mark.parametrize("algoritmo", ["bfs", "dfs"])
def test_inicio_pegado_a_la_meta(algoritmo):
    maze = Maze(walls=[[0, 0], [1, 1]], start=(0, 0), goal=(0, 1))
    resultado = solve(maze, algoritmo)
    assert resultado.solved
    assert resultado.path == [(0, 0), (0, 1)]
    assert resultado.path_length == 1


@pytest.mark.parametrize("algoritmo", ["bfs", "dfs"])
def test_metricas_coherentes(algoritmo):
    maze = generate(rows=21, cols=21, seed=11)
    resultado = solve(maze, algoritmo)
    assert resultado.solved
    assert resultado.expanded == len(resultado.visits) == len(resultado.frontiers)
    assert len(set(resultado.visits)) == len(resultado.visits)
    assert resultado.visits[0] == maze.start
    assert resultado.visits[-1] == maze.goal
    assert resultado.elapsed_ms >= 0
    assert resultado.max_frontier >= 1


@pytest.mark.parametrize("algoritmo", ["bfs", "dfs"])
def test_bfs_nunca_es_peor_que_dfs_en_laberintos_aleatorios(algoritmo):
    for semilla in range(6):
        maze = generate(rows=25, cols=25, seed=semilla)
        assert solve(maze, "bfs").path_length <= solve(maze, "dfs").path_length


def test_algoritmo_desconocido():
    maze = Maze.from_text(DOS_RUTAS)
    with pytest.raises(SolverError):
        solve(maze, "a_estrella")


def test_inicio_no_transitable():
    maze = Maze.from_text(DOS_RUTAS)
    with pytest.raises(SolverError):
        solve(maze, "bfs", start=(0, 0))


def test_serializacion_del_resultado():
    maze = Maze.from_text(DOS_RUTAS)
    datos = bfs(maze).to_dict()
    assert set(datos) >= {
        "algorithm",
        "solved",
        "path",
        "visits",
        "expanded",
        "path_length",
        "elapsed_ms",
        "max_frontier",
    }
    assert isinstance(datos["path"][0], list)


def test_comparacion_reporta_ventaja():
    maze = Maze.from_text(DOS_RUTAS)
    datos = comparar(maze)
    assert datos["bfs"]["path_length"] == 10
    assert datos["dfs"]["path_length"] == 14
    assert datos["ventaja_bfs_pct"] == 40.0
