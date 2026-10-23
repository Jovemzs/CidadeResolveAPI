import { esc } from "./html.js";
import { marcadorStatus } from "./ui.js";

const CENTRO_BRASIL = [-14.24, -51.93];

function iconePino() {
  return window.L.divIcon({ className: "", html: '<div class="pino"></div>', iconSize: [18, 18], iconAnchor: [9, 18], popupAnchor: [0, -18] });
}

export function criarMapa(elemento, { centro = CENTRO_BRASIL, zoom = 4 } = {}) {
  if (!window.L) {
    elemento.classList.add("mapa-indisponivel");
    elemento.textContent = "Mapa indisponível: não foi possível carregar o serviço de mapas.";
    return null;
  }
  const mapa = window.L.map(elemento, { scrollWheelZoom: false }).setView(centro, zoom);
  window.L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  }).addTo(mapa);
  // O contêiner acabou de entrar na página; recalcula o tamanho depois da pintura.
  setTimeout(() => mapa.invalidateSize(), 0);
  return mapa;
}

export function marcarOcorrencias(mapa, ocorrencias) {
  if (!mapa) return;
  const pontos = [];
  for (const o of ocorrencias) {
    if (o.latitude === null || o.longitude === null) continue;
    const ponto = [o.latitude, o.longitude];
    pontos.push(ponto);
    window.L.marker(ponto, { icon: iconePino(), title: o.titulo })
      .addTo(mapa)
      .bindPopup(
        `<a href="#/ocorrencias/${o.id}">${esc(o.titulo)}</a><br>${esc(o.bairro)}<br>${marcadorStatus(o.status)}`,
      );
  }
  if (pontos.length === 1) mapa.setView(pontos[0], 15);
  else if (pontos.length > 1) mapa.fitBounds(pontos, { padding: [30, 30], maxZoom: 15 });
}

/** Mapa em que um clique escolhe o ponto. Chama aoMudar(lat, lng) ou aoMudar(null, null). */
export function criarSeletorDePonto(elemento, inicial, aoMudar) {
  const temInicial = inicial.latitude !== null && inicial.latitude !== undefined;
  const mapa = criarMapa(elemento, temInicial ? { centro: [inicial.latitude, inicial.longitude], zoom: 16 } : {});
  if (!mapa) return { definir() {}, limpar() {} };

  let marcador = null;
  const definir = (lat, lng, centralizar = false) => {
    const ponto = [Number(lat.toFixed(6)), Number(lng.toFixed(6))];
    if (marcador) marcador.setLatLng(ponto);
    else marcador = window.L.marker(ponto, { icon: iconePino() }).addTo(mapa);
    if (centralizar) mapa.setView(ponto, 16);
    aoMudar(ponto[0], ponto[1]);
  };
  const limpar = () => {
    if (marcador) marcador.remove();
    marcador = null;
    aoMudar(null, null);
  };

  if (temInicial) definir(inicial.latitude, inicial.longitude);
  mapa.on("click", (evento) => definir(evento.latlng.lat, evento.latlng.lng));
  return { definir, limpar };
}
