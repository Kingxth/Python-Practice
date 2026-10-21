import sqlite3
import os

DB_NAME = os.path.join(os.path.dirname(__file__), 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Usu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol TEXT DEFAULT 'estudiante',
            config_dificultades TEXT
        )
    ''')
    
    # Partidas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS partidas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            modo TEXT DEFAULT 'clasico',
            tiempo_total_seg REAL,
            score_final INTEGER,
            max_racha INTEGER,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')
    
    # Tabla de intentos por cada pregunta
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS intentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partida_id INTEGER,
            usuario_id INTEGER,
            tipo_operacion TEXT,
            subtipo TEXT,
            dificultad TEXT,
            pregunta TEXT,
            respuesta_correcta TEXT,
            respuesta_usuario TEXT,
            es_correcto INTEGER,
            tiempo_respuesta_ms INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (partida_id) REFERENCES partidas (id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')
    
    conn.commit()
    conn.close()