"""Pruebas del generador de laberintos."""

from collections import deque

import pytest

from maze import generate


def recorrer(maze):
    """Celdas de pasillo alcanzables desde el inicio (BFS de referencia)."""
    vistos = {maze.start}
    cola = deque([maze.start])
    while cola:
        nodo = cola.popleft()
        for vecino in maze.neighbors(nodo):
            if vecino not in vistos:
                vistos.add(vecino)
                cola.append(vecino)
    return vistos


def test_dimensiones_impares():
    assert generate(rows=20, cols=30, seed=1).rows == 19
    assert generate(rows=20, cols=30, seed=1).cols == 29


def test_dimensiones_minimas():
    with pytest.raises(ValueError):
        generate(rows=3, cols=3)


def test_misma_semilla_mismo_laberinto():
    a = generate(rows=21, cols=21, seed=42)
    b = generate(rows=21, cols=21, seed=42)
    assert a == b


def test_semillas_distintas_laberintos_distintos():
    a = generate(rows=21, cols=21, seed=1)
    b = generate(rows=21, cols=21, seed=2)
    assert a.walls != b.walls


def test_todo_el_pasillo_es_alcanzable():
    maze = generate(rows=31, cols=41, seed=7)
    pasillos = {
        (f, c)
        for f in range(maze.rows)
        for c in range(maze.cols)
        if maze.is_open((f, c))
    }
    assert recorrer(maze) == pasillos


def test_inicio_y_meta_transitables():
    maze = generate(rows=21, cols=21, seed=3)
    assert maze.is_open(maze.start)
    assert maze.is_open(maze.goal)
    assert maze.start == (1, 1)
    assert maze.goal == (19, 19)


def test_borde_cerrado():
    maze = generate(rows=15, cols=15, seed=9)
    borde = [
        maze.walls[0][c] for c in range(maze.cols)
    ] + [
        maze.walls[maze.rows - 1][c] for c in range(maze.cols)
    ]
    assert all(borde)


def test_atajos_crean_ciclos():
    """Con braid=1 el laberinto deja de ser un arbol (hay rutas alternativas)."""
    perfecto = generate(rows=31, cols=31, seed=5)
    abierto = generate(rows=31, cols=31, seed=5, braid=1.0)
    pasillos_abiertos = sum(
        abierto.is_open((f, c)) for f in range(abierto.rows) for c in range(abierto.cols)
    )
    pasillos_perfectos = sum(
        perfecto.is_open((f, c))
        for f in range(perfecto.rows)
        for c in range(perfecto.cols)
    )
    assert pasillos_abiertos > pasillos_perfectos


def test_braid_fuera_de_rango():
    with pytest.raises(ValueError):
        generate(rows=11, cols=11, braid=1.5)
