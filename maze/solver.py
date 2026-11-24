"""Algoritmos de busqueda: BFS y DFS.

Ambos algoritmos comparten el mismo motor (``_buscar``) y solo se diferencian
en la estructura de datos que usan como frontera:

    BFS  ->  cola FIFO (``collections.deque``)  ->  explora por niveles
    DFS  ->  pila LIFO (``list`` como pila)     ->  explora en profundidad

El motor es un *generador*: en cada iteracion emite un evento con el nodo que
expande y el tamano de la frontera en ese instante. Esto permite que la
interfaz web anime la busqueda paso a paso sin duplicar la logica, y que las
pruebas automaticas consuman el mismo resultado.

Consecuencia teorica que el proyecto demuestra en pantalla:
BFS garantiza el camino mas corto en numero de pasos; DFS solo garantiza
encontrar *alguna* ruta, que puede ser mucho mas larga.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field

from .grid import Maze

FIFO = "fifo"
LIFO = "lifo"

ALGORITMOS = ("bfs", "dfs")


class SolverError(ValueError):
    """Se pidio un algoritmo desconocido."""


@dataclass
class SolveResult:
    """Resultado completo de una busqueda."""

    algorithm: str
    solved: bool
    path: list[tuple[int, int]] = field(default_factory=list)
    visits: list[tuple[int, int]] = field(default_factory=list)
    frontiers: list[int] = field(default_factory=list)
    expanded: int = 0
    elapsed_ms: float = 0.0

    @property
    def path_length(self):
        """Numero de pasos del camino (0 si no hay solucion)."""
        return max(len(self.path) - 1, 0)

    @property
    def max_frontier(self):
        return max(self.frontiers) if self.frontiers else 0

    def to_dict(self):
        return {
            "algorithm": self.algorithm,
            "solved": self.solved,
            "path": [list(nodo) for nodo in self.path],
            "visits": [list(nodo) for nodo in self.visits],
            "frontiers": self.frontiers,
            "expanded": self.expanded,
            "path_length": self.path_length,
            "elapsed_ms": round(self.elapsed_ms, 3),
            "max_frontier": self.max_frontier,
        }


def _buscar(maze, start, goal, estructura, came_from):
    """Motor generico de busqueda en grafos.

    Emite tuplas ``("visita", nodo, tamano_frontera)`` cada vez que extrae un
    nodo de la frontera y ``("fin", nodo, 0)`` al alcanzar la meta.

    ``came_from`` se recibe por referencia y se va llenando en el momento de
    encolar cada nodo: asi se evitan ciclos y al terminar basta con remontar
    los predecesores desde la meta para reconstruir el camino exacto.
    """
    frontera = deque([start]) if estructura == FIFO else [start]
    visitados = set()

    while frontera:
        nodo = frontera.popleft() if estructura == FIFO else frontera.pop()
        if nodo in visitados:
            # Solo puede pasar en DFS: un nodo encolado dos veces se descarta.
            continue
        visitados.add(nodo)
        yield ("visita", nodo, len(frontera))

        if nodo == goal:
            yield ("fin", nodo, len(frontera))
            return

        for vecino in maze.neighbors(nodo):
            if vecino in visitados or vecino in came_from:
                continue
            came_from[vecino] = nodo
            frontera.append(vecino)


def _reconstruir_camino(came_from, goal):
    camino = []
    nodo = goal
    while nodo is not None:
        camino.append(nodo)
        nodo = came_from[nodo]
    camino.reverse()
    return camino


def solve(maze: Maze, algorithm: str, start=None, goal=None) -> SolveResult:
    """Ejecuta el algoritmo pedido sobre el laberinto y mide su desempeno."""
    algoritmo = (algorithm or "").strip().lower()
    if algoritmo not in ALGORITMOS:
        raise SolverError(
            f"Algoritmo desconocido {algorithm!r}. Opciones validas: {', '.join(ALGORITMOS)}."
        )

    origen = tuple(start) if start is not None else maze.start
    destino = tuple(goal) if goal is not None else maze.goal
    if not maze.is_open(origen):
        raise SolverError(f"El inicio {origen} no es una celda transitable.")
    if not maze.is_open(destino):
        raise SolverError(f"La meta {destino} no es una celda transitable.")

    estructura = FIFO if algoritmo == "bfs" else LIFO
    resultado = SolveResult(algorithm=algoritmo, solved=False)
    came_from = {origen: None}

    inicio_reloj = time.perf_counter()
    for tipo, nodo, tam_frontera in _buscar(maze, origen, destino, estructura, came_from):
        if tipo == "fin":
            resultado.solved = True
            break
        resultado.visits.append(nodo)
        resultado.frontiers.append(tam_frontera)
    resultado.elapsed_ms = (time.perf_counter() - inicio_reloj) * 1000.0
    resultado.expanded = len(resultado.visits)

    if resultado.solved:
        resultado.path = _reconstruir_camino(came_from, destino)

    return resultado


def bfs(maze: Maze, start=None, goal=None) -> SolveResult:
    return solve(maze, "bfs", start=start, goal=goal)


def dfs(maze: Maze, start=None, goal=None) -> SolveResult:
    return solve(maze, "dfs", start=start, goal=goal)


def comparar(maze: Maze) -> dict:
    """Ejecuta ambos algoritmos sobre el mismo laberinto y los contrasta."""
    resultados = {algoritmo: solve(maze, algoritmo) for algoritmo in ALGORITMOS}
    pasos_bfs = resultados["bfs"].path_length
    pasos_dfs = resultados["dfs"].path_length
    diferencia = None
    if pasos_bfs and pasos_dfs:
        diferencia = round((pasos_dfs - pasos_bfs) / pasos_bfs * 100.0, 1)
    return {
        "bfs": resultados["bfs"].to_dict(),
        "dfs": resultados["dfs"].to_dict(),
        "ventaja_bfs_pct": diferencia,
    }
