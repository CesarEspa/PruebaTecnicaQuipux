// Dashboard simple: solo HTML/CSS/JS, sin frameworks. Habla con la misma API
// de FastAPI (mismo origen, por eso no hace falta configurar CORS).

const sismosState = { page: 1, pageSize: 20, totalPages: 1 };
const reportesState = { page: 1, pageSize: 20, totalPages: 1 };

let distribucionChart = null;
let porHoraChart = null;
let mapa = null;
let marcadores = null;

// ---------- utilidades ----------

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Error ${response.status} pidiendo ${url}`);
  return response.json();
}

function formatearFecha(iso) {
  const fecha = new Date(iso);
  return fecha.toLocaleString("es", { dateStyle: "short", timeStyle: "short" });
}

function mostrarToast(mensaje) {
  const toast = document.getElementById("toast");
  toast.textContent = mensaje;
  toast.classList.add("visible");
  setTimeout(() => toast.classList.remove("visible"), 3500);
}

// ---------- pestañas ----------

function inicializarTabs() {
  const botones = document.querySelectorAll(".tab-btn");
  botones.forEach((boton) => {
    boton.addEventListener("click", () => {
      botones.forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));

      boton.classList.add("active");
      document.getElementById(`tab-${boton.dataset.tab}`).classList.add("active");

      if (boton.dataset.tab === "mapa") {
        // Leaflet necesita saber el tamaño real del contenedor una vez que es visible.
        setTimeout(() => mapa && mapa.invalidateSize(), 50);
      }
    });
  });
}

// ---------- sismos ----------

async function cargarSismos() {
  const magnitud = document.getElementById("filtro-magnitud").value;
  const lugar = document.getElementById("filtro-lugar").value;

  const params = new URLSearchParams({
    page: sismosState.page,
    page_size: sismosState.pageSize,
  });
  if (magnitud) params.set("min_magnitude", magnitud);
  if (lugar) params.set("location", lugar);

  const data = await fetchJson(`/earthquakes?${params.toString()}`);
  sismosState.totalPages = Math.max(1, Math.ceil(data.total / data.page_size));

  const tbody = document.getElementById("tabla-sismos");
  tbody.innerHTML = "";
  data.items.forEach((sismo) => tbody.appendChild(filaSismo(sismo)));

  document.getElementById("sismos-pagina").textContent = `Página ${sismosState.page} de ${sismosState.totalPages}`;
  document.getElementById("sismos-prev").disabled = sismosState.page <= 1;
  document.getElementById("sismos-next").disabled = sismosState.page >= sismosState.totalPages;
}

function filaSismo(sismo) {
  const fila = document.createElement("tr");
  fila.innerHTML = `
    <td>${sismo.magnitude.toFixed(1)}</td>
    <td>${sismo.location}</td>
    <td>${formatearFecha(sismo.event_time)}</td>
    <td>${sismo.depth.toFixed(1)}</td>
  `;
  return fila;
}

// ---------- metricas ----------

async function cargarMetricas() {
  const actual = await fetchJson("/metrics/current");

  if (actual && !actual.error) {
    document.getElementById("card-total").textContent = actual.earthquake_count ?? 0;
    document.getElementById("card-promedio").textContent = (actual.avg_magnitude ?? 0).toFixed(2);
    document.getElementById("card-maxima").textContent = (actual.max_magnitude ?? 0).toFixed(2);
    dibujarDistribucion(actual.magnitude_distribution || {});
  }

  const historico = await fetchJson("/metrics?page=1&page_size=12");
  dibujarPorHora(historico.items.slice().reverse());
}

function dibujarDistribucion(distribucion) {
  const etiquetas = Object.keys(distribucion);
  const valores = Object.values(distribucion);

  if (distribucionChart) distribucionChart.destroy();
  distribucionChart = new Chart(document.getElementById("chart-distribucion"), {
    type: "bar",
    data: {
      labels: etiquetas,
      datasets: [{ label: "Sismos", data: valores, backgroundColor: "#c6511a" }],
    },
    options: { responsive: true, plugins: { legend: { display: false } } },
  });
}

function dibujarPorHora(ventanas) {
  if (porHoraChart) porHoraChart.destroy();
  porHoraChart = new Chart(document.getElementById("chart-por-hora"), {
    type: "line",
    data: {
      labels: ventanas.map((v) => v.window),
      datasets: [{ label: "Sismos", data: ventanas.map((v) => v.earthquake_count), borderColor: "#c6511a", tension: 0.3 }],
    },
    options: { responsive: true, plugins: { legend: { display: false } } },
  });
}

// ---------- reportes ----------

async function cargarReportes() {
  const data = await fetchJson(`/reports?page=${reportesState.page}&page_size=${reportesState.pageSize}`);
  reportesState.totalPages = Math.max(1, Math.ceil(data.total / data.page_size));

  const tbody = document.getElementById("tabla-reportes");
  tbody.innerHTML = "";
  data.items.forEach((reporte) => {
    const fila = document.createElement("tr");
    fila.innerHTML = `
      <td>${formatearFecha(reporte.report_date)}</td>
      <td>${reporte.total_events}</td>
      <td>${reporte.average_magnitude.toFixed(2)}</td>
      <td>${reporte.max_magnitude.toFixed(2)}</td>
      <td>${(reporte.top_locations || []).join(", ")}</td>
    `;
    tbody.appendChild(fila);
  });

  document.getElementById("reportes-pagina").textContent = `Página ${reportesState.page} de ${reportesState.totalPages}`;
  document.getElementById("reportes-prev").disabled = reportesState.page <= 1;
  document.getElementById("reportes-next").disabled = reportesState.page >= reportesState.totalPages;
}

// ---------- mapa ----------

function inicializarMapa() {
  mapa = L.map("mapa").setView([10, -70], 2);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap",
  }).addTo(mapa);
  marcadores = L.layerGroup().addTo(mapa);
}

async function cargarMapa() {
  const data = await fetchJson("/earthquakes?page_size=100&sort_by=event_time&order=desc");
  marcadores.clearLayers();

  data.items.forEach((sismo) => {
    const radio = Math.max(4, sismo.magnitude * 3);
    L.circleMarker([sismo.latitude, sismo.longitude], {
      radius: radio,
      color: "#c6511a",
      fillColor: "#c6511a",
      fillOpacity: 0.5,
    })
      .bindPopup(`<b>${sismo.location}</b><br>Magnitud ${sismo.magnitude.toFixed(1)}<br>${formatearFecha(sismo.event_time)}`)
      .addTo(marcadores);
  });
}

// ---------- websocket (sismos en vivo) ----------

function conectarWebSocket() {
  const protocolo = location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${protocolo}://${location.host}/ws/earthquakes`);

  const dot = document.getElementById("live-dot");
  const texto = document.getElementById("live-text");

  socket.onopen = () => {
    dot.classList.add("connected");
    texto.textContent = "en vivo";
  };

  socket.onclose = () => {
    dot.classList.remove("connected");
    texto.textContent = "desconectado";
    setTimeout(conectarWebSocket, 5000); // reintenta en 5s
  };

  socket.onmessage = (evento) => {
    const sismo = JSON.parse(evento.data);
    mostrarToast(`Sismo nuevo: M${sismo.magnitude.toFixed(1)} en ${sismo.location}`);

    // Si estamos viendo la primera pagina de sismos, lo agregamos arriba de la tabla.
    if (sismosState.page === 1) {
      const tbody = document.getElementById("tabla-sismos");
      const fila = filaSismo(sismo);
      fila.classList.add("nuevo");
      tbody.prepend(fila);
    }
  };
}

// ---------- eventos y arranque ----------

document.getElementById("btn-buscar").addEventListener("click", () => {
  sismosState.page = 1;
  cargarSismos();
});

document.getElementById("sismos-prev").addEventListener("click", () => {
  if (sismosState.page > 1) { sismosState.page -= 1; cargarSismos(); }
});
document.getElementById("sismos-next").addEventListener("click", () => {
  if (sismosState.page < sismosState.totalPages) { sismosState.page += 1; cargarSismos(); }
});

document.getElementById("reportes-prev").addEventListener("click", () => {
  if (reportesState.page > 1) { reportesState.page -= 1; cargarReportes(); }
});
document.getElementById("reportes-next").addEventListener("click", () => {
  if (reportesState.page < reportesState.totalPages) { reportesState.page += 1; cargarReportes(); }
});

inicializarTabs();
inicializarMapa();
cargarSismos();
cargarMetricas();
cargarReportes();
cargarMapa();
conectarWebSocket();

// Refresca metricas y mapa cada 30s para que se vea "vivo" sin recargar la pagina.
setInterval(cargarMetricas, 30000);
setInterval(cargarMapa, 30000);
