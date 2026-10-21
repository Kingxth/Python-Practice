import random
import json
from flask import Flask, render_template, request, jsonify, session
from calculos import generar_operacion
from database import init_db, get_db_connection

app = Flask(__name__, 
            static_folder='static', 
            template_folder='templates')
            
app.secret_key = 'asjdfh7634tbgasdf7623pepegrillo'

with app.app_context():
    init_db()


@app.route('/')
def home():
    # Default : en facil
    if 'config_dificultades' not in session:
        session['config_dificultades'] = {
            'suma': 'facil',
            'resta': 'facil',
            'multiplicacion': 'facil',
            'division': 'facil',
            'potencias': 'facil',
            'raices': 'facil'
        }
    return render_template('index.html')


@app.route('/iniciar_juego', methods=['POST'])
def iniciar_juego():
    data = request.json
    ops_elegidas = data.get('operaciones', ['suma'])
    session['ops_disponibles'] = ops_elegidas
    
    session['racha_actual'] = 0
    session['max_racha_partida'] = 0
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO partidas (modo, tiempo_total_seg, score_final, max_racha) VALUES (?, 0, 0, 0)",
        ('clasico',)
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


@app.route('/guardar_partida', methods=['POST'])
def guardar_partida():
    data = request.json
    tiempo_total = data.get('tiempo_total', 90)
    score_final = data.get('score_final', 0)
    max_racha = data.get('max_racha', 0)
    partida_id = session.get('partida_id')
    
    if partida_id:
        conn = get_db_connection()
        conn.execute(
            "UPDATE partidas SET tiempo_total_seg = ?, score_final = ?, max_racha = ? WHERE id = ?",
            (tiempo_total, score_final, max_racha, partida_id)
        )
        conn.commit()
        conn.close()
        
    return jsonify({"status": "success"})

    
@app.route('/obtener_pregunta')
def obtener_pregunta():
    ops_disponibles = session.get('ops_disponibles', ['suma'])
    tipo = random.choice(ops_disponibles)
    config_dificultades = session.get('config_dificultades', {})
    dif = config_dificultades.get(tipo, 'facil')
    
    pregunta, solucion = generar_operacion(tipo, dif)
    
    session['solucion_actual'] = str(solucion)
    session['tipo_actual'] = tipo  
    session['pregunta_actual'] = pregunta
    session['dificultad_actual'] = dif  
    
    return jsonify({
        "pregunta": pregunta,
        "tipo": tipo,
        "dificultad_actual": dif
    })


@app.route('/dashboard')
def dashboard():
    conn = get_db_connection()
    
    stats_generales = conn.execute('''
        SELECT 
            COUNT(*) as total_intentos,
            SUM(es_correcto) as total_aciertos,
            AVG(tiempo_respuesta_ms) as tiempo_promedio_ms
        FROM intentos
    ''').fetchone()
    
    total_intentos = stats_generales['total_intentos'] or 0
    total_aciertos = stats_generales['total_aciertos'] or 0
    porcentaje_acierto = round((total_aciertos / total_intentos * 100), 1) if total_intentos > 0 else 0
    tiempo_promedio_seg = round((stats_generales['tiempo_promedio_ms'] or 0) / 1000, 2)
    
    partidas_jugadas = conn.execute('SELECT COUNT(*) as total FROM partidas').fetchone()['total']
    max_racha_historica = conn.execute('SELECT MAX(max_racha) as max_racha FROM partidas').fetchone()['max_racha'] or 0

    historial_partidas = [dict(row) for row in conn.execute('''
        SELECT id, modo, tiempo_total_seg, score_final, max_racha, fecha
        FROM partidas ORDER BY fecha DESC LIMIT 10
    ''').fetchall()]
    
    conn.close()
    
    return render_template(
        'dashboard.html',
        total_intentos=total_intentos,
        porcentaje_acierto=porcentaje_acierto,
        tiempo_promedio_seg=tiempo_promedio_seg,
        partidas_jugadas=partidas_jugadas,
        max_racha_historica=max_racha_historica,
        historial_partidas=historial_partidas
    )


@app.route('/validar_respuesta', methods=['POST'])
def validar_respuesta():
    data = request.json
    respuesta_usuario = str(data.get('respuesta', '')).strip()    
    tiempo_ms = data.get('tiempo_ms', 0)
    
    solucion_real = str(session.get('solucion_actual', '')).strip()
    tipo_actual = session.get('tipo_actual', '')
    dificultad_actual = session.get('dificultad_actual', 'facil') 
    pregunta_actual = session.get('pregunta_actual', '')
    partida_id = session.get('partida_id')
    
    def normalizar(txt):
        return (txt.replace(" ", "")
                   .lower()
                   .replace("²", "^2")
                   .replace("³", "^3")
                   .replace("*", ""))
    
    norm_usuario = normalizar(respuesta_usuario)
    norm_correcta = normalizar(solucion_real)
    es_correcto = (norm_usuario == norm_correcta)

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
                partida_id, tipo_operacion, subtipo, dificultad, 
                pregunta, respuesta_correcta, respuesta_usuario, es_correcto, tiempo_respuesta_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            partida_id, tipo_actual, None, dificultad_actual,
            pregunta_actual, solucion_real, respuesta_usuario, 1 if es_correcto else 0, tiempo_ms
        ))
        
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
        "dificultad_actual": dificultad_actual
    })


if __name__ == '__main__':
    app.run(debug=True)