import sqlite3

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tabla de Usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            rol TEXT NOT NULL,
            fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de Partidas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS partidas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            modo TEXT,
            tiempo_total_seg REAL,
            score_final INTEGER,
            max_racha INTEGER DEFAULT 0,
            fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')

    # Tabla de Intentos
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
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (partida_id) REFERENCES partidas (id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')

    # Tabla de progreso / Integrales & Derivadas
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS progreso_habilidades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            subtema TEXT NOT NULL,
            aciertos INTEGER DEFAULT 0,
            fallos INTEGER DEFAULT 0,
            xp INTEGER DEFAULT 0,
            porcentaje INTEGER DEFAULT 0,
            completado INTEGER DEFAULT 0,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
            UNIQUE(usuario_id, subtema)
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Base de datos y tablas inicializadas")
    