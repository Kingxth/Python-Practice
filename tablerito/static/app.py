from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secreto_super_seguro'
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('draw_line')
def handle_draw_line(data):
    emit('draw_line', data, broadcast=True, include_self=False)

@socketio.on('clear_board')
def handle_clear_board():
    emit('clear_board', broadcast=True, include_self=False)

if __name__ == '__main__':
    socketio.run(app,host='0.0.0.0', debug=True, port=3000)