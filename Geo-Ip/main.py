import os
import asyncio
import socket
import re
from urllib.parse import urlparse
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx

app = FastAPI(title="KIGN // OSINT Command Center")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@app.get("/")
async def read_index(request: Request):
    return templates.TemplateResponse(request, "index.html", {})

@app.get("/api/geo/reverse")
async def reverse_geocode(lat: float, lon: float):
    """Consulta la dirección aproximada y la zona horaria real basada en coordenadas."""
    try:
        async with httpx.AsyncClient() as client:
            headers = {"User-Agent": "KignOSINTCenter/4.7"}
            resp = await client.get(f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}", headers=headers, timeout=5.0)
            data = resp.json()
            display_name = data.get("display_name", "Zona Operativa Desconocida / Área Remota")
            
            offset_hours = round(lon / 15.0)
            sign = "+" if offset_hours >= 0 else ""
            timezone = f"UTC {sign}{offset_hours}.0"

            return JSONResponse(content={
                "address": display_name,
                "timezone": timezone
            })
    except:
        return JSONResponse(content={
            "address": f"Lat: {lat}, Lng: {lon} (Sin conexión a pasarela inversa)",
            "timezone": "UTC +0.0"
        })

def limpiar_stdout_terminal(texto_crudo):
    """Elimina barras de progreso dinámicas, spinners y códigos ANSI para conservar el reporte puro."""
    if not texto_crudo:
        return ""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    texto = ansi_escape.sub('', texto_crudo)
    
    lineas_limpias = []
    for linea in texto.splitlines():
        if any(k in linea for k in ["Searching |", "Checking username", "%]", "/", "Progress:"]):
            continue
        lineas_limpias.append(linea)
    return "\n".join(lineas_limpias)

async def ejecutar_subproceso(cmd, timeout_sec=180, cwd=None):
    """Ejecuta comandos CLI de forma asíncrona con manejo de timeouts y directorio de trabajo."""
    try:
        proceso = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd
        )
        stdout, stderr = await asyncio.wait_for(proceso.communicate(), timeout=timeout_sec)
        output = stdout.decode("utf-8", errors="ignore") + stderr.decode("utf-8", errors="ignore")
        return output
    except asyncio.TimeoutError:
        try:
            proceso.kill()
        except:
            pass
        return "[!] Error: El subproceso superó el tiempo límite de espera."
    except Exception as e:
        return f"[!] Error crítico ejecutando comando: {str(e)}"


@app.post("/api/escanear")
async def escanear_objetivo(request: Request):
    data = await request.json()
    
    ip = data.get("ip", "").strip()
    email = data.get("email", "").strip()
    username = data.get("usuario", "").strip()
    url = data.get("url", "").strip()

    hallazgos = []
    recon_dict = {"ip": ip or "N/A", "ubi": "N/A", "pais": "N/A", "isp": "N/A"}
    lat, lon = None, None
    ports_list = []
    detected_images = []
    reputacion_ip = "NEUTRAL / LIMPIA"

    # 1. Análisis de IP (Geolocalización + Reputación + Puertos TCP)
    if ip:
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,lat,lon,isp,as,query,hosting,proxy", timeout=5.0)
                geo = resp.json()
                if geo.get("status") != "fail":
                    lat, lon = geo.get("lat"), geo.get("lon")
                    recon_dict["ip"] = geo.get("query")
                    recon_dict["ubi"] = geo.get("city")
                    recon_dict["pais"] = geo.get("country")
                    recon_dict["isp"] = geo.get("isp")
                    
                    if geo.get("hosting", False) or geo.get("proxy", False):
                        reputacion_ip = " HOSTING / DATACENTER (Posible VPN/Proxy)"
                    else:
                        reputacion_ip = "🟢 ISP RESIDENCIAL / CORPORATIVO"

                    hallazgos.append({
                        "tool": "Geo-Intelligence",
                        "categoria": "Geolocalización IP",
                        "objetivo": ip,
                        "valor": f"Ubicación: {geo.get('city')}, {geo.get('country')} ({lat}, {lon}) [Reputación: {reputacion_ip}]",
                        "metadata": f"ISP: {geo.get('isp')}",
                        "url": f"https://maps.google.com/?q={lat},{lon}"
                    })
            except:
                pass

        for p in [21, 22, 25, 53, 80, 443, 3306, 8080]:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.2)
                if s.connect_ex((ip, p)) == 0:
                    ports_list.append({"port": p, "state": "OPEN", "service": "TCP"})
                s.close()
            except:
                pass

    # 2. Análisis de Correo (Holehe + Maigret)
    if email:
        stdout_holehe = await ejecutar_subproceso(["holehe", email, "--no-color"], timeout_sec=20)
        reporte_holehe = limpiar_stdout_terminal(stdout_holehe)
        hallazgos.append({
            "tool": "Identity Registry",
            "categoria": "Registro de Correo",
            "objetivo": email,
            "valor": reporte_holehe.strip(),
            "metadata": "Reporte CLI Completo",
            "url": "#"
        })

        stdout_maigret = await ejecutar_subproceso(["maigret", email, "--no-color", "--timeout", "4"], timeout_sec=60)
        reporte_mg_email = limpiar_stdout_terminal(stdout_maigret)
        hallazgos.append({
            "tool": "Digital Footprint",
            "categoria": "Footprint (Email)",
            "objetivo": email,
            "valor": reporte_mg_email.strip(),
            "metadata": "Reporte CLI Completo",
            "url": "#"
        })
        for line in reporte_mg_email.splitlines():
            if "http://" in line or "https://" in line:
                parts = line.split()
                url_match = [p for p in parts if p.startswith("http://") or p.startswith("https://")]
                if url_match:
                    detected_images.append(url_match[0].strip("[]()"))

    # 3. Análisis de Usuario (Maigret + Sherlock con timeout extendido de 3 min)
    if username:
        stdout_maigret = await ejecutar_subproceso(["maigret", username, "--no-color", "--timeout", "5"], timeout_sec=180)
        reporte_mg = limpiar_stdout_terminal(stdout_maigret)
        hallazgos.append({
            "tool": "Digital Footprint",
            "categoria": "Social Media (User)",
            "objetivo": username,
            "valor": reporte_mg.strip(),
            "metadata": "Dossier CLI Completo",
            "url": "#"
        })

        stdout_sherlock = await ejecutar_subproceso(["sherlock", username, "--no-color", "--timeout", "5"], timeout_sec=90)
        reporte_sh = limpiar_stdout_terminal(stdout_sherlock)
        hallazgos.append({
            "tool": "Profile Scanner",
            "categoria": "Social Media (User)",
            "objetivo": username,
            "valor": reporte_sh.strip(),
            "metadata": "Reporte de Perfiles",
            "url": "#"
        })

        # Extracción pasiva de avatares/imágenes desde el texto crudo
        for text_output in [reporte_mg, reporte_sh]:
            for line in text_output.splitlines():
                if "http://" in line or "https://" in line or "image:" in line:
                    parts = line.split()
                    url_match = [p for p in parts if p.startswith("http://") or p.startswith("https://")]
                    if url_match:
                        link = url_match[0].strip("[]()")
                        if "g.co" not in link and "patreon" not in link:
                            detected_images.append(link)

    # 4. Análisis de URL / Dominio (Photon + theHarvester usando sus propios venvs locales)
    if url:
        target_url = url if url.startswith("http") else f"https://{url}"
        parsed = urlparse(target_url)
        domain = parsed.netloc or url
        
        # 1. Ejecutar Photon
        photon_python = os.path.expanduser("~/tools/Photon/venv/bin/python")
        photon_script = os.path.expanduser("~/tools/Photon/photon.py")
        
        stdout_photon = await ejecutar_subproceso([photon_python, photon_script, "-u", target_url, "--level", "1"], timeout_sec=30)
        reporte_photon = limpiar_stdout_terminal(stdout_photon)

        hallazgos.append({
            "tool": "Photon",
            "categoria": "Web Crawler",
            "objetivo": domain,
            "valor": reporte_photon.strip() if reporte_photon.strip() else "[!] Photon ejecutado sin salida.",
            "metadata": "Reporte Local venv",
            "url": target_url
        })

        # 2. Ejecutar theHarvester llamando a su script interno directamente desde su venv
        harvester_python = os.path.expanduser("~/tools/theHarvester/venv/bin/python")
        harvester_script = os.path.expanduser("~/tools/theHarvester/theHarvester/theHarvester.py")
        harvester_dir = os.path.expanduser("~/tools/theHarvester")
        
        stdout_harvester = await ejecutar_subproceso(
            [harvester_python, harvester_script, "-d", domain, "-b", "all", "-l", "30"], 
            timeout_sec=45, 
            cwd=harvester_dir
        )
        reporte_harvester = limpiar_stdout_terminal(stdout_harvester)

        hallazgos.append({
            "tool": "theHarvester",
            "categoria": "Domain Recon",
            "objetivo": domain,
            "valor": reporte_harvester.strip() if reporte_harvester.strip() else "[!] theHarvester ejecutado sin salida.",
            "metadata": "Reporte Local venv",
            "url": target_url
        })

    telemetria = {
        "coords": f"{lat}, {lon}" if lat and lon else "N/A",
        "lat": lat,
        "lng": lon,
        "ciudad": recon_dict["ubi"],
        "pais": recon_dict["pais"],
        "isp": recon_dict["isp"],
        "ip": ip or "N/A",
        "reputacion": reputacion_ip,
        "images": list(set(detected_images))[:15]
    }

    return JSONResponse(content={
        "status": "success",
        "recon": recon_dict,
        "ports": ports_list,
        "hallazgos": hallazgos,
        "telemetria": telemetria
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)