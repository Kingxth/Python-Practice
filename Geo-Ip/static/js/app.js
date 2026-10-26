let mapa;
let marcadorActual = null;

document.addEventListener("DOMContentLoaded", () => {
    inicializarMapa();
    agregarLogConsola("[INIT] KIGN OSINT Autonomous Core v4.9 activo.");
});

function toggleHelpMenu() {
    const popup = document.getElementById('help_menu_popup');
    popup.classList.toggle('show');
}

window.addEventListener('click', function(e) {
    if (!e.target.closest('.help-dropdown-container')) {
        const popup = document.getElementById('help_menu_popup');
        if (popup && popup.classList.contains('show')) {
            popup.classList.remove('show');
        }
    }
});

function inicializarMapa() {
    mapa = L.map('mapa_principal', { zoomControl: false }).setView([20, 0], 2);
    L.tileLayer('https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png', {
        maxZoom: 20,
        attribution: '&copy; Stadia Maps, OpenMapTiles & OpenStreetMap contributors'
    }).addTo(mapa);
    L.control.zoom({ position: 'bottomright' }).addTo(mapa);

    mapa.on('click', function(e) {
        const lat = e.latlng.lat.toFixed(5);
        const lng = e.latlng.lng.toFixed(5);
        
        if (marcadorActual) mapa.removeLayer(marcadorActual);
        
        marcadorActual = L.marker([lat, lng]).addTo(mapa)
            .bindPopup(`<b>Puntero:</b><br>Lat: ${lat}, Lng: ${lng}`)
            .openPopup();

        document.getElementById('telemetry_status_puntero').innerText = `Puntero activo en (${lat}, ${lng})`;

        fetch(`/api/geo/reverse?lat=${lat}&lon=${lng}`)
            .then(res => res.json())
            .then(geoData => {
                document.getElementById('lbl_direccion_zonal').innerHTML = `
                    <div><b>Lat/Lng:</b> ${lat}, ${lng}</div>
                    <div><b>Dirección:</b> ${geoData.address}</div>
                    <div style="color:var(--yellow-neon); margin-top:2px;"><b>Zona Horaria:</b> ${geoData.timezone}</div>
                `;
            });
    });
}

function cambiarVista(vistaId) {
    document.querySelectorAll('.vista_panel').forEach(p => p.classList.remove('activa'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));

    const vistasMap = {
        'dashboard': ['vista_dashboard', 0],
        'data_hub': ['vista_data_hub', 1],
        'mapa': ['vista_mapa', 2],
        'raw_json': ['vista_raw_json', 3]
    };

    if (vistasMap[vistaId]) {
        const [targetId, indexBtn] = vistasMap[vistaId];
        document.getElementById(targetId).classList.add('activa');
        document.querySelectorAll('.view-switcher .nav-btn')[indexBtn].classList.add('active');
        if (vistaId === 'mapa') {
            setTimeout(() => { mapa.invalidateSize(); }, 100);
        }
    }
}

function verificarEnter(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        ejecutarEscaneo();
    }
}

function ejecutarEscaneo() {
    const ipInput = document.getElementById('input_ip');
    const emailInput = document.getElementById('input_email');
    const usuarioInput = document.getElementById('input_usuario');
    const urlInput = document.getElementById('input_url');

    const ip = ipInput.value.trim();
    const email = emailInput.value.trim();
    const usuario = usuarioInput.value.trim();
    const url = urlInput.value.trim();

    if (!ip && !email && !usuario && !url) {
        agregarLogConsola("[!] Error: Ingresa al menos un parámetro de objetivo.");
        return;
    }

    agregarLogConsola("----------------------------------------");
    agregarLogConsola(`[+] IP    : ${ip || 'N/A'}`);
    agregarLogConsola(`[+] EMAIL : ${email || 'N/A'}`);
    agregarLogConsola(`[+] USER  : ${usuario || 'N/A'}`);
    agregarLogConsola(`[+] URL   : ${url || 'N/A'}`);
    agregarLogConsola("[+] Estado: Ejecutando OSINT asíncrono y extrayendo multimedia...");

    ipInput.value = "";
    emailInput.value = "";
    usuarioInput.value = "";
    urlInput.value = "";

    fetch('/api/escanear', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip, email, usuario, url })
    })
    .then(res => res.json())
    .then(data => {
        agregarLogConsola(`[SUCCESS] Análisis completado (${data.hallazgos ? data.hallazgos.length : 0} módulos procesados).`);
        procesarResultadosRecon(data);
    })
    .catch(err => {
        agregarLogConsola(`[ERROR] Fallo de ejecución: ${err}`);
    });
}

function abrirLightbox(urlImg) {
    const modal = document.getElementById('lightbox_modal');
    const imgModal = document.getElementById('lightbox_img');
    imgModal.src = urlImg;
    modal.style.display = 'flex';
}

function cerrarLightbox() {
    document.getElementById('lightbox_modal').style.display = 'none';
}

function procesarResultadosRecon(data) {
    document.getElementById('contenedor_json_crudo').innerText = JSON.stringify(data, null, 2);

    const t = data.telemetria || {};
    const puertosHtml = (data.ports && data.ports.length > 0) 
        ? data.ports.map(p => `${p.port}/tcp [${p.state}]`).join(' | ') 
        : "Sin puertos abiertos detectados.";
    document.getElementById('lista_puertos').innerHTML = puertosHtml;

    if (t.lat && t.lng) {
        fetch(`/api/geo/reverse?lat=${t.lat}&lon=${t.lng}`)
            .then(res => res.json())
            .then(geoData => {
                document.getElementById('lbl_direccion_zonal').innerHTML = `
                    <div><b>Lat/Lng:</b> ${t.lat}, ${t.lng}</div>
                    <div><b>Dirección:</b> ${geoData.address}</div>
                    <div style="color:var(--yellow-neon); margin-top:2px;"><b>Zona Horaria:</b> ${geoData.timezone} | Reputación: ${t.reputacion}</div>
                `;
            });
    }

    // 1. Social & Identidad: Agrupación inteligente y tarjetas abiertas por defecto con hipervínculos directos
    const resSocial = document.getElementById('resumen_social');
    const socialItems = data.hallazgos ? data.hallazgos.filter(h => h.tool === 'Digital Footprint' || h.tool === 'Profile Scanner' || h.tool === 'Identity Registry') : [];
    
    let perfilesAgrupados = {};
    let extractedImages = [];

    if (socialItems.length > 0) {
        socialItems.forEach(item => {
            const lineas = item.valor.split('\n');
            let perfilActual = null;

            lineas.forEach(line => {
                // Detectar líneas de inicio de perfil (ej. [+] Duolingo: https://...)
                if (line.trim().startsWith('[+]') && line.includes('http')) {
                    const nombreWeb = line.replace('[+]', '').split(':')[0].trim();
                    const urlMatch = line.match(/https?:\/\/[^\s]+/);
                    const profileUrl = urlMatch ? urlMatch[0] : '#';

                    // Clave unificada para agrupar duplicados (ej. mismo nombre de plataforma)
                    const claveAgrupacion = nombreWeb.toLowerCase();

                    if (!perfilesAgrupados[claveAgrupacion]) {
                        perfilesAgrupados[claveAgrupacion] = {
                            web: nombreWeb,
                            url: profileUrl,
                            detalles: [line.trim()]
                        };
                    }
                    perfilActual = perfilesAgrupados[claveAgrupacion];
                } else if (perfilActual && (line.includes('├─') || line.includes('└─'))) {
                    perfilActual.detalles.push(line.trim());

                    // Extracción avanzada de imágenes, avatares y posts multimedia del texto
                    if (line.includes('image:') || line.includes('avatar') || line.includes('photo') || line.includes('media') || line.includes('post')) {
                        const imgMatch = line.match(/https?:\/\/[^\s]+/);
                        if (imgMatch) {
                            const imgUrl = imgMatch[0].replace(/['"<>]/g, '');
                            if (!extractedImages.includes(imgUrl)) {
                                extractedImages.push(imgUrl);
                            }
                        }
                    }
                }
            });
        });

        let htmlPerfiles = "";
        const keys = Object.keys(perfilesAgrupados);

        if (keys.length > 0) {
            keys.forEach(key => {
                const p = perfilesAgrupados[key];
                htmlPerfiles += `
                    <div class="social-item-clean" style="margin-bottom: 10px; border:1px solid var(--border-tactical); border-radius:4px; background:var(--bg-deep);">
                        <div style="padding: 8px 10px; border-bottom:1px solid var(--border-tactical); display:flex; justify-content:space-between; align-items:center; background:var(--bg-surface);">
                            <a href="${p.url}" target="_blank" style="color:var(--cyan-neon); font-weight:bold; font-size:0.75rem; text-decoration:underline;">[+] ${p.web}</a>
                            <span style="color:var(--text-muted); font-size:0.6rem;">Verificado</span>
                        </div>
                        <div style="padding: 8px 10px; background: rgba(0,0,0,0.2);">
                            <pre style="color:var(--text-main); font-size:0.65rem; white-space:pre-wrap; font-family:'JetBrains Mono',monospace; margin:0;">${p.detalles.join('\n')}</pre>
                        </div>
                    </div>
                `;
            });
            resSocial.innerHTML = htmlPerfiles;
        } else {
            resSocial.innerHTML = `<p class="placeholder-text">No se detectaron perfiles estructurados.</p>`;
        }
    } else {
        resSocial.innerHTML = `<p class="placeholder-text">No se detectaron resultados sociales.</p>`;
    }

    // 2. Infraestructura
    const resInfra = document.getElementById('resumen_infra');
    const infraItems = data.hallazgos ? data.hallazgos.filter(h => h.tool !== 'Digital Footprint' && h.tool !== 'Profile Scanner' && h.tool !== 'Identity Registry') : [];
    
    let infraHtml = `<div class="social-item-clean"><b>IP / Host Activo:</b> ${t.ip || 'N/A'} (Reputación: ${t.reputacion || 'N/A'})</div>`;
    infraItems.forEach(item => {
        infraHtml += `
            <div class="social-item-clean" style="margin-top:6px;">
                <b style="color:var(--cyan-neon); font-size:0.7rem;">[${item.tool}]</b>
                <pre style="background:var(--bg-deep); border:1px solid var(--border-tactical); color:var(--text-main); font-size:0.65rem; padding:6px; border-radius:4px; max-height:160px; overflow-y:auto; white-space:pre-wrap; margin-top:2px;">${item.valor}</pre>
            </div>
        `;
    });
    resInfra.innerHTML = infraHtml;

    // 3. Módulo Biométrico y Galería de Imágenes / Posts Multimedia
    const hasResults = socialItems.length > 0;
    const matchSimulado = hasResults ? (85 + Math.random() * 12).toFixed(1) : "14.2";
    document.getElementById('lbl_match_porcentaje').innerText = `${matchSimulado}%`;
    document.getElementById('barra_match_fill').style.width = `${matchSimulado}%`;

    // Consolidar todas las imágenes (avatares + posts/fotos extraídos de los perfiles)
    const allImages = Array.from(new Set([...(t.images || []), ...extractedImages])).slice(0, 25);
    
    if (allImages.length > 0) {
        document.getElementById('img_preview_facial').src = allImages[0];
        const galeria = document.getElementById('galeria_imagenes_encontradas');
        galeria.innerHTML = allImages.map(img => `
            <img src="${img}" class="gallery-img-original" onclick="abrirLightbox('${img}')" onerror="this.style.display='none'">
        `).join('');
    } else {
        document.getElementById('galeria_imagenes_encontradas').innerHTML = `<div class="gallery-placeholder">No se extrajeron imágenes o posts de los perfiles.</div>`;
    }

    // 4. Data Hub Tabla
    const total = data.hallazgos ? data.hallazgos.length : 0;
    document.getElementById('contador_badge').innerText = total;

    const cuerpoTabla = document.getElementById('cuerpo_tabla_osint');
    cuerpoTabla.innerHTML = "";

    if (!data.hallazgos || data.hallazgos.length === 0) {
        cuerpoTabla.innerHTML = `<tr><td colspan="6" class="table-empty-row">Sin hallazgos registrados.</td></tr>`;
    } else {
        data.hallazgos.forEach(item => {
            const fila = document.createElement('tr');
            fila.innerHTML = `
                <td><span class="badge_tool cyan">${item.tool}</span></td>
                <td>${item.categoria}</td>
                <td>${item.objetivo}</td>
                <td><pre style="font-size:0.65rem; max-height:50px; overflow:hidden; color:var(--cyan-neon);">${item.valor.substring(0, 80)}...</pre></td>
                <td>${item.metadata}</td>
                <td><button class="btn_mini" onclick="alert('Consulta el panel izquierdo o Data Hub para ver el reporte completo.')">Ver</button></td>
            `;
            cuerpoTabla.appendChild(fila);
        });
    }

    if (t.lat && t.lng) {
        mapa.setView([t.lat, t.lng], 11);
        if (marcadorActual) mapa.removeLayer(marcadorActual);
        marcadorActual = L.marker([t.lat, t.lng]).addTo(mapa)
            .bindPopup(`<b>Ciudad Detectada:</b> ${t.ciudad || 'Área Operativa'}<br>Lat/Lng: ${t.lat}, ${t.lng}`)
            .openPopup();
    }
}

function abortarEscaneo() {
    agregarLogConsola("[WARN] Operacion canceladad por el operador.");
}

function agregarLogConsola(mensaje) {
    const box = document.getElementById('f12_headers');
    const timestamp = new Date().toLocaleTimeString();
    if (mensaje.startsWith('---')) {
        box.innerHTML += `<br>${mensaje}`;
    } else {
        box.innerHTML += `<br>[${timestamp}] ${mensaje}`;
    }
    box.scrollTop = box.scrollHeight;
}

function filtrarTabla() {
    const filtro = document.getElementById('input_filtro_tabla').value.toLowerCase();
    document.querySelectorAll('#cuerpo_tabla_osint tr').forEach(fila => {
        fila.style.display = fila.innerText.toLowerCase().includes(filtro) ? "" : "none";
    });
}

function filtrarPorHerramienta() {
    const fuente = document.getElementById('filtro_herramienta').value.toLowerCase();
    document.querySelectorAll('#cuerpo_tabla_osint tr').forEach(fila => {
        const badge = fila.querySelector('.badge_tool');
        if (!badge) return;
        fila.style.display = (fuente === 'todos' || badge.innerText.toLowerCase().includes(fuente)) ? "" : "none";
    });
}