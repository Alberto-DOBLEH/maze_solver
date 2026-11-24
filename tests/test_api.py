"""Pruebas de la API HTTP con el cliente de pruebas de Flask."""

import pytest

from app import app


@pytest.fixture()
def cliente():
    app.config.update(TESTING=True)
    with app.test_client() as cliente:
        yield cliente


def test_index_responde_html(cliente):
    respuesta = cliente.get("/")
    assert respuesta.status_code == 200
    assert "BFS" in respuesta.get_data(as_text=True)


def test_salud(cliente):
    datos = cliente.get("/api/salud").get_json()
    assert datos["estado"] == "ok"
    assert datos["algoritmos"] == ["bfs", "dfs"]


def test_generar(cliente):
    respuesta = cliente.post("/api/generate", json={"rows": 15, "cols": 15, "seed": 4})
    assert respuesta.status_code == 200
    datos = respuesta.get_json()
    assert datos["maze"]["rows"] == 15
    assert "#" in datos["text"]


def test_generar_reproducible(cliente):
    a = cliente.post("/api/generate", json={"rows": 15, "cols": 15, "seed": 4}).get_json()
    b = cliente.post("/api/generate", json={"rows": 15, "cols": 15, "seed": 4}).get_json()
    assert a["maze"] == b["maze"]


def test_generar_parametros_invalidos(cliente):
    respuesta = cliente.post("/api/generate", json={"rows": "muchas", "cols": 15})
    assert respuesta.status_code == 400
    assert "error" in respuesta.get_json()


def test_generar_demasiado_grande(cliente):
    respuesta = cliente.post("/api/generate", json={"rows": 401, "cols": 401})
    assert respuesta.status_code == 400


def test_resolver_bfs_y_dfs(cliente):
    maze = cliente.post("/api/generate", json={"rows": 21, "cols": 21, "seed": 8}).get_json()["maze"]
    for algoritmo in ("bfs", "dfs"):
        datos = cliente.post(
            "/api/solve", json={"maze": maze, "algorithm": algoritmo}
        ).get_json()
        assert datos["result"]["algorithm"] == algoritmo
        assert datos["result"]["solved"] is True
        assert datos["result"]["path_length"] > 0


def test_comparar(cliente):
    maze = cliente.post("/api/generate", json={"rows": 21, "cols": 21, "seed": 8}).get_json()["maze"]
    datos = cliente.post("/api/compare", json={"maze": maze}).get_json()
    assert datos["results"]["bfs"]["path_length"] <= datos["results"]["dfs"]["path_length"]


def test_algoritmo_invalido(cliente):
    texto = "#####\n#S..#\n#..G#\n#####"
    respuesta = cliente.post("/api/solve", json={"text": texto, "algorithm": "dijkstra"})
    assert respuesta.status_code == 400
    assert "desconocido" in respuesta.get_json()["error"].lower()


def test_parsear_texto(cliente):
    texto = "#####\n#S..#\n#..G#\n#####"
    datos = cliente.post("/api/parse", json={"text": texto}).get_json()
    assert datos["maze"]["start"] == [1, 1]
    assert datos["maze"]["goal"] == [2, 3]


def test_texto_invalido(cliente):
    respuesta = cliente.post("/api/parse", json={"text": "sin inicio ni meta"})
    assert respuesta.status_code == 400


def test_sin_cuerpo(cliente):
    respuesta = cliente.post("/api/solve", json=None)
    assert respuesta.status_code == 400


def test_ruta_inexistente(cliente):
    assert cliente.get("/api/no-existe").status_code == 404
