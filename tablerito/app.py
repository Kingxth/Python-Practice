from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import base64
import os

app = Flask(__name__)
#cambiala
app.config['SECRET_KEY'] = '^!@#)*(jsakdj121sdjsJSAJsl)'
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('draw_line')
def handle_draw_line(data):
    print(f"Trazo recibido del cliente: modo={data.get('mode')}, color={data.get('color')}")
    emit('draw_line', data, broadcast=True, include_self=False)

# Limpiar tablero
@socketio.on('clear_board')
def handle_clear_board():
    emit('clear_board', broadcast=True, include_self=False)

#Recibe  retransmite la imagen
@socketio.on('upload_image')
def handle_upload_image(data):
    try:
        image_data = data['image_data'].split(',')[1]
        os.makedirs('uploads', exist_ok=True)
        file_path = os.path.abspath('uploads/imagen_recibida.png')
        with open(file_path, 'wb') as fh:
            fh.write(base64.b64decode(image_data))
        print(f"¡Imagen vista: {file_path}!")
    except Exception as e:
        print(f"Error al guardar la imagen en el servidor: {e}")
        
    emit('upload_image', data, broadcast=True, include_self=False)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True, port=3000)
