"""Paquete del proyecto: laberintos y busqueda de rutas."""

from .generator import generate
from .grid import Maze, MazeError

__all__ = ["Maze", "MazeError", "generate"]
