"""Generador de laberintos.

Algoritmo: *backtracking recursivo* (tambien llamado DFS aleatorizado).
Se parte de una rejilla completamente llena de muros y se excava un arbol
de expansion: desde la celda actual se elige un vecino a distancia 2, se
derriba el muro intermedio y se continua. Cuando no quedan vecinos sin
visitar se retrocede en la pila.

El resultado es un *laberinto perfecto*: existe exactamente un camino entre
cualquier par de celdas y no hay ciclos. Eso lo vuelve ideal para comparar
BFS contra DFS, porque DFS puede encontrar un camino muy largo mientras que
BFS siempre encuentra el mas corto.

El parametro ``braid`` permite romper la propiedad de laberinto perfecto
abriendo algunos muros, generando ciclos y multiples rutas validas.
"""

from __future__ import annotations

import random

from .grid import OPEN, WALL, Maze

#: Dimension minima razonable para que quepan muros, pasillos e inicio/meta.
MIN_DIM = 5


def _dimension_impar(valor, nombre):
    if not isinstance(valor, int) or isinstance(valor, bool):
        raise ValueError(f"'{nombre}' debe ser un numero entero.")
    if valor < MIN_DIM:
        raise ValueError(f"'{nombre}' debe ser al menos {MIN_DIM}.")
    # Se fuerza a impar para que el borde quede cerrado y el interior
    # tenga celdas de pasillo en indices impares.
    return valor if valor % 2 == 1 else valor - 1


def generate(rows=21, cols=21, seed=None, braid=0.0):
    """Devuelve un :class:`Maze` aleatorio reproducible.

    rows, cols: dimensiones (se ajustan al impar inferior si son pares).
    seed:       semilla; con la misma semilla se obtiene el mismo laberinto.
    braid:      fraccion 0..1 de callejones sin salida que se abren.
    """
    rows = _dimension_impar(rows, "rows")
    cols = _dimension_impar(cols, "cols")
    if not 0.0 <= braid <= 1.0:
        raise ValueError("'braid' debe estar entre 0 y 1.")

    rng = random.Random(seed)
    walls = [[WALL] * cols for _ in range(rows)]

    origen = (1, 1)
    walls[origen[0]][origen[1]] = OPEN
    pila = [origen]

    while pila:
        fila, col = pila[-1]
        candidatos = []
        for dfila, dcol in ((-2, 0), (0, 2), (2, 0), (0, -2)):
            nfila, ncol = fila + dfila, col + dcol
            if 0 < nfila < rows - 1 and 0 < ncol < cols - 1 and walls[nfila][ncol] == WALL:
                candidatos.append((nfila, ncol, dfila, dcol))

        if not candidatos:
            pila.pop()
            continue

        nfila, ncol, dfila, dcol = rng.choice(candidatos)
        walls[fila + dfila // 2][col + dcol // 2] = OPEN
        walls[nfila][ncol] = OPEN
        pila.append((nfila, ncol))

    if braid > 0:
        _abrir_callejones(walls, rows, cols, braid, rng)

    return Maze(walls=walls, start=origen, goal=(rows - 2, cols - 2))


def _abrir_callejones(walls, rows, cols, braid, rng):
    """Derriba muros adyacentes a callejones sin salida.

    Un callejon sin salida es una celda de pasillo con tres muros alrededor.
    Al abrir uno de esos muros se crea un atajo y el laberinto deja de ser
    un arbol puro: aparecen rutas alternativas.
    """
    callejones = []
    for fila in range(1, rows - 1):
        for col in range(1, cols - 1):
            if walls[fila][col] != OPEN:
                continue
            muros = 0
            for dfila, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                if walls[fila + dfila][col + dcol] == WALL:
                    muros += 1
            if muros == 3:
                callejones.append((fila, col))

    rng.shuffle(callejones)
    cuantos = int(len(callejones) * braid)
    for fila, col in callejones[:cuantos]:
        opciones = []
        for dfila, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nfila, ncol = fila + dfila, col + dcol
            if 1 <= nfila < rows - 1 and 1 <= ncol < cols - 1 and walls[nfila][ncol] == WALL:
                opciones.append((nfila, ncol))
        if opciones:
            nfila, ncol = rng.choice(opciones)
            walls[nfila][ncol] = OPEN
