/* =========================================================================
   Lógica de la interfaz: dibujo en canvas, edición del laberinto y animación
   de las búsquedas. Toda la parte algorítmica vive en el servidor (paquete
   `maze`); aquí solo se pide, se anima y se muestra.
   ========================================================================= */

(() => {
  "use strict";

  /* ------------------------------- constantes ------------------------------ */

  const COLOR = {
    fondo: "#0a0f19",
    muro: "#2b3852",
    muroBorde: "#33415f",
    inicio: "#22d3ee",
    meta: "#f472b6",
    camino: "#a3e635",
    bfs: [56, 189, 248],
    dfs: [251, 191, 36],
  };

  const ETIQUETA = { bfs: "BFS", dfs: "DFS" };
  const NOMBRE = {
    bfs: "BFS · búsqueda en anchura",
    dfs: "DFS · búsqueda en profundidad",
  };

  /* --------------------------------- estado -------------------------------- */

  const estado = {
    maze: null,
    algo: "bfs",
    comparar: false,
    resultados: { bfs: null, dfs: null },
    anim: {
      bfs: { visitas: 0, camino: 0 },
      dfs: { visitas: 0, camino: 0 },
    },
    raf: null,
    pintando: false,
    modoPincel: "dibujar",
    ultimaCelda: null,
    celdas: { board1: { w: 1, h: 1 }, board2: { w: 1, h: 1 } },
  };

  /* --------------------------------- DOM ----------------------------------- */

  const $ = (id) => document.getElementById(id);

  const els = {
    board1: $("board1"),
    board2: $("board2"),
    wrap1: $("wrap1"),
    wrap2: $("wrap2"),
    cap1: $("cap1"),
    cap2: $("cap2"),
    rows: $("rows"),
    cols: $("cols"),
    seed: $("seed"),
    btnSeed: $("btnSeed"),
    braid: $("braid"),
    braidLabel: $("braidLabel"),
    speed: $("speed"),
    status: $("status"),
    toast: $("toast"),
    metrics: $("metrics"),
    metricsBody: $("metricsBody"),
    fileInput: $("fileInput"),
    btnGenerate: $("btnGenerate"),
    btnClearWalls: $("btnClearWalls"),
    btnResetEnds: $("btnResetEnds"),
    btnDownload: $("btnDownload"),
    btnSolve: $("btnSolve"),
    btnCompare: $("btnCompare"),
    btnPng: $("btnPng"),
    algos: Array.from(document.querySelectorAll(".seg")),
  };

  /* ------------------------------ utilidades ------------------------------- */

  function aviso(texto, esError = false) {
    els.toast.textContent = texto;
    els.toast.classList.toggle("is-error", esError);
    els.toast.classList.add("is-visible");
    clearTimeout(aviso._t);
    aviso._t = setTimeout(() => els.toast.classList.remove("is-visible"), 3200);
  }

  function estadoTexto(texto) {
    els.status.textContent = texto;
  }

  async function pedir(url, cuerpo) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(cuerpo),
    });
    let datos = {};
    try {
      datos = await res.json();
    } catch (_) {
      /* respuesta sin JSON */
    }
    if (!res.ok) throw new Error(datos.error || `Error ${res.status} del servidor`);
    return datos;
  }

  function mazeToText(maze) {
    const lineas = [];
    for (let f = 0; f < maze.rows; f++) {
      let linea = "";
      for (let c = 0; c < maze.cols; c++) {
        const esInicio = maze.start[0] === f && maze.start[1] === c;
        const esMeta = maze.goal[0] === f && maze.goal[1] === c;
        linea += esInicio ? "S" : esMeta ? "G" : maze.walls[f][c] ? "#" : ".";
      }
      lineas.push(linea);
    }
    return lineas.join("\n");
  }

  function invalidarResultados() {
    estado.resultados = { bfs: null, dfs: null };
    estado.anim.bfs = { visitas: 0, camino: 0 };
    estado.anim.dfs = { visitas: 0, camino: 0 };
  }

  /* ------------------------------- dibujo ---------------------------------- */

  function clavesVisibles() {
    return estado.comparar ? ["bfs", "dfs"] : [estado.algo];
  }

  function dimensionar(canvas, claveLienzo) {
    const wrap = canvas.closest(".board-wrap");
    const anchoUtil = Math.max(140, (wrap ? wrap.clientWidth : 600) - 26);
    const altoUtil = Math.max(220, window.innerHeight * 0.66);
    const { rows, cols } = estado.maze;
    const celda = Math.max(
      3,
      Math.min(34, Math.floor(anchoUtil / cols), Math.floor(altoUtil / rows))
    );
    const w = celda * cols;
    const h = celda * rows;
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w;
      canvas.height = h;
    }
    canvas.style.width = w + "px";
    canvas.style.height = "auto";
    estado.celdas[claveLienzo] = { w: celda, h: celda };
    return celda;
  }

  /** Mezcla dos colores RGB. t=0 -> a, t=1 -> b */
  function mezclar(a, b, t) {
    const s = Math.max(0, Math.min(1, t));
    return `rgb(${Math.round(a[0] + (b[0] - a[0]) * s)},${Math.round(
      a[1] + (b[1] - a[1]) * s
    )},${Math.round(a[2] + (b[2] - a[2]) * s)})`;
  }

  function dibujarLienzo(canvas, claveLienzo, claveAlgo) {
    const maze = estado.maze;
    if (!maze) return;

    const ctx = canvas.getContext("2d");
    const celda = dimensionar(canvas, claveLienzo);
    const { rows, cols, walls, start, goal } = maze;
    const resultado = estado.resultados[claveAlgo];
    const anim = resultado ? estado.anim[claveAlgo] : null;
    const acento = COLOR[claveAlgo] || COLOR.bfs;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = COLOR.fondo;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // --- celdas exploradas: degradado según el orden de visita -------------
    if (resultado && anim) {
      const visitas = resultado.visits;
      const total = Math.max(1, visitas.length);
      const limite = Math.min(anim.visitas, visitas.length);
      const base = [13, 20, 33];
      // Un solo camino de relleno para no cambiar de color en cada celda.
      for (let i = 0; i < limite; i++) {
        const [f, c] = visitas[i];
        ctx.fillStyle = mezclar(base, acento, 0.3 + 0.62 * (i / total));
        ctx.fillRect(c * celda, f * celda, celda, celda);
      }
    }

    // --- muros -------------------------------------------------------------
    ctx.fillStyle = COLOR.muro;
    for (let f = 0; f < rows; f++) {
      const fila = walls[f];
      for (let c = 0; c < cols; c++) {
        if (fila[c]) ctx.fillRect(c * celda, f * celda, celda, celda);
      }
    }

    // --- retícula sutil ----------------------------------------------------
    if (celda >= 9) {
      ctx.strokeStyle = "rgba(51, 65, 95, 0.28)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      for (let c = 1; c < cols; c++) {
        ctx.moveTo(c * celda + 0.5, 0);
        ctx.lineTo(c * celda + 0.5, rows * celda);
      }
      for (let f = 1; f < rows; f++) {
        ctx.moveTo(0, f * celda + 0.5);
        ctx.lineTo(cols * celda, f * celda + 0.5);
      }
      ctx.stroke();
    }

    // --- camino encontrado -------------------------------------------------
    if (resultado && resultado.solved && anim && anim.camino > 0) {
      const camino = resultado.path.slice(0, anim.camino);
      if (camino.length > 1) {
        ctx.lineWidth = Math.max(2, celda * 0.34);
        ctx.lineCap = "round";
        ctx.lineJoin = "round";
        ctx.strokeStyle = COLOR.camino;
        ctx.shadowColor = "rgba(163, 230, 53, 0.55)";
        ctx.shadowBlur = Math.min(14, celda * 0.9);
        ctx.beginPath();
        camino.forEach(([f, c], i) => {
          const x = c * celda + celda / 2;
          const y = f * celda + celda / 2;
          if (i === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        });
        ctx.stroke();
        ctx.shadowBlur = 0;
      }
    }

    // --- inicio y meta -----------------------------------------------------
    const marcar = (celdaXY, color, letra) => {
      const [f, c] = celdaXY;
      const x = c * celda;
      const y = f * celda;
      ctx.fillStyle = color;
      ctx.fillRect(x, y, celda, celda);
      if (celda >= 13) {
        ctx.fillStyle = "#06121f";
        ctx.font = `700 ${Math.floor(celda * 0.62)}px "Segoe UI", system-ui, sans-serif`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(letra, x + celda / 2, y + celda / 2 + 0.5);
      }
    };
    marcar(start, COLOR.inicio, "S");
    marcar(goal, COLOR.meta, "G");
  }

  function dibujarTodo() {
    if (!estado.maze) return;
    const clave1 = estado.comparar ? "bfs" : estado.algo;
    dibujarLienzo(els.board1, "board1", clave1);
    if (estado.comparar) dibujarLienzo(els.board2, "board2", "dfs");
    actualizarCabeceras();
  }

  function actualizarCabeceras() {
    if (estado.comparar) {
      els.cap1.textContent = NOMBRE.bfs;
      els.cap2.textContent = NOMBRE.dfs;
    } else {
      els.cap1.textContent = NOMBRE[estado.algo];
    }
  }

  /* ------------------------------ animación -------------------------------- */

  function animar(claves) {
    cancelAnimationFrame(estado.raf);
    claves.forEach((k) => {
      estado.anim[k] = { visitas: 0, camino: 0 };
    });

    const paso = () => {
      const velocidad = Number(els.speed.value);
      let activa = false;

      claves.forEach((k) => {
        const r = estado.resultados[k];
        const a = estado.anim[k];
        if (!r) return;
        if (a.visitas < r.visits.length) {
          a.visitas = Math.min(r.visits.length, a.visitas + velocidad);
          activa = true;
        } else if (a.camino < r.path.length) {
          a.camino = Math.min(r.path.length, a.camino + Math.max(1, Math.ceil(velocidad / 2)));
          activa = true;
        }
      });

      dibujarTodo();

      if (activa) {
        estado.raf = requestAnimationFrame(paso);
      } else {
        estado.raf = null;
        finalizarAnimacion(claves);
      }
    };

    estado.raf = requestAnimationFrame(paso);
  }

  function finalizarAnimacion(claves) {
    const partes = claves.map((k) => {
      const r = estado.resultados[k];
      if (!r) return `${ETIQUETA[k]}: sin datos`;
      return `${ETIQUETA[k]}: ${r.solved ? r.path_length + " pasos" : "sin ruta"} · ${r.expanded} nodos`;
    });
    estadoTexto("Animación terminada — " + partes.join("  |  "));
  }

  /* ------------------------------- métricas -------------------------------- */

  function fmt(n) {
    return typeof n === "number" ? n.toLocaleString("es-MX") : n;
  }

  function renderMetricas() {
    const tbody = els.metricsBody;
    const thead = els.metrics.querySelector("thead");

    if (estado.comparar && estado.resultados.bfs && estado.resultados.dfs) {
      const b = estado.resultados.bfs;
      const d = estado.resultados.dfs;
      thead.innerHTML = `<tr><th>Métrica</th><th style="color:var(--bfs)">BFS</th><th style="color:var(--dfs)">DFS</th></tr>`;
      const fila = (nombre, a, c, clase = "") =>
        `<tr><td>${nombre}</td><td class="${clase}">${a}</td><td class="${clase}">${c}</td></tr>`;
      tbody.innerHTML = [
        fila("¿Encuentra ruta?", b.solved ? "Sí" : "No", d.solved ? "Sí" : "No"),
        fila("Nodos expandidos", fmt(b.expanded), fmt(d.expanded)),
        fila("Longitud del camino", fmt(b.path_length), fmt(d.path_length)),
        fila("Frontera máxima", fmt(b.max_frontier), fmt(d.max_frontier)),
        fila("Tiempo (ms)", fmt(b.elapsed_ms), fmt(d.elapsed_ms)),
      ].join("");
      return;
    }

    thead.innerHTML = `<tr><th>Métrica</th><th>Valor</th></tr>`;
    const r = estado.resultados[estado.algo];
    if (!r) {
      tbody.innerHTML = `<tr><td colspan="2" class="empty">Sin ejecuciones todavía.</td></tr>`;
      return;
    }
    const si = r.solved
      ? `<span class="good">Sí</span>`
      : `<span class="bad">No</span>`;
    tbody.innerHTML = [
      `<tr><td>Algoritmo</td><td>${ETIQUETA[r.algorithm]}</td></tr>`,
      `<tr><td>¿Encuentra ruta?</td><td>${si}</td></tr>`,
      `<tr><td>Nodos expandidos</td><td>${fmt(r.expanded)}</td></tr>`,
      `<tr><td>Longitud del camino</td><td>${fmt(r.path_length)} pasos</td></tr>`,
      `<tr><td>Frontera máxima</td><td>${fmt(r.max_frontier)}</td></tr>`,
      `<tr><td>Tiempo de cómputo</td><td>${fmt(r.elapsed_ms)} ms</td></tr>`,
    ].join("");
  }

  /* --------------------------- acciones principales ------------------------ */

  async function generar() {
    estadoTexto("Generando laberinto…");
    try {
      const filas = Number(els.rows.value);
      const columnas = Number(els.cols.value);
      const datos = await pedir("/api/generate", {
        rows: filas,
        cols: columnas,
        seed: Number(els.seed.value),
        braid: Number(els.braid.value) / 100,
      });
      aplicarLaberinto(datos.maze);
      invalidarResultados();
      renderMetricas();
      dibujarTodo();
      estadoTexto(
        `Laberinto ${datos.maze.rows}×${datos.maze.cols} · semilla ${els.seed.value}`
      );
      aviso("Laberinto generado");
    } catch (error) {
      estadoTexto("Error");
      aviso(error.message, true);
    }
  }

  function aplicarLaberinto(maze) {
    estado.maze = maze;
    els.rows.value = maze.rows;
    els.cols.value = maze.cols;
  }

  /** Elige una semilla al azar (1 - 999 999) y regenera el laberinto. */
  function semillaAleatoria() {
    els.seed.value = 1 + Math.floor(Math.random() * 999999);
    const boton = els.btnSeed;
    boton.classList.remove("girando");
    void boton.offsetWidth; // reinicia la animación
    boton.classList.add("girando");
    generar();
  }

  async function resolver() {
    if (!estado.maze) return;
    estadoTexto(`Ejecutando ${ETIQUETA[estado.algo]}…`);
    try {
      const datos = await pedir("/api/solve", {
        maze: estado.maze,
        algorithm: estado.algo,
      });
      estado.comparar = false;
      els.wrap2.classList.add("is-hidden");
      estado.resultados[estado.algo] = datos.result;
      renderMetricas();
      if (!datos.result.solved) {
        dibujarTodo();
        aviso("No existe ruta entre el inicio y la meta con este laberinto", true);
        estadoTexto("Sin ruta posible");
        return;
      }
      animar([estado.algo]);
    } catch (error) {
      estadoTexto("Error");
      aviso(error.message, true);
    }
  }

  async function comparar() {
    if (!estado.maze) return;
    estadoTexto("Ejecutando BFS y DFS…");
    try {
      const datos = await pedir("/api/compare", { maze: estado.maze });
      estado.resultados = { bfs: datos.results.bfs, dfs: datos.results.dfs };
      estado.comparar = true;
      els.wrap2.classList.remove("is-hidden");
      dibujarTodo();
      renderMetricas();
      animar(["bfs", "dfs"]);
    } catch (error) {
      estadoTexto("Error");
      aviso(error.message, true);
    }
  }

  /* ------------------------- edición sobre el lienzo ---------------------- */

  function celdaDesdeEvento(canvas, clave, evento) {
    const rect = canvas.getBoundingClientRect();
    const { w, h } = estado.celdas[clave];
    const x = (evento.clientX - rect.left) / (rect.width || 1);
    const y = (evento.clientY - rect.top) / (rect.height || 1);
    const col = Math.floor((x * canvas.width) / w);
    const fila = Math.floor((y * canvas.height) / h);
    if (fila < 0 || col < 0 || fila >= estado.maze.rows || col >= estado.maze.cols) {
      return null;
    }
    return [fila, col];
  }

  const mismaCelda = (a, b) => a && b && a[0] === b[0] && a[1] === b[1];

  function aplicarPincel(celda, modo) {
    const maze = estado.maze;
    const [f, c] = celda;
    const esInicio = mismaCelda(celda, maze.start);
    const esMeta = mismaCelda(celda, maze.goal);
    if (esInicio || esMeta) return false;
    const valorDeseado = modo === "borrar" ? 0 : 1;
    if (maze.walls[f][c] === valorDeseado) return false;
    maze.walls[f][c] = valorDeseado;
    return true;
  }

  function conectarEdicion(canvas, clave) {
    canvas.addEventListener("pointerdown", (evento) => {
      if (!estado.maze) return;
      const celda = celdaDesdeEvento(canvas, clave, evento);
      if (!celda) return;

      // Alt+clic define el inicio, Ctrl(clic) define la meta.
      if (evento.altKey || evento.ctrlKey || evento.metaKey) {
        const objetivo = evento.altKey ? "start" : "goal";
        const [f, c] = celda;
        if (estado.maze.walls[f][c]) {
          aviso("No puedes colocar el punto sobre un muro", true);
          return;
        }
        if (mismaCelda(celda, estado.maze[objetivo === "start" ? "goal" : "start"])) {
          aviso("El inicio y la meta deben ser celdas distintas", true);
          return;
        }
        estado.maze[objetivo] = [f, c];
      } else {
        const esMuro = estado.maze.walls[celda[0]][celda[1]] === 1;
        estado.modoPincel = evento.shiftKey || esMuro ? "borrar" : "dibujar";
        aplicarPincel(celda, estado.modoPincel);
      }

      invalidarResultados();
      renderMetricas();
      dibujarTodo();
      estadoTexto("Laberinto editado · resultados reiniciados");
      estado.pintando = true;
      estado.ultimaCelda = celda;
      canvas.setPointerCapture(evento.pointerId);
    });

    canvas.addEventListener("pointermove", (evento) => {
      if (!estado.pintando || !estado.maze) return;
      const celda = celdaDesdeEvento(canvas, clave, evento);
      if (!celda || mismaCelda(celda, estado.ultimaCelda)) return;
      if (aplicarPincel(celda, estado.modoPincel)) {
        dibujarTodo();
      }
      estado.ultimaCelda = celda;
    });

    const soltar = () => {
      estado.pintando = false;
      estado.ultimaCelda = null;
    };
    canvas.addEventListener("pointerup", soltar);
    canvas.addEventListener("pointercancel", soltar);
    canvas.addEventListener("pointerleave", soltar);
    canvas.addEventListener("contextmenu", (e) => e.preventDefault());
  }

  /* ------------------------------- capturas -------------------------------- */

  function captura() {
    const clave1 = estado.comparar ? "bfs" : estado.algo;
    const lienzos = [{ canvas: els.board1, etiqueta: NOMBRE[clave1] }];
    if (estado.comparar) lienzos.push({ canvas: els.board2, etiqueta: NOMBRE.dfs });

    const margen = 28;
    const separacion = 26;
    const altoTitulo = 76;
    const anchoTotal =
      lienzos.reduce((suma, l) => suma + l.canvas.width, 0) +
      separacion * (lienzos.length - 1) +
      margen * 2;
    const altoTotal =
      Math.max(...lienzos.map((l) => l.canvas.height)) + margen * 2 + altoTitulo + 34;

    const salida = document.createElement("canvas");
    salida.width = anchoTotal;
    salida.height = altoTotal;
    const ctx = salida.getContext("2d");

    ctx.fillStyle = "#0b0f1a";
    ctx.fillRect(0, 0, anchoTotal, altoTotal);

    ctx.fillStyle = "#e8edf7";
    ctx.font = '700 22px "Segoe UI", system-ui, sans-serif';
    ctx.textAlign = "left";
    ctx.textBaseline = "alphabetic";
    ctx.fillText("Rutas en laberintos · BFS vs DFS", margen, margen + 22);

    ctx.fillStyle = "#8b98b2";
    ctx.font = '400 13px "Segoe UI", system-ui, sans-serif';
    const detalles = lienzos
      .map((l) => {
        const clave = l.canvas === els.board2 ? "dfs" : clave1;
        const r = estado.resultados[clave];
        return r
          ? `${ETIQUETA[clave]}: ${r.solved ? r.path_length + " pasos" : "sin ruta"}, ${r.expanded} nodos, ${r.elapsed_ms} ms`
          : `${ETIQUETA[clave]}: sin ejecutar`;
      })
      .join("   ·   ");
    ctx.fillText(detalles, margen, margen + 48);

    let x = margen;
    const y = margen + altoTitulo;
    lienzos.forEach((l) => {
      ctx.drawImage(l.canvas, x, y);
      x += l.canvas.width + separacion;
    });

    ctx.fillStyle = "#8b98b2";
    ctx.font = '400 12px "Segoe UI", system-ui, sans-serif';
    ctx.fillText(
      `Inicio S · Meta G · Muro oscuro · Celdas exploradas y camino en verde`,
      margen,
      altoTotal - 16
    );

    const enlace = document.createElement("a");
    enlace.download = `laberinto-${estado.comparar ? "comparacion" : estado.algo}.png`;
    enlace.href = salida.toDataURL("image/png");
    enlace.click();
    aviso("Captura guardada");
  }

  /* ------------------------------ archivos -------------------------------- */

  function descargarTexto() {
    if (!estado.maze) return;
    const texto = mazeToText(estado.maze);
    const blob = new Blob([texto + "\n"], { type: "text/plain;charset=utf-8" });
    const enlace = document.createElement("a");
    enlace.href = URL.createObjectURL(blob);
    enlace.download = "laberinto.txt";
    enlace.click();
    URL.revokeObjectURL(enlace.href);
    aviso("Archivo .txt guardado");
  }

  async function cargarArchivo(archivo) {
    if (!archivo) return;
    try {
      const texto = await archivo.text();
      const datos = await pedir("/api/parse", { text: texto });
      aplicarLaberinto(datos.maze);
      invalidarResultados();
      renderMetricas();
      dibujarTodo();
      estadoTexto(`Archivo cargado: ${archivo.name}`);
      aviso("Laberinto cargado desde archivo");
    } catch (error) {
      aviso(error.message, true);
    } finally {
      els.fileInput.value = "";
    }
  }

  /* ------------------------------ eventos UI ------------------------------- */

  function seleccionarAlgoritmo(algo) {
    estado.algo = algo;
    els.algos.forEach((boton) => {
      const activo = boton.dataset.algo === algo;
      boton.classList.toggle("is-active", activo);
      boton.setAttribute("aria-checked", String(activo));
    });
    salirComparacion();
    dibujarTodo();
    renderMetricas();
  }

  function salirComparacion() {
    if (estado.comparar) {
      estado.comparar = false;
      els.wrap2.classList.add("is-hidden");
    }
  }

  function conectarUI() {
    els.algos.forEach((boton) =>
      boton.addEventListener("click", () => seleccionarAlgoritmo(boton.dataset.algo))
    );

    els.btnGenerate.addEventListener("click", generar);
    els.btnSeed.addEventListener("click", semillaAleatoria);
    els.seed.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        generar();
      }
    });
    els.btnSolve.addEventListener("click", resolver);
    els.btnCompare.addEventListener("click", comparar);
    els.btnPng.addEventListener("click", captura);
    els.btnDownload.addEventListener("click", descargarTexto);

    els.braid.addEventListener("input", () => {
      els.braidLabel.textContent = `${els.braid.value} %`;
    });

    els.btnClearWalls.addEventListener("click", () => {
      if (!estado.maze) return;
      estado.maze.walls = estado.maze.walls.map((fila) => fila.map(() => 0));
      invalidarResultados();
      renderMetricas();
      dibujarTodo();
      aviso("Muros eliminados");
    });

    els.btnResetEnds.addEventListener("click", () => {
      if (!estado.maze) return;
      const { rows, cols } = estado.maze;
      estado.maze.start = [1, 1];
      estado.maze.goal = [rows - 2, cols - 2];
      estado.maze.walls[1][1] = 0;
      estado.maze.walls[rows - 2][cols - 2] = 0;
      invalidarResultados();
      renderMetricas();
      dibujarTodo();
    });

    els.fileInput.addEventListener("change", (e) => cargarArchivo(e.target.files[0]));

    document.addEventListener("keydown", (e) => {
      if (e.target.matches("input")) return;
      const tecla = e.key.toLowerCase();
      if (tecla === "g") generar();
      if (tecla === "n") semillaAleatoria();
      if (tecla === "r") resolver();
      if (tecla === "c") comparar();
      if (tecla === "b") seleccionarAlgoritmo("bfs");
      if (tecla === "d") seleccionarAlgoritmo("dfs");
    });

    conectarEdicion(els.board1, "board1");
    conectarEdicion(els.board2, "board2");

    const observador = new ResizeObserver(() => dibujarTodo());
    observador.observe(els.wrap1);
    observador.observe(els.wrap2);
  }

  /* --------------------------------- arranque ------------------------------ */

  async function iniciar() {
    conectarUI();
    els.braidLabel.textContent = `${els.braid.value} %`;
    try {
      const datos = await pedir("/api/generate", {
        rows: Number(els.rows.value),
        cols: Number(els.cols.value),
        seed: Number(els.seed.value),
        braid: 0,
      });
      aplicarLaberinto(datos.maze);
      invalidarResultados();
      dibujarTodo();
      renderMetricas();
      estadoTexto(`Laberinto ${datos.maze.rows}×${datos.maze.cols} listo`);
    } catch (error) {
      estadoTexto("Sin conexión con el servidor");
      aviso(error.message, true);
    }
  }

  document.addEventListener("DOMContentLoaded", iniciar);
})();
