"""Modelo del laberinto.

El laberinto se representa como una rejilla de celdas, donde cada celda es
un muro o un pasillo. Las coordenadas se manejan como tuplas ``(fila, columna)``
con origen en la esquina superior izquierda.

Notacion de texto usada para guardar y cargar laberintos (archivos .txt):

    #   muro
    .   pasillo (tambien se acepta espacio)
    S   inicio
    G   meta (o E, de "end")
"""

from __future__ import annotations

WALL = 1
OPEN = 0

#: Movimientos permitidos: arriba, derecha, abajo, izquierda.
MOVIMIENTOS = ((-1, 0), (0, 1), (1, 0), (0, -1))

SYMBOL_WALL = "#"
SYMBOL_OPEN = "."
SYMBOL_START = "S"
SYMBOL_GOAL = "G"


class MazeError(ValueError):
    """El laberinto recibido no es valido."""


class Maze:
    """Rejilla navegable con punto de inicio y meta."""

    def __init__(self, walls, start, goal):
        if not walls or not walls[0]:
            raise MazeError("El laberinto esta vacio.")
        self.walls = [[1 if valor else 0 for valor in fila] for fila in walls]
        self.rows = len(self.walls)
        self.cols = len(self.walls[0])
        if any(len(fila) != self.cols for fila in self.walls):
            raise MazeError("Todas las filas deben tener la misma longitud.")
        self.start = self._validar_celda(start, "inicio")
        self.goal = self._validar_celda(goal, "meta")
        if self.start == self.goal:
            raise MazeError("El inicio y la meta no pueden ser la misma celda.")

    # ------------------------------------------------------------------ basicos

    def _validar_celda(self, celda, nombre):
        try:
            fila, col = celda
        except (TypeError, ValueError):
            raise MazeError(f"La {nombre} debe ser una pareja (fila, columna).")
        if not self.in_bounds((fila, col)):
            raise MazeError(f"La {nombre} {celda} esta fuera del laberinto.")
        if self.is_wall((fila, col)):
            raise MazeError(f"La {nombre} {celda} cae sobre un muro.")
        return (fila, col)

    def in_bounds(self, nodo):
        fila, col = nodo
        return 0 <= fila < self.rows and 0 <= col < self.cols

    def is_wall(self, nodo):
        fila, col = nodo
        return self.walls[fila][col] == WALL

    def is_open(self, nodo):
        return self.in_bounds(nodo) and not self.is_wall(nodo)

    def neighbors(self, nodo):
        """Vecinos transitables en orden fijo (arriba, derecha, abajo, izquierda).

        El orden es determinista a proposito: hace que BFS y DFS produzcan
        siempre el mismo resultado para el mismo laberinto, algo necesario
        para poder comparar y para que las pruebas no sean fragiles.
        """
        fila, col = nodo
        vecinos = []
        for dfila, dcol in MOVIMIENTOS:
            candidato = (fila + dfila, col + dcol)
            if self.is_open(candidato):
                vecinos.append(candidato)
        return vecinos

    def toggle_wall(self, nodo):
        fila, col = nodo
        if not self.in_bounds(nodo):
            raise MazeError(f"La celda {nodo} esta fuera del laberinto.")
        self.walls[fila][col] = OPEN if self.walls[fila][col] == WALL else WALL

    # ------------------------------------------------------- (de)serializacion

    def to_dict(self):
        return {
            "rows": self.rows,
            "cols": self.cols,
            "walls": self.walls,
            "start": list(self.start),
            "goal": list(self.goal),
        }

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise MazeError("Se esperaba un objeto JSON con el laberinto.")
        try:
            walls = data["walls"]
            start = data["start"]
            goal = data["goal"]
        except KeyError as exc:
            raise MazeError(f"Falta el campo obligatorio {exc} en el laberinto.")
        if not isinstance(walls, list) or not all(isinstance(f, list) for f in walls):
            raise MazeError("'walls' debe ser una lista de listas.")
        if len(start) != 2 or len(goal) != 2:
            raise MazeError("'start' y 'goal' deben ser pares (fila, columna).")
        return cls(
            walls=walls,
            start=(int(start[0]), int(start[1])),
            goal=(int(goal[0]), int(goal[1])),
        )

    def to_text(self):
        lineas = []
        for fila in range(self.rows):
            caracteres = []
            for col in range(self.cols):
                nodo = (fila, col)
                if nodo == self.start:
                    caracteres.append(SYMBOL_START)
                elif nodo == self.goal:
                    caracteres.append(SYMBOL_GOAL)
                elif self.is_wall(nodo):
                    caracteres.append(SYMBOL_WALL)
                else:
                    caracteres.append(SYMBOL_OPEN)
            lineas.append("".join(caracteres))
        return "\n".join(lineas)

    @classmethod
    def from_text(cls, text):
        if not isinstance(text, str) or not text.strip():
            raise MazeError("El archivo de laberinto esta vacio.")

        lineas = [linea.rstrip("\n") for linea in text.splitlines()]
        # Se descartan lineas totalmente vacias al inicio y al final,
        # pero se conservan los espacios internos, que son pasillos validos.
        while lineas and not lineas[0].strip():
            lineas.pop(0)
        while lineas and not lineas[-1].strip():
            lineas.pop()
        if not lineas:
            raise MazeError("El archivo de laberinto esta vacio.")

        start = goal = None
        walls = []
        for indice_fila, linea in enumerate(lineas):
            fila = []
            for indice_col, caracter in enumerate(linea):
                if caracter == SYMBOL_WALL:
                    fila.append(WALL)
                elif caracter in (SYMBOL_OPEN, " "):
                    fila.append(OPEN)
                elif caracter in (SYMBOL_START, "s"):
                    fila.append(OPEN)
                    start = (indice_fila, indice_col)
                elif caracter in (SYMBOL_GOAL, "E", "e"):
                    fila.append(OPEN)
                    goal = (indice_fila, indice_col)
                else:
                    raise MazeError(
                        f"Caracter no reconocido {caracter!r} en la fila "
                        f"{indice_fila + 1}, columna {indice_col + 1}."
                    )
            walls.append(fila)

        if start is None:
            raise MazeError("El laberinto no tiene inicio (falta la 'S').")
        if goal is None:
            raise MazeError("El laberinto no tiene meta (falta la 'G').")
        return cls(walls=walls, start=start, goal=goal)

    def __eq__(self, otro):
        if not isinstance(otro, Maze):
            return NotImplemented
        return (
            self.walls == otro.walls
            and self.start == otro.start
            and self.goal == otro.goal
        )

    def __repr__(self):
        return f"Maze(rows={self.rows}, cols={self.cols}, start={self.start}, goal={self.goal})"
