async function organizarArchivos() {
    const origen = document.getElementById('origen').value;
    const destino = document.getElementById('destino').value;
    const statusMsg = document.getElementById('status-message');

    statusMsg.style.color = "#ccc";
    statusMsg.innerText = "Procesando archivos...";

    try {
        const response = await fetch('/api/organizar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ origen, destino })
        });

        const data = await response.json();

        if (response.ok) {
            statusMsg.style.color = "#4CAF50";
            statusMsg.innerText = data.message;
            cargarLogs(); // Actualizar lista de logs
        } else {
            statusMsg.style.color = "#ff5252";
            statusMsg.innerText = "Error: " + data.message;
        }
    } catch (error) {
        statusMsg.style.color = "#ff5252";
        statusMsg.innerText = "Error de conexion con el servidor.";
    }
}

async function cargarLogs() {
    const listaLogs = document.getElementById('lista-logs');
    listaLogs.innerHTML = '<li>...Cargando...</li>';

    try {
        const response = await fetch('/api/logs');
        const logs = await response.json();

        listaLogs.innerHTML = '';

        if (logs.length === 0) {
            listaLogs.innerHTML = '<li style="color: #777;">No hay logs</li>';
            return;
        }

        logs.forEach(nombreLog => {
            const li = document.createElement('li');
            li.innerText = nombreLog;
            li.onclick = () => verLog(nombreLog);
            listaLogs.appendChild(li);
        });


        if (logs.length > 0) {
            verLog(logs[0]);
        }
    } catch (error) {
        listaLogs.innerHTML = '<li style="color: #ff5252;">Error al cargar</li>';
    }
}

async function verLog(nombreArchivo) {
    const visor = document.getElementById('contenido-log');
    visor.innerText = "Leyendo archivo...";

    try {
        const response = await fetch(`/api/logs/${nombreArchivo}`);
        const data = await response.json();

        if (response.ok) {
            visor.innerText = data.content;
        } else {
            visor.innerText = "No se pudo leer el archivo.";
        }
    } catch (error) {
        visor.innerText = "Error de conexion";
    }
}

window.onload = () => {
    cargarLogs();
};