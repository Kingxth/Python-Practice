import platform
import subprocess
import re
import datetime
import time
import threading
import os
import sys

# Un Lock para evitar problemas de concurrencia 
lock = threading.Lock()

def saber_os():
    return platform.system().lower()

def enel_cmd(comando):
    res = subprocess.run(comando, capture_output=True, text=True, shell=True)
    return res.stdout

def donde_donde():
    so = saber_os()
    if "windows" in so:
        out = enel_cmd("ipconfig")
        for linea in out.splitlines():
            if "Default Gateway" in linea or "Puerta de enlace predeterminada" in linea:
                trozos = linea.split(":")
                if len(trozos) > 1:
                    gw = trozos[1].strip()
                    if gw and "." in gw:
                        m = re.search(r"(\d+\.\d+\.\d+)\.\d+", gw)
                        if m:
                            return m.group(1) + ".0/24"
    else:
        out = enel_cmd("ip route show | grep default")
        m = re.search(r"via (\d+\.\d+\.\d+)\.\d+", out)
        if m:
            return m.group(1) + ".0/24"
    return "192.168.1.0/24"

def buscar_nombre(ip):
    try:
        r = subprocess.run(["nslookup", ip], capture_output=True, text=True, timeout=2)
        for l in r.stdout.splitlines():
            if "Name:" in l or "nombre:" in l.lower():
                return l.split(":")[-1].strip()
    except Exception:
        pass
    return "Desconocido"

def leer_nmap(salida):
    dispos = {}
    bloques = salida.split("Nmap scan report for ")
    for bloque in bloques[1:]:
        lineas = bloque.splitlines()
        p_linea = lineas[0].strip()
        ip = ""
        nombre = "Desconocido"
        if "(" in p_linea and ")" in p_linea:
            partes = p_linea.split("(")
            nombre = partes[0].strip()
            ip = partes[1].replace(")", "").strip()
        else:
            ip = p_linea
            
        mac = "Desconocida"
        for l in lineas:
            if "MAC Address:" in l:
                partes_mac = l.split("MAC Address:")
                if len(partes_mac) > 1:
                    m_info = partes_mac[1].strip().split()
                    mac = m_info[0].lower()
                    if len(m_info) > 1 and "(" in m_info[1]:
                        fab = " ".join(m_info[1:]).replace("(", "").replace(")", "")
                        nombre = f"{nombre} ({fab})" if nombre != "Desconocido" else fab

        if ip:
            if nombre == "Desconocido":
                nombre = buscar_nombre(ip)
            dispos[ip] = {"mac": mac, "nombre": nombre}
    return dispos

def escanear():
    subred = donde_donde()
    salida = enel_cmd(f"nmap -PR -sn {subred}")
    return leer_nmap(salida)

def ver_estado(devices):
    with lock:
        print("\n--- ESTADO ACTUAL DE LA RED ---")
        conectados = [(k, v) for k, v in devices.items() if v["estado"] == "Conectado"]
        if not conectados:
            print("Sin conexiones activas")
        else:
            for ip, datos in conectados:
                print(f"IP: {ip}")
                print(f"  Nombre: {datos['nombre']}")
                print(f"  MAC: {datos['mac']}")
                print(f"  Estado: {datos['estado']}")
                print(f"  Ultima vez activo: {datos['ultima_conexion']}")

        print("\n--- DESCONECTADOS ---")
        desconectados = [(k, v) for k, v in devices.items() if v["estado"] == "Desconectado"]
        if not desconectados:
            print("Sin dispositivos desconectados")
        else:
            for ip, datos in desconectados:
                print(f"IP: {ip}")
                print(f"  Nombre: {datos['nombre']}")
                print(f"  MAC: {datos['mac']}")
                print(f"  Estado: {datos['estado']}")
                print(f"  Ultima vez activo: {datos['ultima_conexion']}")
        print("-" * 30)

def loop_fondo(devices):
    primera_ronda = True
    while True:
        tiempo_inicio_escaneo = datetime.datetime.now()
        activos = escanear()
        ahora = tiempo_inicio_escaneo.strftime("%Y-%m-%d %H:%M:%S")

        with lock:
            for ip, info in activos.items():
                if ip not in devices:
                    devices[ip] = {
                        "mac": info["mac"],
                        "nombre": info["nombre"],
                        "primera_conexion": ahora,
                        "ultima_conexion": ahora,
                        "estado": "Conectado",
                        "intentos_perdidos": 0
                    }
                    if not primera_ronda:
                        print(f"\n[ALERTA NUEVA IP] IP: {ip} | Nombre: {info['nombre']} | MAC: {info['mac']}")
                else:
                    if devices[ip]["estado"] == "Desconectado" and not primera_ronda:
                        print(f"\n[ALERTA RECONEXION] IP: {ip} | Nombre: {devices[ip]['nombre']}")
                    
                    devices[ip]["ultima_conexion"] = ahora
                    devices[ip]["estado"] = "Conectado"
                    devices[ip]["intentos_perdidos"] = 0
                    if devices[ip]["nombre"] == "Desconocido" and info["nombre"] != "Desconocido":
                        devices[ip]["nombre"] = info["nombre"]

            # verificacion de desconectados
            for ip in list(devices.keys()):
                if ip not in activos and devices[ip]["estado"] == "Conectado":
                    devices[ip]["intentos_perdidos"] += 1
                    if devices[ip]["intentos_perdidos"] >= 3:
                        devices[ip]["estado"] = "Desconectado"
                        devices[ip]["ultima_conexion"] = ahora
                        if not primera_ronda:
                            print(f"\n[ALERTA DESCONEXION] IP: {ip} | Nombre: {devices[ip]['nombre']}")

        primera_ronda = False
        time.sleep(30)

def descargar_reporte(devices):
    with lock:
        print("\n--- MENU REPORTE ---")
        print("1. Solo conectados")
        print("2. Todos (conectados y desconectados)")
        op = input("Elige: ").strip()

        if not os.path.exists("reports"):
            os.makedirs("reports")

        sufijo = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        f_path = os.path.join("reports", f"reporte_deRed_{sufijo}.txt")

        with open(f_path, "w", encoding="utf-8") as f:
            f.write("REPORTE DE RED DETALLADO\n")
            f.write("=" * 40 + "\n")
            for ip, datos in devices.items():
                if op == "1" and datos["estado"] != "Conectado":
                    continue
                f.write(f"IP: {ip}\n")
                f.write(f"Nombre: {datos['nombre']}\n")
                f.write(f"MAC: {datos['mac']}\n")
                f.write(f"Primera vez visto: {datos['primera_conexion']}\n")
                f.write(f"Ultima vez activo: {datos['ultima_conexion']}\n")
                f.write(f"Estado: {datos['estado']}\n")
                f.write("-" * 40 + "\n")

        print(f"Guardado en: {f_path}")

def main():
    devices = {}
    print("Escaneando red de entrada...")
    iniciales = escanear()
    ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with lock:
        for ip, info in iniciales.items():
            devices[ip] = {
                "mac": info["mac"],
                "nombre": info["nombre"],
                "primera_conexion": ahora,
                "ultima_conexion": ahora,
                "estado": "Conectado",
                "intentos_perdidos": 0
            }

    hilo = threading.Thread(target=loop_fondo, args=(devices,), daemon=True)
    hilo.start()
    print("Monitoreo en segundo plano...")

    while True:
        print("\n=== MENU PRINCIPAL ===")
        print("1. Ver dispositivos")
        print("2. Descargar reporte")
        print("3. Salir")
        resp = input("Opcion: ").strip()

        if resp == "1":
            ver_estado(devices)
        elif resp == "2":
            descargar_reporte(devices)
        elif resp == "3":
            print("Saliendo...")
            sys.exit(0)
        else:
            print("Opcion invalida")

if __name__ == "__main__":
    main()