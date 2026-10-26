const side = document.getElementById('sidebar');
const main = document.getElementById('main-container');
const menu = document.getElementById('menu-juego');
const zona = document.getElementById('zona-juego');
const modal = document.getElementById('modal-resultados');
const configSec = document.getElementById('config-operaciones');
const btnC = document.getElementById('btn-classic');
const btnA = document.getElementById('btn-abandonar');
const btnV = document.getElementById('btn-volver-menu');
const btnConfigLink = document.getElementById('btn-config-classic');
const btnGuardarConfig = document.getElementById('btn-guardar-config');
const btnVolverDesdeConfig = document.getElementById('btn-volver-desde-config');
const inp = document.getElementById('respuesta-usuario');

const contenedorOps = document.getElementById('lista-config-ops');
const opsConfig = ['Suma', 'Resta', 'Multiplicacion', 'Division', 'Potencias', 'Raices', 'Prop_potencias', 'Sencos'];

let t = 6000, p = 0, racha = 0, intT;
let inicioPregunta = 0; // coso de tiempo

btnC.addEventListener('click', start);
inp.addEventListener('keypress', (e) => { if (e.key === 'Enter') check(); });
btnA.addEventListener('click', () => { stop(); reset(); });
btnV.addEventListener('click', reset);

btnConfigLink.addEventListener('click', (e) => {
    e.preventDefault();
    menu.classList.add('hidden');
    configSec.classList.remove('hidden');
});

btnVolverDesdeConfig.addEventListener('click', () => {
    configSec.classList.add('hidden');
    menu.classList.remove('hidden');
});

btnGuardarConfig.addEventListener('click', () => {
    const configuracion = {};
    document.querySelectorAll('.dificultad-selector').forEach(selector => {
        const op = selector.getAttribute('data-op');
        const activa = selector.querySelector('.btn-dificultad.active');
        configuracion[op] = activa ? activa.getAttribute('data-val') : 'facil';
    });
    fetch('/guardar_config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(configuracion)
    });
    configSec.classList.add('hidden');
    menu.classList.remove('hidden');
});

contenedorOps.addEventListener('click', (e) => {
    if (e.target.classList.contains('btn-dificultad')) {
        const parent = e.target.parentElement;
        parent.querySelectorAll('.btn-dificultad').forEach(btn => btn.classList.remove('active'));
        e.target.classList.add('active');
    }
});

// Generar botones de dificultad
opsConfig.forEach(op => {
    const row = document.createElement('div');
    row.className = 'config-row';
    row.innerHTML = `
        <span>${op}</span>
        <div class="dificultad-selector" data-op="${op.toLowerCase()}">
            <button class="btn-dificultad active" data-val="facil">Facil</button>
            <button class="btn-dificultad" data-val="medio">Medio</button>
            <button class="btn-dificultad" data-val="dificil">Difícil</button>
        </div>
    `;
    contenedorOps.appendChild(row);
});

function start() {
    side.classList.add('hidden');
    main.classList.add('full-width');
    menu.classList.add('hidden');
    zona.classList.remove('hidden');

    const ops = [];
    if (document.getElementById('op-basicas').checked) ops.push('suma', 'resta');
    if (document.getElementById('op-multdiv').checked) ops.push('multiplicacion', 'division');
    if (document.getElementById('op-potencias').checked) ops.push('potencias');
    if (document.getElementById('op-raices').checked) ops.push('raices');
    if (document.getElementById('op-prop-potencias').checked) ops.push('prop_potencias');
    if (document.getElementById('op-sencos').checked) ops.push('sencos');

    t = 1000; p = 0; racha = 0;
    updateHUD();

    fetch('/iniciar_juego', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ operaciones: ops })
    }).then(() => next());

    intT = setInterval(() => {
        t--;
        let s = Math.floor(t / 100);
        let ms = t % 100;
        document.getElementById('tiempo-valor').innerText = `${s}.${ms.toString().padStart(2, '0')}`;
        if (t <= 0) stop();
    }, 10);
}

function next() {
    fetch('/obtener_pregunta')
        .then(res => res.json())
        .then(data => {
            let pTexto = data.pregunta;
            if (pTexto.includes('^')) {
                let partes = pTexto.split('^');
                pTexto = `${partes[0]}<sup>${partes[1]}</sup>`;
            }
            document.getElementById('pregunta-texto').innerHTML = pTexto;
            inp.value = '';
            inp.focus();
            inicioPregunta = Date.now();
        });
}

function check() {
    const val = inp.value.trim();
    if (!val) return;
    
    const tiempoRespuesta = Date.now() - inicioPregunta;

    fetch('/validar_respuesta', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ respuesta: val, tiempo_ms: tiempoRespuesta })
    })
    .then(res => res.json())
    .then(data => {
        const el = document.getElementById('pregunta-texto');
        if (data.racha_actual !== undefined) {
            racha = data.racha_actual;
        }
        if (data.resultado === true) {
            p += 10;
            t += 500;
            next(); 
        } else {
            el.classList.add('wrong');
            setTimeout(() => {
                el.classList.remove('wrong');
                next();
            }, 300);
        }
        updateHUD();
    });
}

function updateHUD() {
    document.getElementById('puntos-valor').innerText = p;
    const rEl = document.getElementById('racha-valor');
    if (rEl) rEl.innerText = racha;
}

function stop() {
    clearInterval(intT);
    zona.classList.add('hidden');
    modal.classList.remove('hidden');

    fetch('/guardar_partida', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tiempo_total: (6000 - t) / 100 })
    });
    
    fetch('/obtener_config_dificultades')
        .then(res => res.json())
        .then(config => {
            document.getElementById('score-final').innerText = p;
            const lista = document.getElementById('lista-dificultades');
            lista.innerHTML = '';
            for (const [op, dif] of Object.entries(config)) {
                const li = document.createElement('li');
                li.innerHTML = `<strong>${op}:</strong> <span class="dificultad-tag ${dif}">${dif.toUpperCase()}</span>`;
                lista.appendChild(li);
            }
        });
}

function reset() {
    modal.classList.add('hidden');
    zona.classList.add('hidden');
    configSec.classList.add('hidden');
    menu.classList.remove('hidden');
    side.classList.remove('hidden');
    main.classList.remove('full-width');
}

document.querySelectorAll('.chk-tablero-op').forEach(chk => {
    const guardadas = JSON.parse(localStorage.getItem('ops_tablero') || '["ecuacion_1er_grado"]');
    if (guardadas.includes(chk.value)) {
        chk.checked = true;
    } else {
        chk.checked = false;
    }

    chk.addEventListener('change', () => {
        const seleccionadas = [];
        document.querySelectorAll('.chk-tablero-op:checked').forEach(c => {
            seleccionadas.push(c.value);
        });
        localStorage.setItem('ops_tablero', JSON.stringify(seleccionadas));
    });
});