from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
import os

app = FastAPI()

# Crear carpetas si no existen
os.makedirs("static", exist_ok=True)
os.makedirs("data", exist_ok=True)

# Servir archivos estáticos (HTML, JS, CSS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Gestor de conexiones para el grupo en tiempo real
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.ultimas_posiciones: dict = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Enviar las posiciones actuales del grupo al recién conectado
        await websocket.send_json({"type": "INIT_POSITIONS", "data": self.ultimas_posiciones})

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_location(self, user_data: dict):
        user_id = user_data.get("user_id")
        if user_id:
            self.ultimas_posiciones[user_id] = user_data
            
        # Reenviar posición a todos los conectados en la red
        for connection in self.active_connections:
            await connection.send_json({"type": "UPDATE_LOCATION", "data": user_data})

manager = ConnectionManager()

@app.get("/")
async def get_index():
    return FileResponse("static/index.html")

@app.get("/api/sofa-data")
async def get_sofa_data():
    if os.path.exists("data/sofa_data.json"):
        with open("data/sofa_data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {"error": "Datos no encontrados. Ejecuta scraper_sofa.py primero."}

@app.websocket("/ws/geoloc")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data_str = await websocket.receive_text()
            data = json.loads(data_str)
            await manager.broadcast_location(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)