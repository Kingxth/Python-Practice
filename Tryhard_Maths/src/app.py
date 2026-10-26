from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response
from werkzeug.security import generate_password_hash, check_password_hash
import random
import sqlite3
from calculos import generar_operacion
from database import init_db, get_db_connection

app = Flask(__name__, 
            static_folder='static', 
            template_folder='templates')
            
app.secret_key = 'tu_clave_secreta'

with app.app_context():
    init_db()
    conn = get_db_connection()
    admin = conn.execute("SELECT id FROM usuarios WHERE username = 'profesor'").fetchone()
    if not admin:
        hashed_pw = generate_password_hash('admin123')
        conn.execute(
            "INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?)",
            ('profesor', hashed_pw, 'profesor')
        )
        conn.commit()
    conn.close()


@app.route('/register', methods=['POST'])
def register():
    data = request.json if request.is_json else request.form
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    rol = data.get('rol', 'estudiante')
    
    if not username or not password:
        if request.is_json:
            return jsonify({"status": "error", "message": "Faltan datos"}), 400
        return "Faltan datos", 400
        
    hashed_pw = generate_password_hash(password)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?)",
            (username, hashed_pw, rol)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        session['usuario_id'] = user_id
        session['username'] = username
        session['rol'] = rol
        
        if request.is_json:
            return jsonify({"status": "success"})
        return redirect(url_for('home'))
        
    except sqlite3.IntegrityError:
        if request.is_json:
            return jsonify({"status": "error", "message": "El usuario ya existe"}), 400
        return "El usuario ya existe", 400

        
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json if request.is_json else request.form
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM usuarios WHERE username = ?", (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['usuario_id'] = user['id']
            session['username'] = user['username']
            session['rol'] = user['rol']
            return jsonify({"status": "success", "rol": user['rol']}) if request.is_json else redirect(url_for('home'))
        
        return jsonify({"status": "error", "message": "Credenciales inválidas"}), 401
        
    return render_template('login.html')



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# General 

@app.route('/')
def home():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', username=session.get('username'), rol=session.get('rol'))

@app.route('/iniciar_juego', methods=['POST'])
def iniciar_juego():
    if 'usuario_id' not in session:
        return jsonify({"status": "unauthorized"}), 401
        
    data = request.json
    session['ops_disponibles'] = data.get('operaciones')
    
    session['racha_actual'] = 0
    session['max_racha_partida'] = 0
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO partidas (usuario_id, modo, tiempo_total_seg, score_final, max_racha) VALUES (?, ?, 0, 0, 0)",
        (session['usuario_id'], 'clasico')
    )
    conn.commit()
    session['partida_id'] = cursor.lastrowid
    conn.close()
    
    return jsonify({"status": "ok"})

@app.route('/iniciar_juego_tablero', methods=['POST'])
def iniciar_juego_tablero():
    if 'usuario_id' not in session:
        return jsonify({"status": "unauthorized"}), 401
        
    data = request.json
    session['ops_disponibles'] = data.get('operaciones')
    
    session['racha_actual'] = 0
    session['max_racha_partida'] = 0
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO partidas (usuario_id, modo, tiempo_total_seg, score_final, max_racha) VALUES (?, ?, 0, 0, 0)",
        (session['usuario_id'], 'tablero')
    )
    conn.commit()
    session['partida_id'] = cursor.lastrowid
    conn.close()
    
    return jsonify({"status": "ok"})


@app.route('/guardar_config', methods=['POST'])
def guardar_config():
    session['config_dificultades'] = request.json
    return jsonify({"status": "ok"})

@app.route('/obtener_config_dificultades')
def obtener_config():
    return jsonify(session.get('config_dificultades', {}))

@app.route('/tablero')
def tablero():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('tablero.html')

@app.route('/guardar_partida', methods=['POST'])
def guardar_partida():
    data = request.json
    tiempo_total = data.get('tiempo_total', 0)
    partida_id = session.get('partida_id')
    max_racha_final = session.get('max_racha_partida', 0)
    
    if partida_id:
        conn = get_db_connection()
        conn.execute(
            "UPDATE partidas SET tiempo_total_seg = ?, max_racha = ? WHERE id = ?",
            (tiempo_total, max_racha_final, partida_id)
        )
        conn.commit()
        conn.close()
        
    return jsonify({"status": "success"})

@app.route('/obtener_pregunta')
def obtener_pregunta():
    if 'usuario_id' not in session:
        return jsonify({"status": "unauthorized"}), 401
    tipo_solicitado = request.args.get('tipo')
    if tipo_solicitado:
        tipo = tipo_solicitado
    else:
        tipo = random.choice(session.get('ops_disponibles', ['suma']))
        
    dif = session.get('dificultad_actual', session.get('config_dificultades', {}).get(tipo, 'facil'))
    
    pregunta, solucion, subtema = generar_operacion(tipo, dif)
    session['solucion_actual'] = str(solucion)
    session['tipo_actual'] = tipo  
    session['subtema_actual'] = subtema  
    session['pregunta_actual'] = pregunta
    
    return jsonify({
        "pregunta": pregunta,
        "tipo": tipo,
        "dificultad_actual": dif
    })

    def obtener_resumen_nivel(nivel_str):
        # Partidas/intentos/usu
        ops_raw = conn.execute('''
            SELECT 
                tipo_operacion as nombre,
                SUM(es_correcto) * 100.0 / COUNT(*) as porcentaje_habilidad,
                SUM(es_correcto) as aciertos,
                SUM(CASE WHEN es_correcto = 0 THEN 1 ELSE 0 END) as fallos,
                ROUND(AVG(tiempo_respuesta_ms) / 1000.0, 2) as tiempo_promedio
            FROM intentos 
            WHERE usuario_id = ? AND dificultad = ?
            GROUP BY tipo_operacion
        ''', (usuario_id, nivel_str)).fetchall()
        
        operaciones = [dict(row) for row in ops_raw]
        
        # Calcular porcentaje global
        total_ops = sum(op['aciertos'] + op['fallos'] for op in operaciones)
        total_aciertos_nivel = sum(op['aciertos'] for op in operaciones)
        porcentaje_global = round((total_aciertos_nivel / total_ops * 100), 1) if total_ops > 0 else 0
        
        return {
            "partidas": len(operaciones),
            "porcentaje_global": porcentaje_global,
            "operaciones": operaciones
        }

    resumen_facil = obtener_resumen_nivel('facil')
    resumen_medio = obtener_resumen_nivel('medio')
    resumen_dificil = obtener_resumen_nivel('dificil')


    def obtener_resumen_nivel(nivel_str):
        return {
            "partidas": 0,
            "porcentaje_global": 0,
            "operaciones": []
        }

    resumen_facil = obtener_resumen_nivel('facil')
    resumen_medio = obtener_resumen_nivel('medio')
    resumen_dificil = obtener_resumen_nivel('dificil')
    
    conn.close()
    
    return render_template(
        'dashboard.html',
        username=session.get('username'),
        total_intentos=total_intentos,
        porcentaje_acierto=porcentaje_acierto,
        tiempo_promedio_seg=tiempo_promedio_seg,
        partidas_jugadas=partidas_jugadas,
        max_racha_historica=max_racha_historica,
        desglose=desglose,
        historial_partidas=historial_partidas,
        resumen_facil=resumen_facil,
        resumen_medio=resumen_medio,
        resumen_dificil=resumen_dificil
    )
@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
        
    usuario_id = session['usuario_id']
    conn = get_db_connection()
    
    stats_generales = conn.execute('''
        SELECT 
            COUNT(*) as total_intentos,
            SUM(es_correcto) as total_aciertos,
            AVG(tiempo_respuesta_ms) as tiempo_promedio_ms
        FROM intentos 
        WHERE usuario_id = ?
    ''', (usuario_id,)).fetchone()
    
    total_intentos = stats_generales['total_intentos'] or 0
    total_aciertos = stats_generales['total_aciertos'] or 0
    
    porcentaje_acierto = round((total_aciertos / total_intentos * 100), 1) if total_intentos > 0 else 0
    tiempo_promedio_seg = round((stats_generales['tiempo_promedio_ms'] or 0) / 1000, 2)
    
    partidas_jugadas = conn.execute('''
        SELECT COUNT(*) as total FROM partidas WHERE usuario_id = ?
    ''', (usuario_id,)).fetchone()['total']

    max_racha_historica = conn.execute('''
        SELECT MAX(max_racha) as max_racha FROM partidas WHERE usuario_id = ?
    ''', (usuario_id,)).fetchone()['max_racha'] or 0
    
    desglose_raw = conn.execute('''
        SELECT 
            tipo_operacion,
            COUNT(*) as total,
            SUM(es_correcto) as aciertos,
            ROUND(AVG(tiempo_respuesta_ms) / 1000.0, 2) as tiempo_promedio_seg
        FROM intentos 
        WHERE usuario_id = ?
        GROUP BY tipo_operacion
    ''', (usuario_id,)).fetchall()
    
    desglose = [dict(row) for row in desglose_raw]

    partidas_raw = conn.execute('''
        SELECT id, modo, tiempo_total_seg, score_final, max_racha, fecha
        FROM partidas 
        WHERE usuario_id = ?
        ORDER BY fecha DESC
        LIMIT 10
    ''', (usuario_id,)).fetchall()
    
    historial_partidas = [dict(row) for row in partidas_raw]

    def obtener_resumen_nivel(nivel_str):
        ops_raw = conn.execute('''
            SELECT 
                tipo_operacion as nombre,
                SUM(es_correcto) * 100.0 / COUNT(*) as porcentaje_habilidad,
                SUM(es_correcto) as aciertos,
                SUM(CASE WHEN es_correcto = 0 THEN 1 ELSE 0 END) as fallos,
                ROUND(AVG(tiempo_respuesta_ms) / 1000.0, 2) as tiempo_promedio
            FROM intentos 
            WHERE usuario_id = ? AND dificultad = ?
            GROUP BY tipo_operacion
        ''', (usuario_id, nivel_str)).fetchall()
        
        operaciones = [dict(row) for row in ops_raw]
        
        total_ops = sum(op['aciertos'] + op['fallos'] for op in operaciones)
        total_aciertos_nivel = sum(op['aciertos'] for op in operaciones)
        porcentaje_global = round((total_aciertos_nivel / total_ops * 100), 1) if total_ops > 0 else 0
        
        return {
            "partidas": len(operaciones),
            "porcentaje_global": porcentaje_global,
            "operaciones": operaciones
        }

    resumen_facil = obtener_resumen_nivel('facil')
    resumen_medio = obtener_resumen_nivel('medio')
    resumen_dificil = obtener_resumen_nivel('dificil')
    
    conn.close()
    
    return render_template(
        'dashboard.html',
        username=session.get('username'),
        total_intentos=total_intentos,
        porcentaje_acierto=porcentaje_acierto,
        tiempo_promedio_seg=tiempo_promedio_seg,
        partidas_jugadas=partidas_jugadas,
        max_racha_historica=max_racha_historica,
        desglose=desglose,
        historial_partidas=historial_partidas,
        resumen_facil=resumen_facil,
        resumen_medio=resumen_medio,
        resumen_dificil=resumen_dificil
    )

@app.route('/validar_respuesta', methods=['POST'])
def validar_respuesta():
    if 'usuario_id' not in session:
        return jsonify({"status": "unauthorized"}), 401
        
    data = request.json
    respuesta_usuario = str(data.get('respuesta', '')).strip()    
    tiempo_ms = data.get('tiempo_ms', 0)
    
    solucion_real = str(session.get('solucion_actual', '')).strip()
    tipo_actual = session.get('tipo_actual', '')
    subtema_actual = session.get('subtema_actual', 'general')
    dificultad_actual = session.get('dificultad_actual', 'facil')
    pregunta_actual = session.get('pregunta_actual', '')
    partida_id = session.get('partida_id')
    usuario_id = session['usuario_id']
    
    es_correcto = False

    if tipo_actual == 'ecuacion_2do_grado':
        try:
            soluciones_correctas = [float(x.strip()) for x in solucion_real.split(',')]
        except ValueError:
            soluciones_correctas = []

        try:
            respuestas_usuario = [float(x.strip()) for x in respuesta_usuario.split(',') if x.strip() != '']
        except ValueError:
            respuestas_usuario = []

        if soluciones_correctas and respuestas_usuario:
            if sorted(soluciones_correctas) == sorted(respuestas_usuario):
                es_correcto = True
    else:
        def normalizar(txt):
            return (txt.replace(" ", "")
                       .lower()
                       .replace("²", "^2")
                       .replace("³", "^3")
                       .replace("*", ""))
        
        norm_usuario = normalizar(respuesta_usuario)
        norm_correcta = normalizar(solucion_real)
        es_correcto = (norm_usuario == norm_correcta)

    historial = session.get('historial_aciertos', [])
    historial.append(es_correcto)
    session['historial_aciertos'] = historial[-10:]

    niveles = ['facil', 'medio', 'dificil']
    idx_actual = niveles.index(dificultad_actual) if dificultad_actual in niveles else 0

    if len(historial) >= 10 and all(historial[-10:]):
        if idx_actual < len(niveles) - 1:
            idx_actual += 1
            session['historial_aciertos'] = []
    elif len(historial) >= 5 and all(not x for x in historial[-5:]):
        if idx_actual > 0:
            idx_actual -= 1
            session['historial_aciertos'] = []

    nueva_dificultad = niveles[idx_actual]
    session['dificultad_actual'] = nueva_dificultad
    session['ultimo_nivel_evaluado'] = nueva_dificultad

    # Control de rachas
    if es_correcto:
        session['racha_actual'] = session.get('racha_actual', 0) + 1
        if session['racha_actual'] > session.get('max_racha_partida', 0):
            session['max_racha_partida'] = session['racha_actual']
    else:
        session['racha_actual'] = 0

    if partida_id:
        conn = get_db_connection()
        
        conn.execute('''
            INSERT INTO intentos (
                partida_id, usuario_id, tipo_operacion, subtipo, dificultad, 
                pregunta, respuesta_correcta, respuesta_usuario, es_correcto, tiempo_respuesta_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            partida_id, usuario_id, tipo_actual, subtema_actual, dificultad_actual,
            pregunta_actual, solucion_real, respuesta_usuario, 1 if es_correcto else 0, tiempo_ms
        ))
        
        progreso = conn.execute(
            "SELECT * FROM progreso_habilidades WHERE usuario_id = ? AND subtema = ?",
            (usuario_id, subtema_actual)
        ).fetchone()

        if progreso:
            aciertos = progreso['aciertos'] + (1 if es_correcto else 0)
            fallos = progreso['fallos'] + (0 if es_correcto else 1)
            xp = progreso['xp'] + (10 if es_correcto else 0)
            porcentaje = min(100, xp)
            completado = 1 if porcentaje >= 100 else 0
            
            conn.execute('''
                UPDATE progreso_habilidades 
                SET aciertos = ?, fallos = ?, xp = ?, porcentaje = ?, completado = ?
                WHERE usuario_id = ? AND subtema = ?
            ''', (aciertos, fallos, xp, porcentaje, completado, usuario_id, subtema_actual))
        else:
            aciertos = 1 if es_correcto else 0
            fallos = 0 if es_correcto else 1
            xp = 10 if es_correcto else 0
            porcentaje = min(100, xp)
            completado = 1 if porcentaje >= 100 else 0
            
            conn.execute('''
                INSERT INTO progreso_habilidades (usuario_id, subtema, aciertos, fallos, xp, porcentaje, completado)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (usuario_id, subtema_actual, aciertos, fallos, xp, porcentaje, completado))

        conn.execute('''
            UPDATE partidas SET max_racha = ? WHERE id = ?
        ''', (session.get('max_racha_partida', 0), partida_id))
        
        conn.commit()
        conn.close()

    return jsonify({
        "resultado": es_correcto,
        "solucion_correcta": solucion_real,
        "racha_actual": session.get('racha_actual', 0),
        "max_racha": session.get('max_racha_partida', 0),
        "dificultad_actual": nueva_dificultad
    })


@app.route('/arbol-habilidades')
def arbol_habilidades():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
        
    usuario_id = session['usuario_id']
    conn = get_db_connection()
    
    progresos_raw = conn.execute(
        "SELECT * FROM progreso_habilidades WHERE usuario_id = ?",
        (usuario_id,)
    ).fetchall()
    
    conn.close()
    progreso_dict = {row['subtema']: dict(row) for row in progresos_raw}
    return render_template('arbol.html', progreso=progreso_dict, username=session.get('username'))


@app.route('/practica')
def practica():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('practica.html', username=session.get('username'))


if __name__ == '__main__':
    app.run(debug=True)