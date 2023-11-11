import io
from flask import Flask, render_template, Response
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)


@app.route('/')
@app.route('/index')
@app.route('/index.html')
def index():
    return render_template('index.html')


@app.route('/settings')
@app.route('/settings.html')
def settings():
    return render_template('settings.html')


@app.route('/info')
@app.route('/info.html')
def info():
    return render_template('info.html')


@app.route('/video_feed')
def video_feed():
    if app.recording:
        return app.send_static_file('./static/images/paused_image.jpg')
    return Response(gen(app.camera), mimetype='multipart/x-mixed-replace; boundary=frame')


def gen(camera):
    stream = io.BytesIO()
    for _ in camera.capture_continuous(stream, 'jpeg', use_video_port=True):
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + stream.getvalue() + b'\r\n')
        stream.seek(0)
        stream.truncate()


def send_status_update(status):
    with app.app_context():
        socketio.emit('status_update', status, namespace='/',
                      room='/', include_self=True)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
