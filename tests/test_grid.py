"""Pruebas del modelo de laberinto (lectura, escritura y vecinos)."""

import pytest

from maze import Maze, MazeError


LABERINTO = """\
#####
#S..#
#.#.#
#..G#
#####
"""


def test_parsear_texto_basico():
    maze = Maze.from_text(LABERINTO)
    assert maze.rows == 5
    assert maze.cols == 5
    assert maze.start == (1, 1)
    assert maze.goal == (3, 3)
    assert maze.is_open((1, 2))
    assert maze.is_wall((2, 2))


def test_ida_y_vuelta_de_texto():
    maze = Maze.from_text(LABERINTO)
    assert Maze.from_text(maze.to_text()) == maze


def test_acepta_espacios_como_pasillo():
    texto = "#####\n#S  #\n# # #\n#  G#\n#####"
    maze = Maze.from_text(texto)
    assert maze.is_open((1, 2))


def test_vecinos_en_orden_fijo():
    maze = Maze.from_text(LABERINTO)
    assert maze.neighbors((1, 1)) == [(1, 2), (2, 1)]


def test_no_sale_del_tablero():
    maze = Maze.from_text(LABERINTO)
    assert maze.neighbors((0, 0)) == []


@pytest.mark.parametrize(
    "texto, mensaje",
    [
        ("", "vacio"),
        ("#####\n#...#\n#####", "inicio"),
        ("#####\n#S..#\n#####", "meta"),
        ("#####\n#S.X#\n#####", "no reconocido"),
    ],
)
def test_textos_invalidos(texto, mensaje):
    with pytest.raises(MazeError) as error:
        Maze.from_text(texto)
    assert mensaje in str(error.value).lower()


def test_inicio_sobre_muro_es_error():
    with pytest.raises(MazeError):
        Maze(walls=[[1, 1], [1, 0]], start=(0, 0), goal=(1, 1))


def test_inicio_igual_a_meta_es_error():
    with pytest.raises(MazeError):
        Maze(walls=[[0, 0], [0, 0]], start=(0, 0), goal=(0, 0))


def test_dict_ida_y_vuelta():
    maze = Maze.from_text(LABERINTO)
    copia = Maze.from_dict(maze.to_dict())
    assert copia == maze


def test_dict_incompleto():
    with pytest.raises(MazeError):
        Maze.from_dict({"walls": [[0]], "start": [0, 0]})


def test_alternar_muro():
    maze = Maze.from_text(LABERINTO)
    assert maze.is_wall((2, 2))
    maze.toggle_wall((2, 2))
    assert maze.is_open((2, 2))
