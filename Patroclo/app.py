import os
import shutil
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

LOGS = Path("logs")
LOGS.mkdir(exist_ok=True)

@app.route("/")
def index():
    # Detecta el usu 
    default_origen = str(Path.home() / "Downloads")
    default_destino = str(Path.home() / "Patroclo")
    
    return render_template("index.html", default_origen=default_origen, default_destino=default_destino)

@app.route("/api/organizar", methods=["POST"])
def organizar():
    data = request.json
    src = data.get("origen")
    dst = data.get("destino")
    
    if not src or not dst:
        return jsonify({"status": "error", "message": "Faltan rutas"}), 400

    try:
        src_path = Path(src).expanduser().resolve()
        dst_path = Path(dst).expanduser().resolve()

        if not src_path.exists():
            return jsonify({"status": "error", "message": "El origen no existe"}), 400

        # Backup 
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = src_path.parent / f"backup_{ts}"
        backup.mkdir(exist_ok=True)

        files = [f for f in src_path.rglob('*') if f.is_file() and not f.name.startswith('.')]

        if not files:
            shutil.rmtree(backup, ignore_errors=True)
            return jsonify({"status": "error", "message": "No hay archivos para ordenar"}), 400

        for f in files:
            rel = f.relative_to(src_path)
            dest_backup = backup / rel
            dest_backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dest_backup)

        shutil.make_archive(str(backup), 'zip', backup)
        shutil.rmtree(backup)

        files.sort(key=lambda x: x.name.lower())

        log_file = LOGS / f"log_{ts}.txt"
        log_data = [f"Log organizacion - {ts}", f"Origen: {src_path}", f"Destino: {dst_path}", "-"*30]

        dst_path.mkdir(exist_ok=True, parents=True)
        count = 0

        for f in files:
            ext = f.suffix[1:].upper() if f.suffix else "OTROS"
            target_dir = dst_path / ext
            target_dir.mkdir(exist_ok=True)

            final_path = target_dir / f.name
            i = 1
            while final_path.exists():
                final_path = target_dir / f"{f.stem}_{i}{f.suffix}"
                i += 1

            shutil.move(str(f), str(final_path))
            log_data.append(f"Movido: {f.name} -> {ext}/")
            count += 1

        # Limpiar carpetas vacias
        for p in sorted(src_path.rglob('*'), reverse=True):
            if p.is_dir() and p != src_path:
                try:
                    p.rmdir()
                except:
                    pass

        log_file.write_text("\n".join(log_data), encoding="utf-8")

        return jsonify({
            "status": "success",
            "message": f"Listo, {count} archivos ordenados.",
            "log_file": log_file.name
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/logs", methods=["GET"])
def get_logs():
    logs = [f.name for f in LOGS.glob("*.txt")]
    return jsonify(sorted(logs, reverse=True))

@app.route("/api/logs/<filename>", methods=["GET"])
def get_log(filename):
    f_path = LOGS / filename
    if f_path.exists():
        return jsonify({"content": f_path.read_text(encoding="utf-8")})
    return jsonify({"error": "No encontrado"}), 404

if __name__ == "__main__":
    app.run(debug=True, port=5000)