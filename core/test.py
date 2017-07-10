from aiohttp import web
import socketio

sio = socketio.AsyncServer()
app = web.Application()
sio.attach(app)

async def index(request):
    """Serve the client-side application."""
    return web.Response(text='hello', content_type='text/html')

@sio.on('connect', namespace='/chat')
def connect(sid, environ):
    print("connect ", sid)

@sio.on('chat message', namespace='/chat')
async def message(sid, data):
    print("message ", data)
    await sio.emit('reply', room=sid)

@sio.on('disconnect', namespace='/chat')
def disconnect(sid):
    print('disconnect ', sid)

app.router.add_get('/', index)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5001)