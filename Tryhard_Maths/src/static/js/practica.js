document.addEventListener('DOMContentLoaded', () => {
    const textoEcuacion = document.getElementById('texto-ecuacion');
    const inputRespuesta = document.getElementById('resp-tablero');
    const btnVerificar = document.getElementById('btn-verificar-tablero');
    const selectTema = document.getElementById('select-tema-practica');
    const btnCambiarTema = document.getElementById('btn-cambiar-tema');
    const retroalimentacion = document.getElementById('retroalimentacion');
    let tiempoInicio = Date.now();


    function cargarPregunta() {
        const temaSeleccionado = selectTema.value;
        textoEcuacion.innerHTML = 'Cargando...';
        inputRespuesta.value = '';
        retroalimentacion.textContent = '';
        retroalimentacion.className = 'feedback-msg';
        tiempoInicio = Date.now();

        fetch(`/obtener_pregunta?tipo=${temaSeleccionado}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'unauthorized') {
                    window.location.href = '/login';
                    return;
                }
                textoEcuacion.innerHTML = data.pregunta;
            })
            .catch(error => {
                console.error('Error al cargar pregunta:', error);
                textoEcuacion.innerHTML = 'Error al cargar la pregunta';
            });
    }

    function verificarRespuesta() {
        const respuesta = inputRespuesta.value.trim();
        if (!respuesta) return;

        const tiempoMs = Date.now() - tiempoInicio;

        fetch('/validar_respuesta', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                respuesta: respuesta,
                tiempo_ms: tiempoMs
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.resultado) {
                retroalimentacion.textContent = 'Correcto';
                retroalimentacion.style.color = '#2ecc71';
                setTimeout(cargarPregunta, 1500);
            } else {
                retroalimentacion.textContent = `Incorrecto. La respuesta correcta era: ${data.solucion_correcta}`;
                retroalimentacion.style.color = '#e74c3c';
            }
        })
        .catch(error => {
            console.error('Error al validar:', error);
        });
    }

    btnVerificar.addEventListener('click', verificarRespuesta);
    inputRespuesta.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            verificarRespuesta();
        }
    });

    btnCambiarTema.addEventListener('click', cargarPregunta);
    selectTema.addEventListener('change', cargarPregunta);

    cargarPregunta();

    const canvas = document.getElementById('pizarron');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        let dibujando = false;
        let modoBorrador = false;

        function ajustarCanvas() {
            canvas.width = canvas.parentElement.clientWidth;
            canvas.height = canvas.parentElement.clientHeight - 60;
        }
        ajustarCanvas();
        window.addEventListener('resize', ajustarCanvas);

        canvas.addEventListener('mousedown', () => { dibujando = true; });
        canvas.addEventListener('mouseup', () => { dibujando = false; ctx.beginPath(); });
        canvas.addEventListener('mousemove', (e) => {
            if (!dibujando) return;
            ctx.lineWidth = modoBorrador ? 20 : 3;
            ctx.lineCap = 'round';
            ctx.strokeStyle = modoBorrador ? '#141414' : '#ffffff';

            const rect = canvas.getBoundingClientRect();
            ctx.lineTo(e.clientX - rect.left, e.clientY - rect.top);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(e.clientX - rect.left, e.clientY - rect.top);
        });

        document.getElementById('btn-lapiz').addEventListener('click', () => {
            modoBorrador = false;
            document.getElementById('btn-lapiz').classList.add('active');
            document.getElementById('btn-borrador').classList.remove('active');
        });

        document.getElementById('btn-borrador').addEventListener('click', () => {
            modoBorrador = true;
            document.getElementById('btn-borrador').classList.add('active');
            document.getElementById('btn-lapiz').classList.remove('active');
        });

        document.getElementById('btn-limpiar').addEventListener('click', () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
        });
    }
});