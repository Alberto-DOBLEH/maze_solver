"""Paquete del proyecto: laberintos y busqueda de rutas."""

from .generator import generate
from .grid import Maze, MazeError
from .solver import ALGORITMOS, SolverError, bfs, comparar, dfs, solve

__all__ = [
    "ALGORITMOS",
    "Maze",
    "MazeError",
    "SolverError",
    "bfs",
    "comparar",
    "dfs",
    "generate",
    "solve",
]
