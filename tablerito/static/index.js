const canvas = document.getElementById('pizarra');
const ctx = canvas.getContext('2d');
const container = document.getElementById('canvas-container');
const eraserCursor = document.getElementById('eraser-cursor');
const colorPicker = document.getElementById('hidden-color-picker');
const btnCustomColor = document.getElementById('btn-custom-color');
const zoomDisplay = document.getElementById('zoom-display');
const lineWidthSelect = document.getElementById('lineWidth');
const sidebar = document.getElementById('sidebar');
const btnDraw = document.getElementById('btn-draw');
const btnLine = document.getElementById('btn-line');
const btnRect = document.getElementById('btn-rect');
const btnErase = document.getElementById('btn-erase');
const btnPan = document.getElementById('btn-pan');
const btnZoom = document.getElementById('btn-zoom');
const btnClear = document.getElementById('btn-clear');
const btnSave = document.getElementById('btn-save');
const btnUndo = document.getElementById('btn-undo');
const btnRedo = document.getElementById('btn-redo');
const btnImport = document.getElementById('btn-import');
const imageLoader = document.getElementById('image-loader');
const infoPointer = document.getElementById('info-pointer');
const colorButtons = document.querySelectorAll('.color-btn');
let isDrawing = false;
let mode = 'draw';
let selectedColor = '#ffffff';
let lastX = 0, lastY = 0;
let rawLastX = 0, rawLastY = 0;
let startX = 0, startY = 0;
let offsetX = 0, offsetY = 0;
let scale = 1.0;
let tempPreviousMode = null;
let historyStack = [];
let historyIndex = -1;
let activePointers = [];
let floatingImage = null;
let floatingImageX = 0;
let floatingImageY = 0;
const drawingCanvas = document.createElement('canvas');
const drawingCtx = drawingCanvas.getContext('2d');

function saveHistoryState() {
    if (historyIndex < historyStack.length - 1) {
        historyStack = historyStack.slice(0, historyIndex + 1);
    }
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = drawingCanvas.width;
    tempCanvas.height = drawingCanvas.height;
    const tempCtx = tempCanvas.getContext('2d');
    tempCtx.drawImage(drawingCanvas, 0, 0);
    historyStack.push(tempCanvas);
    historyIndex++;
    if (historyStack.length > 500) {
        historyStack.shift();
        historyIndex--;
    }
}

function undo() {
    if (historyIndex > 0) {
        historyIndex--;
        restoreHistoryState();
    }
}

function redo() {
    if (historyIndex < historyStack.length - 1) {
        historyIndex++;
        restoreHistoryState();
    }
}

function restoreHistoryState() {
    if (historyIndex < 0 || !historyStack[historyIndex]) {
        return;
    }
    const state = historyStack[historyIndex];
    drawingCanvas.width = state.width;
    drawingCanvas.height = state.height;
    drawingCtx.clearRect(0, 0, drawingCanvas.width, drawingCanvas.height);
    drawingCtx.drawImage(state, 0, 0);
    drawingCtx.lineCap = 'round';
    drawingCtx.lineJoin = 'round';
    rediseñarLienzoPrincipal();
}

function rediseñarLienzoPrincipal() {
    if (canvas.width !== drawingCanvas.width) {
        canvas.width = drawingCanvas.width;
    }
    if (canvas.height !== drawingCanvas.height) {
        canvas.height = drawingCanvas.height;
    }
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(drawingCanvas, 0, 0);
    
    if (floatingImage && mode === 'place_image') {
        ctx.save();
        ctx.globalAlpha = 0.8;
        ctx.drawImage(floatingImage, floatingImageX, floatingImageY);
        ctx.strokeStyle = '#3498db';
        ctx.lineWidth = 2 / scale;
        ctx.strokeRect(floatingImageX, floatingImageY, floatingImage.width, floatingImage.height);
        ctx.restore();
    }

    canvas.style.width = `${drawingCanvas.width}px`;
    canvas.style.height = `${drawingCanvas.height}px`;
    canvas.style.transformOrigin = '0 0';
    canvas.style.transform = `translate(${offsetX}px, ${offsetY}px) scale(${scale})`;
    const spacing = 30;
    canvas.style.backgroundSize = `${spacing}px ${spacing}px`;
    canvas.style.backgroundPosition = '0 0';
}

function resizeCanvas() {
    const width = window.innerWidth - sidebar.offsetWidth;
    const height = window.innerHeight;
    let nuevoAncho = drawingCanvas.width;
    let nuevoAlto = drawingCanvas.height;
    if (nuevoAncho < width) {
        nuevoAncho = width;
    }
    if (nuevoAlto < height) {
        nuevoAlto = height;
    }
    if (nuevoAncho !== drawingCanvas.width || nuevoAlto !== drawingCanvas.height) {
        const temp = document.createElement('canvas');
        temp.width = drawingCanvas.width;
        temp.height = drawingCanvas.height;
        const tempCtx = temp.getContext('2d');
        tempCtx.drawImage(drawingCanvas, 0, 0);
        drawingCanvas.width = nuevoAncho;
        drawingCanvas.height = nuevoAlto;
        drawingCtx.drawImage(temp, 0, 0);
    }
    drawingCtx.lineCap = 'round';
    drawingCtx.lineJoin = 'round';
    if (historyStack.length === 0) {
        saveHistoryState();
    }
    rediseñarLienzoPrincipal();
    updateCursorStyle();
}

window.addEventListener('resize', resizeCanvas);
window.addEventListener('DOMContentLoaded', resizeCanvas);

function getCoordinates(e) {
    const rect = canvas.getBoundingClientRect();
    const containerRect = container.getBoundingClientRect();
    return {
        x: (e.clientX - rect.left) / scale,
        y: (e.clientY - rect.top) / scale,
        rawX: e.clientX - containerRect.left,
        rawY: e.clientY - containerRect.top
    };
}

canvas.addEventListener('contextmenu', e => e.preventDefault());

function startDrawing(e) {
    actualizarInfoPointer(e.pointerType);
    if (mode === 'place_image') {
        confirmarImagenFlotante();
        return;
    }
    if (!activePointers.some(pointer => pointer.pointerId === e.pointerId)) {
        activePointers.push(e);
    }
    if (activePointers.length > 1) {
        isDrawing = false;
        if (activePointers.length === 2) {
            window.lastTouchDistance = null;
        }
        return;
    }
    const coords = getCoordinates(e);
    if (['draw', 'erase', 'line', 'rect'].includes(mode)) {
        if (coords.x < 0 || coords.x > drawingCanvas.width || coords.y < 0 || coords.y > drawingCanvas.height) {
            activePointers = activePointers.filter(pointer => pointer.pointerId !== e.pointerId);
            return;
        }
    }
    isDrawing = true;
    rawLastX = e.clientX;
    rawLastY = e.clientY;
    startX = coords.x;
    startY = coords.y;
    lastX = coords.x;
    lastY = coords.y;
    if (mode === 'draw' || mode === 'erase') {
        draw(e);
    }
}

function draw(e) {
    const index = activePointers.findIndex(pointer => pointer.pointerId === e.pointerId);
    if (index !== -1) {
        activePointers[index] = e;
    }
    if (activePointers.length === 2) {
        handlePinchZoom();
        return;
    }
    const coords = getCoordinates(e);
    if (mode === 'place_image' && floatingImage) {
        floatingImageX = coords.x - (floatingImage.width / 2);
        floatingImageY = coords.y - (floatingImage.height / 2);
        rediseñarLienzoPrincipal();
        return;
    }
    if (mode === 'erase') {
        eraserCursor.style.left = `${coords.rawX}px`;
        eraserCursor.style.top = `${coords.rawY}px`;
    }
    if (!isDrawing) {
        return;
    }
    if (mode === 'pan') {
        offsetX += e.clientX - rawLastX;
        offsetY += e.clientY - rawLastY;
        rawLastX = e.clientX;
        rawLastY = e.clientY;
        rediseñarLienzoPrincipal();
        return;
    }
    if (mode === 'zoom') {
        const dy = e.clientY - rawLastY;
        rawLastX = e.clientX;
        rawLastY = e.clientY;
        adjustZoom(-dy * 0.01, e.clientX, e.clientY);
        return;
    }
    if (e.pointerType === 'pen' && e.pressure === 0) {
        return;
    }
    if (coords.x > drawingCanvas.width - 50 || coords.y > drawingCanvas.height - 50) {
        const anchoAnterior = drawingCanvas.width;
        const altoAnterior = drawingCanvas.height;
        let nuevoAncho = anchoAnterior;
        let nuevoAlto = altoAnterior;
        if (coords.x > anchoAnterior - 50) {
            nuevoAncho = Math.max(anchoAnterior * 1.5, coords.x + 200);
        }
        if (coords.y > altoAnterior - 50) {
            nuevoAlto = Math.max(altoAnterior * 1.5, coords.y + 200);
        }
        const temp = document.createElement('canvas');
        temp.width = anchoAnterior;
        temp.height = altoAnterior;
        temp.getContext('2d').drawImage(drawingCanvas, 0, 0);
        drawingCanvas.width = nuevoAncho;
        drawingCanvas.height = nuevoAlto;
        drawingCtx.lineCap = 'round';
        drawingCtx.lineJoin = 'round';
        drawingCtx.drawImage(temp, 0, 0);
    }
    let currentWidth = parseInt(lineWidthSelect.value);
    if (e.pointerType === 'pen' && e.pressure > 0) {
        currentWidth = currentWidth * e.pressure;
    }
    if (mode === 'line' || mode === 'rect') {
        rediseñarLienzoPrincipal();
        ctx.save();
        ctx.lineWidth = currentWidth;
        ctx.strokeStyle = selectedColor;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.beginPath();
        if (mode === 'line') {
            ctx.moveTo(startX, startY);
            ctx.lineTo(coords.x, coords.y);
            ctx.stroke();
        }
        if (mode === 'rect') {
            ctx.strokeRect(startX, startY, coords.x - startX, coords.y - startY);
        }
        ctx.restore();
        return;
    }
    drawingCtx.save();
    drawingCtx.beginPath();
    drawingCtx.moveTo(lastX, lastY);
    drawingCtx.lineTo(coords.x, coords.y);
    if (mode === 'erase') {
        drawingCtx.lineWidth = currentWidth * 1.6;
        drawingCtx.globalCompositeOperation = 'destination-out';
        drawingCtx.strokeStyle = 'rgba(0,0,0,1)';
    } else {
        drawingCtx.lineWidth = currentWidth;
        drawingCtx.globalCompositeOperation = 'source-over';
        drawingCtx.strokeStyle = selectedColor;
    }
    drawingCtx.stroke();
    drawingCtx.restore();
    emitirTrazo(lastX, lastY, coords.x, coords.y, selectedColor, currentWidth, mode);
    lastX = coords.x;
    lastY = coords.y;
    rawLastX = e.clientX;
    rawLastY = e.clientY;
    rediseñarLienzoPrincipal();
}

function stopDrawing(e) {
    if (isDrawing && (mode === 'line' || mode === 'rect')) {
        const coords = getCoordinates(e);
        let currentWidth = parseInt(lineWidthSelect.value);
        if (e.pointerType === 'pen' && e.pressure > 0) {
            currentWidth = currentWidth * e.pressure;
        }
        drawingCtx.save();
        drawingCtx.lineWidth = currentWidth;
        drawingCtx.strokeStyle = selectedColor;
        drawingCtx.lineCap = 'round';
        drawingCtx.lineJoin = 'round';
        drawingCtx.beginPath();
        if (mode === 'line') {
            drawingCtx.moveTo(startX, startY);
            drawingCtx.lineTo(coords.x, coords.y);
            drawingCtx.stroke();
        }
        if (mode === 'rect') {
            drawingCtx.strokeRect(startX, startY, coords.x - startX, coords.y - startY);
        }
        drawingCtx.restore();
        rediseñarLienzoPrincipal();
    }
    if (isDrawing && ['draw', 'erase', 'line', 'rect'].includes(mode)) {
        saveHistoryState();
    }
    isDrawing = false;
    activePointers = activePointers.filter(pointer => pointer.pointerId !== e.pointerId);
    if (activePointers.length === 0) {
        isDrawing = false;
    }
    if (activePointers.length < 2) {
        window.lastTouchDistance = null;
    }
}

function handlePinchZoom() {
    if (activePointers.length < 2) {
        return;
    }
    const p1 = activePointers[0];
    const p2 = activePointers[1];
    const dx = p1.clientX - p2.clientX;
    const dy = p1.clientY - p2.clientY;
    const distance = Math.sqrt(dx * dx + dy * dy);
    const midX = (p1.clientX + p2.clientX) / 2;
    const midY = (p1.clientY + p2.clientY) / 2;
    if (window.lastTouchDistance) {
        const change = distance / window.lastTouchDistance;
        const zoomFactor = change - 1;
        adjustZoom(zoomFactor, midX, midY);
    }
    window.lastTouchDistance = distance;
}

function adjustZoom(factor, centerX, centerY) {
    const rect = container.getBoundingClientRect();
    const mouseX = centerX - rect.left;
    const mouseY = centerY - rect.top;
    const wheelX = (mouseX - offsetX) / scale;
    const wheelY = (mouseY - offsetY) / scale;
    scale += factor;
    if (scale < 0.15) {
        scale = 0.15;
    }
    if (scale > 7.0) {
        scale = 7.0;
    }
    offsetX = mouseX - wheelX * scale;
    offsetY = mouseY - wheelY * scale;
    zoomDisplay.textContent = `${Math.round(scale * 100)}%`;
    rediseñarLienzoPrincipal();
    updateCursorStyle();
}

container.addEventListener('wheel', (e) => {
    e.preventDefault();
    const intensity = 0.07;
    if (e.deltaY < 0) {
        adjustZoom(intensity, e.clientX, e.clientY);
    } else {
        adjustZoom(-intensity, e.clientX, e.clientY);
    }
});

window.addEventListener('keydown', (e) => {
    const key = e.key;
    if (e.ctrlKey && key.toLowerCase() === 'z') {
        e.preventDefault();
        undo();
        return;
    }
    if (e.ctrlKey && key.toLowerCase() === 'y') {
        e.preventDefault();
        redo();
        return;
    }
    if (key === '1') {
        floatingImage = null;
        mode = 'rect';
        setActiveMode(btnRect);
        tempPreviousMode = null;
        rediseñarLienzoPrincipal();
    } else if (key === '2') {
        floatingImage = null;
        mode = 'line';
        setActiveMode(btnLine);
        tempPreviousMode = null;
        rediseñarLienzoPrincipal();
    } else if (key === '3') {
        floatingImage = null;
        mode = 'zoom';
        setActiveMode(btnZoom);
        tempPreviousMode = null;
        rediseñarLienzoPrincipal();
    } else if (key === '4') {
        imageLoader.click();
    } else if (key === 'Control') {
        if (tempPreviousMode === null && mode !== 'pan') {
            tempPreviousMode = mode;
        }
        floatingImage = null;
        mode = 'pan';
        setActiveMode(btnPan);
        rediseñarLienzoPrincipal();
    } else if (key.toLowerCase() === 'b') {
        floatingImage = null;
        mode = 'erase';
        setActiveMode(btnErase);
        tempPreviousMode = null;
        rediseñarLienzoPrincipal();
    } else if (key.toLowerCase() === 'e') {
        floatingImage = null;
        mode = 'draw';
        setActiveMode(btnDraw);
        tempPreviousMode = null;
        rediseñarLienzoPrincipal();
    }
});

window.addEventListener('keyup', (e) => {
    if (e.key === 'Control' && tempPreviousMode !== null) {
        mode = tempPreviousMode;
        const btnMap = {
            'draw': btnDraw,
            'erase': btnErase,
            'pan': btnPan,
            'zoom': btnZoom,
            'line': btnLine,
            'rect': btnRect
        };
        setActiveMode(btnMap[mode]);
        tempPreviousMode = null;
    }
});

function handleImageFile(file, posX = null, posY = null) {
    if (!file || !file.type.startsWith('image/')) {
        return;
    }
    const reader = new FileReader();
    reader.onload = function(event) {
        const img = new Image();
        img.onload = function() {
            floatingImage = img;
            if (posX === null || posY === null) {
                floatingImageX = (canvas.width / 2 - offsetX) / scale - (img.width / 2);
                floatingImageY = (canvas.height / 2 - offsetY) / scale - (img.height / 2);
            } else {
                floatingImageX = posX;
                floatingImageY = posY;
            }
            mode = 'place_image';
            updateCursorStyle();
            rediseñarLienzoPrincipal();
        };
        img.src = event.target.result;
    };
    reader.readAsDataURL(file);
}

function confirmarImagenFlotante() {
    if (!floatingImage) return;
    let targetX = floatingImageX;
    let targetY = floatingImageY;
    let nuevoAncho = drawingCanvas.width;
    let nuevoAlto = drawingCanvas.height;
    if (targetX + floatingImage.width > nuevoAncho) {
        nuevoAncho = Math.max(drawingCanvas.width * 1.5, targetX + floatingImage.width + 100);
    }
    if (targetY + floatingImage.height > nuevoAlto) {
        nuevoAlto = Math.max(drawingCanvas.height * 1.5, targetY + floatingImage.height + 100);
    }
    if (nuevoAncho !== drawingCanvas.width || nuevoAlto !== drawingCanvas.height) {
        const temp = document.createElement('canvas');
        temp.width = drawingCanvas.width;
        temp.height = drawingCanvas.height;
        temp.getContext('2d').drawImage(drawingCanvas, 0, 0);
        drawingCanvas.width = nuevoAncho;
        drawingCanvas.height = nuevoAlto;
        drawingCtx.drawImage(temp, 0, 0);
        drawingCtx.lineCap = 'round';
        drawingCtx.lineJoin = 'round';
    }
    drawingCtx.drawImage(floatingImage, targetX, targetY);

    const imageDataURL = drawingCanvas.toDataURL('image/png');
    socket.emit('upload_image', {
        x: targetX,
        y: targetY,
        image_data: imageDataURL
    });

    floatingImage = null;
    saveHistoryState();
    rediseñarLienzoPrincipal();
    mode = 'draw';
    setActiveMode(btnDraw);
}

window.addEventListener('paste', (e) => {
    const items = e.clipboardData.items;
    for (let i = 0; i < items.length; i++) {
        if (items[i].type.indexOf('image') !== -1) {
            const blob = items[i].getAsFile();
            const centerLogicalX = (canvas.width / 2 - offsetX) / scale;
            const centerLogicalY = (canvas.height / 2 - offsetY) / scale;
            handleImageFile(blob, centerLogicalX, centerLogicalY);
            e.preventDefault();
            break;
        }
    }
});

container.addEventListener('dragover', (e) => {
    e.preventDefault();
    container.classList.add('drag-over');
});

container.addEventListener('dragleave', () => {
    container.classList.remove('drag-over');
});

container.addEventListener('drop', (e) => {
    e.preventDefault();
    container.classList.remove('drag-over');
    if (e.dataTransfer.files.length === 0) {
        return;
    }
    const rect = canvas.getBoundingClientRect();
    const logicalX = (e.clientX - rect.left) / scale;
    const logicalY = (e.clientY - rect.top) / scale;
    handleImageFile(e.dataTransfer.files[0], logicalX, logicalY);
});

btnImport.addEventListener('click', () => {
    imageLoader.click();
});

imageLoader.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        const centerLogicalX = (canvas.width / 2 - offsetX) / scale;
        const centerLogicalY = (canvas.height / 2 - offsetY) / scale;
        handleImageFile(e.target.files[0], centerLogicalX, centerLogicalY);
        e.target.value = '';
    }
});

btnCustomColor.addEventListener('click', () => {
    colorPicker.click();
});

colorPicker.addEventListener('input', (e) => {
    selectedColor = e.target.value;
    btnCustomColor.style.backgroundColor = selectedColor;
    colorButtons.forEach(button => {
        button.classList.remove('active');
    });
    btnCustomColor.classList.add('active');
    if (mode === 'erase' || mode === 'pan' || mode === 'zoom') {
        mode = 'draw';
        setActiveMode(btnDraw);
    }
});

function limpiarTablero() {
    if (confirm('Limpiar el tablero')) {
        drawingCtx.clearRect(0, 0, drawingCanvas.width, drawingCanvas.height);
        offsetX = 0;
        offsetY = 0;
        scale = 1.0;
        zoomDisplay.textContent = '100%';
        historyStack = [];
        historyIndex = -1;
        saveHistoryState();
        rediseñarLienzoPrincipal();
        socket.emit('clear_board');
    }
}

function guardarComoImagen() {
    const exportCanvas = document.createElement('canvas');
    exportCanvas.width = drawingCanvas.width;
    exportCanvas.height = drawingCanvas.height;
    const exportCtx = exportCanvas.getContext('2d');
    exportCtx.fillStyle = '#1e1e1e';
    exportCtx.fillRect(0, 0, exportCanvas.width, exportCanvas.height);
    exportCtx.drawImage(drawingCanvas, 0, 0);
    const link = document.createElement('a');
    link.download = 'img_tablerito.png';
    link.href = exportCanvas.toDataURL('image/png');
    link.click();
}

function updateCursorStyle() {
    if (mode === 'pan') {
        container.style.cursor = 'grab';
        eraserCursor.style.display = 'none';
    } else if (mode === 'zoom') {
        container.style.cursor = 'zoom-in';
        eraserCursor.style.display = 'none';
    } else if (mode === 'line' || mode === 'rect') {
        container.style.cursor = 'crosshair';
        eraserCursor.style.display = 'none';
    } else if (mode === 'erase') {
        container.style.cursor = 'none';
        const size = parseInt(lineWidthSelect.value) * 1.6 * scale;
        eraserCursor.style.width = `${size}px`;
        eraserCursor.style.height = `${size}px`;
        eraserCursor.style.display = 'block';
    } else if (mode === 'place_image') {
        container.style.cursor = 'move';
        eraserCursor.style.display = 'none';
    } else {
        container.style.cursor = 'crosshair';
        eraserCursor.style.display = 'none';
    }
}

function actualizarInfoPointer(type) {
    const nombres = {
        mouse: "Mouse",
        pen: "Wacom - Lapiz",
        touch: "Tactil-capaz tablet"
    };
    infoPointer.textContent = nombres[type] || type;
}

canvas.addEventListener('pointerdown', startDrawing);
canvas.addEventListener('pointermove', draw);
canvas.addEventListener('pointerup', stopDrawing);
canvas.addEventListener('pointercancel', stopDrawing);
canvas.addEventListener('pointerleave', (e) => {
    if (e.pointerType === 'mouse') {
        stopDrawing(e);
    }
});

lineWidthSelect.addEventListener('change', () => {
    updateCursorStyle();
    const size = parseInt(lineWidthSelect.value) * 1.6 * scale;
    eraserCursor.style.width = `${size}px`;
    eraserCursor.style.height = `${size}px`;
});

btnDraw.addEventListener('click', () => { 
    floatingImage = null;
    mode = 'draw'; 
    setActiveMode(btnDraw); 
    rediseñarLienzoPrincipal();
});

btnLine.addEventListener('click', () => { 
    floatingImage = null;
    mode = 'line'; 
    setActiveMode(btnLine); 
    rediseñarLienzoPrincipal();
});

btnRect.addEventListener('click', () => { 
    floatingImage = null;
    mode = 'rect'; 
    setActiveMode(btnRect); 
    rediseñarLienzoPrincipal();
});

btnErase.addEventListener('click', () => { 
    floatingImage = null;
    mode = 'erase'; 
    setActiveMode(btnErase); 
    rediseñarLienzoPrincipal();
});

btnPan.addEventListener('click', () => { 
    floatingImage = null;
    mode = 'pan'; 
    setActiveMode(btnPan); 
    rediseñarLienzoPrincipal();
});

btnZoom.addEventListener('click', () => { 
    floatingImage = null;
    mode = 'zoom'; 
    setActiveMode(btnZoom); 
    rediseñarLienzoPrincipal();
});

btnUndo.addEventListener('click', undo);
btnRedo.addEventListener('click', redo);
btnSave.addEventListener('click', guardarComoImagen);
btnClear.addEventListener('click', limpiarTablero);

function setActiveMode(activeButton) {
    const botones = [btnDraw, btnLine, btnRect, btnErase, btnPan, btnZoom];
    botones.forEach(btn => btn.classList.remove('active'));
    activeButton.classList.add('active');
    updateCursorStyle();
}

colorButtons.forEach(button => {
    if (button.id === 'btn-custom-color') {
        return;
    }
    button.addEventListener('click', (e) => {
        colorButtons.forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        selectedColor = e.target.getAttribute('data-color');
        if (mode === 'erase' || mode === 'pan' || mode === 'zoom') {
            mode = 'draw';
            setActiveMode(btnDraw);
        }
    });
});

function actualizarBarra(hacerCompacta) {
    if (hacerCompacta) {
        sidebar.classList.add('compact');
    } else {
        sidebar.classList.remove('compact');
    }
    resizeCanvas();
}

sidebar.addEventListener('pointerenter', () => {
    actualizarBarra(false);
});

sidebar.addEventListener('pointerleave', () => {
    actualizarBarra(true);
});

resizeCanvas();
setActiveMode(btnDraw);

const socket = io();

function emitirTrazo(x1, y1, x2, y2, color, width, mode) {
    socket.emit('draw_line', { x1, y1, x2, y2, color, width, mode });
}

socket.on('draw_line', (data) => {
    drawingCtx.save();
    drawingCtx.beginPath();
    drawingCtx.moveTo(data.x1, data.y1);
    drawingCtx.lineTo(data.x2, data.y2);
    if (data.mode === 'erase') {
        drawingCtx.lineWidth = data.width * 1.6;
        drawingCtx.globalCompositeOperation = 'destination-out';
        drawingCtx.strokeStyle = 'rgba(0,0,0,1)';
    } else {
        drawingCtx.lineWidth = data.width;
        drawingCtx.globalCompositeOperation = 'source-over';
        drawingCtx.strokeStyle = data.color;
    }
    drawingCtx.stroke();
    drawingCtx.restore();
    rediseñarLienzoPrincipal();
});

socket.on('clear_board', () => {
    drawingCtx.clearRect(0, 0, drawingCanvas.width, drawingCanvas.height);
    rediseñarLienzoPrincipal();
});

socket.on('upload_image', (data) => {
    const img = new Image();
    img.onload = function() {
        drawingCtx.drawImage(img, data.x, data.y);
        rediseñarLienzoPrincipal();
    };
    img.src = data.image_data;
});