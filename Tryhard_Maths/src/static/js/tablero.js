document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('pizarron');
    const ctx = canvas.getContext('2d');
    
    const btnLapiz = document.getElementById('btn-lapiz');
    const btnBorrador = document.getElementById('btn-borrador');
    const btnLimpiar = document.getElementById('btn-limpiar');
    const btnVerificar = document.getElementById('btn-verificar-tablero');
    const textoEcuacion = document.getElementById('texto-ecuacion');
    const feedback = document.getElementById('retroalimentacion');

    const chk1 = document.getElementById('chk-eq1');
    const chk2 = document.getElementById('chk-eq2');
    const chkfact = document.getElementById('chk-fact');
    const chkDerivadas = document.getElementById('chk-derivadas');
    const chkIntegrales = document.getElementById('chk-integrales');
    const chkLhopital = document.getElementById('chk-lhopital');
    const chkOptimizacion = document.getElementById('chk-optimizacion');
    const chkPartes = document.getElementById('chk-partes');
    const chkSust = document.getElementById('chk-sust');
    const chkFracciones = document.getElementById('chk-fracciones');

    const todosLosCheckboxes = [
        chk1, chk2, chkfact, chkDerivadas, chkIntegrales, 
        chkLhopital, chkOptimizacion, chkPartes, chkSust, chkFracciones
    ];

    function ajustarCanvas() {
        const rect = canvas.parentElement.getBoundingClientRect();
        canvas.width = rect.width - 40;
        canvas.height = rect.height - 80;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
    }
    
    ajustarCanvas();
    window.addEventListener('resize', ajustarCanvas);

    let dibujando = false;
    let modoBorrador = false;
    let inicioPregunta = 0;

    ctx.strokeStyle = '#f3f2f2';
    ctx.lineWidth = 3;

    function cargarPreferencias() {
        const guardado = localStorage.getItem('ops_tablero');
        if (guardado) {
            const ops = JSON.parse(guardado);
            if (chk1) chk1.checked = ops.includes('ecuacion_1er_grado');
            if (chk2) chk2.checked = ops.includes('ecuacion_2do_grado');
            if (chkfact) chkfact.checked = ops.includes('factorizacion');
            if (chkDerivadas) chkDerivadas.checked = ops.includes('derivadas');
            if (chkIntegrales) chkIntegrales.checked = ops.includes('integrales');
            if (chkLhopital) chkLhopital.checked = ops.includes('l_hopital');
            if (chkOptimizacion) chkOptimizacion.checked = ops.includes('optimizacion');
            if (chkPartes) chkPartes.checked = ops.includes('integrales_partes');
            if (chkSust) chkSust.checked = ops.includes('sustitucion_trig');
            if (chkFracciones) chkFracciones.checked = ops.includes('fracciones_parciales');
        }
    }

    function guardarPreferencias() {
        const ops = obtenerOpsSeleccionadas();
        localStorage.setItem('ops_tablero', JSON.stringify(ops));
    }

    cargarPreferencias();

    canvas.addEventListener('pointerdown', (e) => {
        dibujando = true;
        ctx.beginPath();
        ctx.moveTo(e.offsetX, e.offsetY);
    });

    canvas.addEventListener('pointermove', (e) => {
        if (!dibujando) return;
        
        if (modoBorrador) {
            ctx.strokeStyle = '#0f0f0f';
            ctx.lineWidth = 20;
        } else {
            ctx.strokeStyle = '#f3f2f2';
            ctx.lineWidth = 3;
        }
        
        ctx.lineTo(e.offsetX, e.offsetY);
        ctx.stroke();
    });

    canvas.addEventListener('pointerup', () => { dibujando = false; ctx.beginPath(); });
    canvas.addEventListener('pointerleave', () => { dibujando = false; ctx.beginPath(); });

    btnLimpiar.addEventListener('click', () => {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
    });

    function obtenerOpsSeleccionadas() {
        const ops = [];
        if (chk1 && chk1.checked) ops.push('ecuacion_1er_grado');
        if (chk2 && chk2.checked) ops.push('ecuacion_2do_grado');
        if (chkfact && chkfact.checked) ops.push('factorizacion');
        if (chkDerivadas && chkDerivadas.checked) ops.push('derivadas');
        if (chkIntegrales && chkIntegrales.checked) ops.push('integrales');
        if (chkLhopital && chkLhopital.checked) ops.push('l_hopital');
        if (chkOptimizacion && chkOptimizacion.checked) ops.push('optimizacion');
        if (chkPartes && chkPartes.checked) ops.push('integrales_partes');
        if (chkSust && chkSust.checked) ops.push('sustitucion_trig');
        if (chkFracciones && chkFracciones.checked) ops.push('fracciones_parciales');
        
        return ops.length > 0 ? ops : ['ecuacion_1er_grado'];
    }

    todosLosCheckboxes.forEach(chk => {
        if (chk) {
            chk.addEventListener('change', () => {
                guardarPreferencias();
                siguienteEcuacion();
            });
        }
    });

    function siguienteEcuacion() {
        const operacionesActivas = obtenerOpsSeleccionadas();

        fetch('/iniciar_juego', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ operaciones: operacionesActivas })
        })
        .then(() => fetch('/obtener_pregunta'))
        .then(res => res.json())
        .then(data => {
            textoEcuacion.innerHTML = data.pregunta;
            
            const contenedorInputs = document.getElementById('inputs-dinamicos');
            const labelResp = document.getElementById('label-respuesta');
            contenedorInputs.setAttribute('data-tipo', data.tipo);

            if (data.tipo === 'ecuacion_2do_grado') {
                labelResp.innerText = "Escribe los valores de x:";
                contenedorInputs.innerHTML = `
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <span>x₁ =</span> <input type="text" id="resp-x1" autocomplete="off" placeholder="Ej: -4" style="width: 80px;">
                        <span>x₂ =</span> <input type="text" id="resp-x2" autocomplete="off" placeholder="Ej: -3" style="width: 80px;">
                    </div>
                `;
                document.getElementById('resp-x1').focus();
            } else {
                labelResp.innerText = "Escribe tu respuesta :D";
                contenedorInputs.innerHTML = `
                    <input type="text" id="resp-tablero" autocomplete="off" placeholder="Escribe tu resultado...">
                `;
                document.getElementById('resp-tablero').focus();
            }

            inicioPregunta = Date.now();
        });
    }

    function verificarRespuesta() {
        const contenedorInputs = document.getElementById('inputs-dinamicos');
        const tipoActual = contenedorInputs.getAttribute('data-tipo');
        
        let valorParaEnviar = "";

        if (tipoActual === 'ecuacion_2do_grado') {
            const x1 = document.getElementById('resp-x1').value.trim();
            const x2 = document.getElementById('resp-x2').value.trim();
            if (!x1 || !x2) return;
            valorParaEnviar = `${x1}, ${x2}`;
        } else {
            const inpRespuesta = document.getElementById('resp-tablero');
            valorParaEnviar = inpRespuesta ? inpRespuesta.value.trim() : "";
            if (!valorParaEnviar) return;
        }

        const tiempoRespuesta = Date.now() - inicioPregunta;

        fetch('/validar_respuesta', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ respuesta: valorParaEnviar, tiempo_ms: tiempoRespuesta })
        })
        .then(res => res.json())
        .then(data => {
            if (data.resultado === true) {
                feedback.innerText = "Correcto!";
                feedback.style.color = "#2ecc71";
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                setTimeout(() => {
                    feedback.innerText = "";
                    siguienteEcuacion();
                }, 400);
            } else {
                feedback.innerText = "Incorrecto";
                feedback.style.color = "#e74c3c";
                if (tipoActual === 'ecuacion_2do_grado') {
                    document.getElementById('resp-x1').focus();
                    document.getElementById('resp-x1').select();
                } else {
                    const inpRespuesta = document.getElementById('resp-tablero');
                    if (inpRespuesta) { inpRespuesta.focus(); inpRespuesta.select(); }
                }
            }
        });
    }

    btnVerificar.addEventListener('click', verificarRespuesta);
    document.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const activeElement = document.activeElement;
            if (activeElement && (activeElement.id === 'resp-tablero' || activeElement.id === 'resp-x1' || activeElement.id === 'resp-x2')) {
                verificarRespuesta();
            }
        }
    });

    siguienteEcuacion();

    btnLapiz.addEventListener('click', () => {
        modoBorrador = false;
        btnLapiz.classList.add('active');
        btnBorrador.classList.remove('active');
        canvas.classList.remove('borrador-activo');
    });

    btnBorrador.addEventListener('click', () => {
        modoBorrador = true;
        btnBorrador.classList.add('active');
        btnLapiz.classList.remove('active');
        canvas.classList.add('borrador-activo');
    });
});