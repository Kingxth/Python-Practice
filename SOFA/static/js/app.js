// IMPORTANTE: Mantenemos las importaciones necesarias de tus módulos
import { SOFA_GEODATA } from './sofa_data.js';
import { PUESTOS_AUTO } from './puestos_auto.js';

// Variables de Estado
let map;
let markersLayerGroup;
let polygonsLayerGroup;
let ws = null;
let myUserId = 'Cosplayer_' + Math.floor(100 + Math.random() * 900);

// Presencia / Simulación GPS (Posición inicial sobre Pabellón 1)
let mySimulatedPos = [4.628955, -74.090587]; 
let playerRotationDeg = 0; // Orientación inicial (0 = Norte)
let myUserMarker = null;
let currentPabellonInside = null;
let visitedPabellones = new Set(JSON.parse(localStorage.getItem('visitedPabellones') || '[]'));

// Arreglo local para almacenar y filtrar expositores del pabellón activo
let currentPabellonTiendas = [];

const CORFERIAS_CENTER = [4.630295, -74.090525];
const CORFERIAS_BOUNDS = L.latLngBounds([4.627000, -74.093500], [4.633500, -74.087000]);

document.addEventListener('DOMContentLoaded', () => {
  initMap();
  renderMapPolygons();
  renderMapMarkers();
  updateChecklistUI();
  setupEventListeners();
  updateUserPresenceOnMap();
  checkGeofencePolygon();
  initWebSocket();
});

// Inicialización del Mapa GPS con Leaflet
function initMap() {
  map = L.map('map', {
    zoomControl: false,
    minZoom: 17,
    maxZoom: 22,
    zoomSnap: 0.1,
    zoomDelta: 0.2,
    maxBounds: CORFERIAS_BOUNDS,
    maxBoundsViscosity: 1.0
  }).setView(CORFERIAS_CENTER, 18);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 22,
    maxNativeZoom:19,
    attribution: ''
  }).addTo(map);

  // Perímetro General de Corferias
  L.polygon(SOFA_GEODATA.corferiasBounds, {
    color: '#a855f7',
    weight: 2,
    dashArray: '4, 4',
    fillColor: '#a855f7',
    fillOpacity: 0.03
  }).addTo(map);

  polygonsLayerGroup = L.layerGroup().addTo(map);
  markersLayerGroup = L.layerGroup().addTo(map);
}

// Algoritmo Ray-Casting para Geofencing
function pointInPolygon(point, vs) {
  const x = point[0], y = point[1];
  let inside = false;
  for (let i = 0, j = vs.length - 1; i < vs.length; j = i++) {
    const xi = vs[i][0], yi = vs[i][1];
    const xj = vs[j][0], yj = vs[j][1];

    const intersect = ((yi > y) !== (yj > y)) &&
        (x < (xj - xi) * (y - yi) / (yj - yi) + xi);
    if (intersect) inside = !inside;
  }
  return inside;
}

function createMinimalDotMarker(colorClass, label) {
  const html = `
    <div class="group relative flex items-center justify-center">
      <span class="w-3 h-3 rounded-full ${colorClass} border border-slate-900 shadow-md"></span>
      <span class="absolute left-4 bg-slate-950/90 text-slate-200 border border-slate-800 text-[10px] font-medium px-2 py-0.5 rounded shadow-xl whitespace-nowrap backdrop-blur-sm opacity-90">
        ${label}
      </span>
    </div>
  `;
  return L.divIcon({ html, className: 'custom-minimal-marker', iconSize: [12, 12], iconAnchor: [6, 6] });
}

// Marcador del Personaje con Cono de Campo de Visión (FOV)
function createMyPresenceMarker(rotationAngle) {
  const html = `
    <div class="relative flex items-center justify-center pointer-events-none">
      <div class="absolute -top-12 w-16 h-16 origin-bottom flex justify-center items-end" style="transform: rotate(${rotationAngle}deg);">
        <div class="w-full h-full bg-gradient-to-t from-pink-500/50 via-pink-500/10 to-transparent clip-fov"></div>
      </div>
      <span class="absolute w-7 h-7 rounded-full bg-pink-500/30 animate-ping"></span>
      <span class="w-4 h-4 rounded-full bg-pink-500 border-2 border-white shadow-[0_0_15px_#ec4899] z-10"></span>
      <span class="absolute -top-5 bg-pink-600 text-white text-[9px] font-black px-1.5 py-0.5 rounded shadow whitespace-nowrap">Primer bot bro</span>
    </div>
  `;
  return L.divIcon({ html, className: 'custom-presence-marker', iconSize: [20, 20], iconAnchor: [10, 10] });
}

// Mover presencia calculando dirección
export function moveSimulatedPresence(latMeters, lngMeters) {
  const PASO_HUMANO = 0.000015;
  mySimulatedPos[0] += latMeters * PASO_HUMANO;
  mySimulatedPos[1] += lngMeters * PASO_HUMANO;

  if (latMeters > 0 && lngMeters === 0) playerRotationDeg = 0;    // Norte
  if (latMeters < 0 && lngMeters === 0) playerRotationDeg = 180;  // Sur
  if (latMeters === 0 && lngMeters > 0) playerRotationDeg = 90;   // Este
  if (latMeters === 0 && lngMeters < 0) playerRotationDeg = 270;  // Oeste
  if (latMeters > 0 && lngMeters > 0) playerRotationDeg = 45;   // Noreste
  if (latMeters > 0 && lngMeters < 0) playerRotationDeg = 315;  // Noroeste
  if (latMeters < 0 && lngMeters > 0) playerRotationDeg = 135;  // Sureste
  if (latMeters < 0 && lngMeters < 0) playerRotationDeg = 225;  // Suroeste

  updateUserPresenceOnMap();
  sendLocationWebSocket();
  checkGeofencePolygon();
}

window.moveSimulatedPresence = moveSimulatedPresence;

export function setPlayerOrientation(degrees) {
  playerRotationDeg = degrees;
  updateUserPresenceOnMap();
}

function updateUserPresenceOnMap() {
  if (myUserMarker) map.removeLayer(myUserMarker);
  myUserMarker = L.marker(mySimulatedPos, { 
    icon: createMyPresenceMarker(playerRotationDeg), 
    zIndexOffset: 2000 
  }).addTo(map);
}

function checkGeofencePolygon() {
  let insidePab = null;

  SOFA_GEODATA.pabellones.forEach(pab => {
    if (pab.polygon && pointInPolygon(mySimulatedPos, pab.polygon)) {
      insidePab = pab;
    }
  });

  if (insidePab) {
    if (currentPabellonInside !== insidePab.id) {
      currentPabellonInside = insidePab.id;

      visitedPabellones.add(insidePab.id);
      localStorage.setItem('visitedPabellones', JSON.stringify([...visitedPabellones]));
      
      updateChecklistUI();
      renderMapPolygons();
      openPabellonDirectory(insidePab);
    }
  } else {
    if (currentPabellonInside !== null) {
      currentPabellonInside = null;
      closePabellonDirectory();
    }
  }
}

function renderMapPolygons() {
  polygonsLayerGroup.clearLayers();

  SOFA_GEODATA.pabellones.forEach(pab => {
    if (pab.polygon) {
      const isChecked = visitedPabellones.has(pab.id);
      L.polygon(pab.polygon, {
        color: isChecked ? '#a855f7' : '#3b82f6',
        weight: 2,
        fillColor: isChecked ? '#a855f7' : '#3b82f6',
        fillOpacity: isChecked ? 0.25 : 0.12
      }).addTo(polygonsLayerGroup);
    }
  });

  SOFA_GEODATA.zonaComida.forEach(serv => {
    if (serv.polygon) {
      L.polygon(serv.polygon, {
        color: '#10b981',
        weight: 2,
        fillColor: '#10b981',
        fillOpacity: 0.18
      }).addTo(polygonsLayerGroup);
    }
  });
}

function renderMapMarkers() {
  markersLayerGroup.clearLayers();

  SOFA_GEODATA.pabellones.forEach(pab => {
    const isChecked = visitedPabellones.has(pab.id);
    const color = isChecked ? 'bg-purple-500' : 'bg-blue-500';
    const label = `${isChecked ? '✓ ' : ''}${pab.nombre}`;
    const icon = createMinimalDotMarker(color, label);
    L.marker(pab.coordenadas_centro, { icon }).addTo(markersLayerGroup);
  });

  SOFA_GEODATA.baths.forEach(bath => {
    const icon = createMinimalDotMarker('bg-cyan-400', bath.nombre);
    L.marker(bath.coords, { icon }).addTo(markersLayerGroup);
  });

  (SOFA_GEODATA.comidaPuntos || []).forEach(food => {
    const icon = createMinimalDotMarker('bg-emerald-400', food.nombre);
    L.marker(food.coords, { icon }).addTo(markersLayerGroup);
  });
}

// Abrir el Overlay con el Directorio
function openPabellonDirectory(pabellon) {
  const overlay = document.getElementById('canvasOverlay');
  if (!overlay) return;
  
  document.getElementById('canvasPabellonTitle').innerText = pabellon.nombre;
  
  // Limpiar campo de búsqueda al entrar
  const searchInput = document.getElementById('searchStandInput');
  if (searchInput) searchInput.value = '';

  overlay.classList.remove('hidden');
  renderPabellonHTMLGraphic(pabellon);
}

function closePabellonDirectory() {
  const overlay = document.getElementById('canvasOverlay');
  if (overlay) overlay.classList.add('hidden');
}

// RENDERIZADO DEL DIRECTORIO DE EXPOSITORES EN HTML
function renderPabellonHTMLGraphic(pabellon) {
  const container = document.getElementById('pabellonGridHTML');
  if (!container || !pabellon) return;

  container.innerHTML = ''; // Limpiar grilla anterior
  currentPabellonTiendas = (PUESTOS_AUTO && PUESTOS_AUTO[pabellon.id]) || [];

  if (currentPabellonTiendas.length === 0) {
    container.innerHTML = `
      <div class="col-span-full text-center py-12">
        <i class="fa-solid fa-store-slash text-3xl text-slate-600 mb-3 block"></i>
        <p class="text-slate-400 text-xs">No hay expositores registrados oficialmente en este pabellón aún.</p>
      </div>
    `;
    return;
  }

  dibujarTarjetasTiendas(currentPabellonTiendas, pabellon.nombre);
}

// Dibujar Tarjetas Limpias e Interactivas
function dibujarTarjetasTiendas(tiendas, nombrePabellon) {
  const container = document.getElementById('pabellonGridHTML');
  if (!container) return;
  container.innerHTML = '';

  if (tiendas.length === 0) {
    container.innerHTML = `
      <div class="col-span-full text-center py-8">
        <p class="text-slate-500 text-xs">No se encontraron resultados para la búsqueda.</p>
      </div>
    `;
    return;
  }

  tiendas.forEach((item) => {
    const card = document.createElement('div');
    card.className = `
      bg-slate-900/90 border border-slate-800 hover:border-purple-500/60 
      active:scale-95 transition-all p-3.5 rounded-2xl flex flex-col justify-between 
      shadow-lg hover:shadow-purple-500/10 gap-3 group cursor-pointer
    `;

    card.innerHTML = `
      <div>
        <div class="flex items-center justify-between mb-2">
          <span class="text-[10px] font-mono font-bold text-pink-400 bg-pink-950/80 border border-pink-500/30 px-2 py-0.5 rounded-md">
            STAND #${item.stand}
          </span>
          <span class="text-[9px] font-bold text-purple-300 bg-purple-950/60 border border-purple-800/40 px-2 py-0.5 rounded-md">
            ${item.categoria || 'General'}
          </span>
        </div>

        <h4 class="text-sm font-bold text-white group-hover:text-purple-300 transition leading-snug">
          ${item.nombre}
        </h4>
      </div>

      <div class="flex items-center justify-between pt-2 border-t border-slate-800/80">
        <span class="text-[10px] text-slate-400 font-medium flex items-center gap-1">
          <i class="fa-solid fa-images text-pink-400"></i> Ver galería y contacto
        </span>
        
        <a href="${item.web || '#'}" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation()" 
           class="bg-slate-800 hover:bg-pink-600 text-slate-200 hover:text-white px-2.5 py-1 rounded-lg text-[10px] font-bold transition flex items-center gap-1 border border-slate-700">
          <span>Web</span>
          <i class="fa-solid fa-arrow-up-right-from-square text-[8px]"></i>
        </a>
      </div>
    `;

    // Abrir Modal con Galería de Imágenes, Correo y Redes
    card.addEventListener('click', () => {
      document.getElementById('modalPabellonBadge').innerText = nombrePabellon || 'Pabellón';
      document.getElementById('modalStandNum').innerText = `STAND #${item.stand}`;
      document.getElementById('modalStandTitle').innerText = item.nombre;
      document.getElementById('modalStandCat').innerText = item.categoria || 'Expositor Oficial';
      document.getElementById('modalStandDesc').innerText = item.descripcion || 'Expositor oficial registrado en el festival SOFA Corferias.';
      
      const webLink = document.getElementById('modalStandWeb');
      webLink.href = item.web || '#';
      webLink.setAttribute('target', '_blank');
      webLink.setAttribute('rel', 'noopener noreferrer');

      // Cargar Galería de Fotos del Perfil
      const galleryContainer = document.getElementById('modalStandGallery');
      galleryContainer.innerHTML = '';

      if (item.fotos && item.fotos.length > 0) {
        item.fotos.forEach(src => {
          const img = document.createElement('img');
          img.src = src;
          img.alt = item.nombre;
          img.className = 'w-full h-24 object-cover rounded-xl border border-slate-800 hover:scale-105 transition duration-200 shadow-md cursor-pointer';
          
          // Abrir imagen en pantalla completa al tocarla
          img.addEventListener('click', () => window.open(src, '_blank'));
          galleryContainer.appendChild(img);
        });
      }

      // Renderizar Redes Sociales y Correo en el Modal
      let contactContainer = document.getElementById('modalContactInfo');
      if (!contactContainer) {
        contactContainer = document.createElement('div');
        contactContainer.id = 'modalContactInfo';
        contactContainer.className = 'mb-4 space-y-2';
        document.getElementById('modalStandGallery').parentElement.after(contactContainer);
      }

      contactContainer.innerHTML = `
        <span class="text-[10px] text-slate-500 uppercase tracking-wider block font-bold">Contacto y Redes</span>
        <div class="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1.5 text-xs">
          <p class="text-slate-300 flex items-center gap-2">
            <i class="fa-solid fa-envelope text-purple-400"></i>
            <span>${item.email || 'No especificado'}</span>
          </p>
          <div class="flex gap-3 pt-1">
            ${item.instagram ? `
              <a href="${item.instagram}" target="_blank" class="text-pink-400 hover:text-pink-300 flex items-center gap-1 font-bold">
                <i class="fa-brands fa-instagram text-sm"></i> Instagram
              </a>
            ` : ''}
            ${item.facebook ? `
              <a href="${item.facebook}" target="_blank" class="text-blue-400 hover:text-blue-300 flex items-center gap-1 font-bold">
                <i class="fa-brands fa-facebook text-sm"></i> Facebook
              </a>
            ` : ''}
          </div>
        </div>
      `;

      document.getElementById('standModal').classList.remove('hidden');
    });

    container.appendChild(card);
  });
}


function updateChecklistUI() {
  const container = document.getElementById('checklistItems');
  if (!container) return;

  container.innerHTML = '';
  document.getElementById('checkProgressText').innerText = `${visitedPabellones.size} / ${SOFA_GEODATA.pabellones.length}`;

  SOFA_GEODATA.pabellones.forEach(pab => {
    const isChecked = visitedPabellones.has(pab.id);
    const div = document.createElement('div');
    div.className = `flex items-center justify-between p-2 rounded-xl border text-xs ${
      isChecked ? 'bg-purple-950/40 border-purple-500/40 text-purple-300' : 'bg-slate-900/60 border-slate-800 text-slate-400'
    }`;
    div.innerHTML = `
      <span>${pab.nombre}</span>
      <span class="text-[10px] font-bold ${isChecked ? 'text-purple-400' : 'text-slate-600'}">
        ${isChecked ? 'Checked ✓' : 'Pendiente'}
      </span>
    `;
    container.appendChild(div);
  });
}

function initWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  ws = new WebSocket(`${protocol}//${window.location.host}/ws/geoloc`);
}

function sendLocationWebSocket() {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ user_id: myUserId, lat: mySimulatedPos[0], lng: mySimulatedPos[1] }));
  }
}

function setupEventListeners() {
  const recenterBtn = document.getElementById('recenterBtn');
  if (recenterBtn) {
    recenterBtn.addEventListener('click', () => {
      map.flyTo(mySimulatedPos, 19, { duration: 0.6 });
    });
  }

  const closeBtn = document.getElementById('closeCanvasBtn');
  if (closeBtn) {
    closeBtn.addEventListener('click', closePabellonDirectory);
  }

  const checklistBtn = document.getElementById('checklistToggleBtn');
  if (checklistBtn) {
    checklistBtn.addEventListener('click', () => {
      document.getElementById('checklistDrawer').classList.toggle('hidden');
    });
  }

  // Cierre del modal de detalles del expositor
  const closeModalBtn = document.getElementById('closeStandModalBtn');
  if (closeModalBtn) {
    closeModalBtn.addEventListener('click', () => {
      document.getElementById('standModal').classList.add('hidden');
    });
  }

  // Buscador en Tiempo Real dentro del Pabellón
  const searchInput = document.getElementById('searchStandInput');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase().trim();
      const filtradas = currentPabellonTiendas.filter(t => 
        t.nombre.toLowerCase().includes(query) || 
        t.stand.toLowerCase().includes(query) ||
        (t.categoria && t.categoria.toLowerCase().includes(query))
      );
      dibujarTarjetasTiendas(filtradas, document.getElementById('canvasPabellonTitle').innerText);
    });
  }
}